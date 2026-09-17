import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient
from fastapi import HTTPException
from backend.app.main import app
from backend.app.security.auth import get_current_user, get_optional_current_user
from backend.app.database.models import User, Repository, RepositoryIndex, Opportunity, Contribution, SolutionPlan
from sqlalchemy import select

# Dummy user for auth override
dummy_user = User(id=uuid.uuid4(), username="testuser", github_user_id=123)

async def override_get_current_user():
    return dummy_user

@pytest.fixture
def authenticated_client(client):
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_optional_current_user] = override_get_current_user
    yield client
    app.dependency_overrides.clear()

@pytest.fixture
def mock_github_api(mocker):
    mock_svc = mocker.patch("backend.app.api.v1.repositories.github_service")
    mock_svc.get_client_for_user = AsyncMock()
    mock_svc.get_client_for_user.return_value = MagicMock(access_token="fake-token")
    mock_svc.search_repositories = AsyncMock()
    mock_svc.get_repository = AsyncMock()
    return mock_svc

@pytest.mark.asyncio
async def test_search_repositories_api(authenticated_client, mock_github_api):
    mock_github_api.search_repositories.return_value = {"items": [], "total_count": 0}
    response = await authenticated_client.get("/api/v1/repositories/search?q=loom")
    assert response.status_code == 200
    assert response.json()["items"] == []

@pytest.mark.asyncio
async def test_get_repository_api_not_in_db(authenticated_client, mock_github_api):
    repo_id = 12345
    mock_github_api.get_repository.return_value = {"id": repo_id, "name": "test-repo", "owner": {"login": "o"}}
    response = await authenticated_client.get(f"/api/v1/repositories/{repo_id}")
    assert response.status_code == 200
    assert response.json()["id"] == repo_id
    assert response.json()["is_imported"] is False

@pytest.mark.asyncio
async def test_get_repository_api_by_uuid(authenticated_client, db_session, mock_github_api):
    repo = Repository(id=uuid.uuid4(), github_repo_id=6789, owner="owner1", name="name1", full_name="owner1/name1", html_url="http://url1")
    db_session.add(repo)
    await db_session.commit()
    mock_github_api.get_repository.return_value = {"id": 6789, "name": "name1", "owner": {"login": "owner1"}}
    response = await authenticated_client.get(f"/api/v1/repositories/{repo.id}")
    assert response.status_code == 200
    assert response.json()["loom_id"] == str(repo.id)

@pytest.mark.asyncio
async def test_get_repository_api_by_github_id_in_db(authenticated_client, db_session, mock_github_api):
    repo = Repository(id=uuid.uuid4(), github_repo_id=555, owner="o8", name="n8", full_name="o8/n8", html_url="h")
    db_session.add(repo)
    await db_session.commit()
    mock_github_api.get_repository.return_value = {"id": 555, "name": "n8", "owner": {"login": "o8"}}
    response = await authenticated_client.get("/api/v1/repositories/555")
    assert response.status_code == 200
    assert response.json()["loom_id"] == str(repo.id)

@pytest.mark.asyncio
async def test_get_repository_api_not_found(authenticated_client, mock_github_api):
    mock_github_api.get_client_for_user.return_value = MagicMock()
    mock_github_api.get_repository.side_effect = Exception("Not Found")
    response = await authenticated_client.get("/api/v1/repositories/999999")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_initialize_repository_api(authenticated_client, db_session, mock_github_api):
    github_id = 9999
    mock_github_api.get_repository.return_value = {"id": github_id, "name": "new-repo", "owner": {"login": "o2"}, "full_name": "o2/new-repo", "html_url": "http://h2"}
    with patch("backend.app.api.v1.repositories.run_indexing") as mock_idx:
        response = await authenticated_client.post(f"/api/v1/repositories/initialize?github_id={github_id}")
        assert response.status_code == 200
        assert response.json()["github_repo_id"] == github_id

@pytest.mark.asyncio
async def test_discover_opportunities_api(authenticated_client, db_session, mock_github_api):
    repo = Repository(id=uuid.uuid4(), github_repo_id=111, owner="o3", name="n3", full_name="o3/n3", html_url="h3")
    db_session.add(repo)
    await db_session.commit()
    response = await authenticated_client.post(f"/api/v1/repositories/{repo.id}/opportunities/discover")
    assert response.status_code == 200
    assert response.json()["status"] == "indexing"
    index = RepositoryIndex(repository_id=repo.id, status="completed", branch="main", commit_sha="abc")
    db_session.add(index)
    await db_session.commit()
    response = await authenticated_client.post(f"/api/v1/repositories/{repo.id}/opportunities/discover")
    assert response.status_code == 200
    assert response.json()["status"] == "discovering"

@pytest.mark.asyncio
async def test_score_opportunity_api(authenticated_client, db_session, mocker, mock_github_api):
    repo_id = uuid.uuid4()
    repo = Repository(id=repo_id, github_repo_id=222, owner="o4", name="n4", full_name="o4/n4", html_url="h4")
    index = RepositoryIndex(repository_id=repo_id, status="completed", branch="main", commit_sha="def")
    db_session.add_all([repo, index])
    await db_session.commit()
    mock_opp_svc = mocker.patch("backend.app.api.v1.repositories.opportunity_service")
    mock_opp_svc.score_opportunity = AsyncMock(return_value={"score": 85})
    response = await authenticated_client.post(f"/api/v1/repositories/{repo_id}/opportunities/{uuid.uuid4()}/score")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_create_contribution_api(authenticated_client, mocker, mock_github_api):
    repo_id = uuid.uuid4()
    opp_id = uuid.uuid4()
    mock_contrib_svc = mocker.patch("backend.app.api.v1.repositories.contribution_service")
    mock_contrib_svc.create_contribution = AsyncMock(return_value={"id": "c1"})

    response = await authenticated_client.post(f"/api/v1/repositories/{repo_id}/contributions?opportunity_id={opp_id}")
    assert response.status_code == 200
    assert response.json()["id"] == "c1"

@pytest.mark.asyncio
async def test_contribution_workflow_full(authenticated_client, mocker, mock_github_api):
    repo_id = uuid.uuid4()
    contr_id = uuid.uuid4()

    mock_svc = mocker.patch("backend.app.api.v1.repositories.contribution_service")
    mock_svc.create_contribution = AsyncMock(return_value={"id": str(contr_id)})
    mock_svc.generate_plan = AsyncMock(return_value={"status": "planned"})
    mock_svc.execute_implementation = AsyncMock(return_value={"status": "implementing"})
    mock_svc.setup_contribution_workspace = AsyncMock(return_value={"status": "ready"})
    mock_svc.validate_contribution = AsyncMock(return_value={"is_valid": True})
    mock_svc.push_to_github = AsyncMock(return_value={"status": "pushed"})
    mock_svc.create_github_pr = AsyncMock(return_value={"url": "http://pr"})
    mock_svc.execute_mock_implementation = AsyncMock(return_value={"status": "mocked"})

    endpoints = [
        (f"post", f"/api/v1/repositories/{repo_id}/contributions?opportunity_id={uuid.uuid4()}"),
        (f"post", f"/api/v1/repositories/{repo_id}/contributions/{contr_id}/plan"),
        (f"post", f"/api/v1/repositories/{repo_id}/contributions/{contr_id}/implement"),
        (f"post", f"/api/v1/repositories/{repo_id}/contributions/{contr_id}/workspace"),
        (f"get", f"/api/v1/repositories/{repo_id}/contributions/{contr_id}/validate"),
        (f"post", f"/api/v1/repositories/{repo_id}/contributions/{contr_id}/push"),
        (f"post", f"/api/v1/repositories/{repo_id}/contributions/{contr_id}/pull-request"),
        (f"post", f"/api/v1/repositories/{repo_id}/contributions/{contr_id}/mock-implement"),
    ]

    for method, url in endpoints:
        resp = await getattr(authenticated_client, method)(url)
        assert resp.status_code == 200

@pytest.mark.asyncio
async def test_get_contribution_details_success(authenticated_client, db_session, mock_github_api):
    # Ensure user exists for FK
    query = select(User).where(User.id == dummy_user.id)
    existing_user = (await db_session.execute(query)).scalars().first()
    if not existing_user:
        # User needs github_user_id which is unique, so use a unique one if 123 exists
        user_to_add = User(id=dummy_user.id, username=f"testuser_{uuid.uuid4().hex[:8]}", github_user_id=int(uuid.uuid4().int % 1000000))
        db_session.add(user_to_add)
        await db_session.commit()
    else:
        user_to_add = existing_user

    repo_id = uuid.uuid4()
    contr_id = uuid.uuid4()
    repo = Repository(id=repo_id, github_repo_id=int(uuid.uuid4().int % 1000000), owner="o5", name="n5", full_name=f"o5/n5_{uuid.uuid4().hex[:8]}", html_url="h5")
    opp = Opportunity(id=uuid.uuid4(), repository_id=repo_id, title="T", description="D", type="bug", impact="high", difficulty="easy")
    contrib = Contribution(id=contr_id, repository_id=repo_id, user_id=user_to_add.id, opportunity_id=opp.id, branch_name="b", status="started")
    db_session.add_all([repo, opp, contrib])
    await db_session.commit()

    response = await authenticated_client.get(f"/api/v1/repositories/{repo_id}/contributions/{contr_id}")
    assert response.status_code == 200
    assert response.json()["id"] == str(contr_id)

@pytest.mark.asyncio
async def test_run_indexing_task(db_session, mocker):
    repo = Repository(id=uuid.uuid4(), github_repo_id=int(uuid.uuid4().int % 1000000), owner="o6", name="n6", full_name=f"o6/n6_{uuid.uuid4().hex[:8]}", html_url="h6")
    db_session.add(repo)
    await db_session.commit()

    from backend.app.api.v1.repositories import run_indexing
    with patch("backend.app.api.v1.repositories.SessionLocal") as mock_session_local, \
         patch("backend.app.api.v1.repositories.repository_indexer", new_callable=AsyncMock) as mock_indexer:

        mock_session_local.return_value.__aenter__.return_value = db_session
        await run_indexing(str(repo.id), "token")
        mock_indexer.index_repository.assert_called_once()

@pytest.mark.asyncio
async def test_run_indexing_task_failure(db_session):
    from backend.app.api.v1.repositories import run_indexing
    with patch("backend.app.api.v1.repositories.SessionLocal") as mock_session_local, \
         patch("backend.app.api.v1.repositories.repository_indexer", new_callable=AsyncMock) as mock_indexer:
        mock_session_local.return_value.__aenter__.return_value = db_session
        mock_indexer.index_repository.side_effect = Exception("Index error")
        # Should not raise exception
        await run_indexing(str(uuid.uuid4()), "token")

@pytest.mark.asyncio
async def test_get_repository_api_fallback_to_db(authenticated_client, db_session, mock_github_api):
    repo = Repository(id=uuid.uuid4(), github_repo_id=777, owner="o9", name="n9", full_name="o9/n9", html_url="h", description="D", language="L", stargazers_count=10, forks_count=5)
    db_session.add(repo)
    await db_session.commit()

    mock_github_api.get_repository.side_effect = Exception("GitHub down")
    response = await authenticated_client.get("/api/v1/repositories/777")
    assert response.status_code == 200
    assert response.json()["loom_id"] == str(repo.id)
    assert response.json()["description"] == "D"

@pytest.mark.asyncio
async def test_initialize_repository_already_exists(authenticated_client, db_session, mock_github_api):
    github_id = 8888
    repo = Repository(id=uuid.uuid4(), github_repo_id=github_id, owner="o10", name="n10", full_name="o10/n10", html_url="h")
    db_session.add(repo)
    await db_session.commit()

    with patch("backend.app.api.v1.repositories.run_indexing") as mock_idx:
        response = await authenticated_client.post(f"/api/v1/repositories/initialize?github_id={github_id}")
        assert response.status_code == 200
        assert response.json()["github_repo_id"] == github_id
        mock_idx.assert_called_once()

@pytest.mark.asyncio
async def test_discover_opportunities_repo_not_found(authenticated_client):
    response = await authenticated_client.post(f"/api/v1/repositories/{uuid.uuid4()}/opportunities/discover")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_discover_opportunities_indexing_in_progress(authenticated_client, db_session, mock_github_api):
    repo = Repository(id=uuid.uuid4(), github_repo_id=112, owner="o3", name="n3", full_name="o3/n3_v2", html_url="h3")
    db_session.add(repo)
    await db_session.commit()
    index = RepositoryIndex(repository_id=repo.id, status="in_progress", branch="main", commit_sha="abc")
    db_session.add(index)
    await db_session.commit()

    response = await authenticated_client.post(f"/api/v1/repositories/{repo.id}/opportunities/discover")
    assert response.status_code == 200
    assert response.json()["status"] == "indexing"

@pytest.mark.asyncio
async def test_score_opportunity_errors(authenticated_client, db_session):
    repo_id = uuid.uuid4()
    # Repo not found
    response = await authenticated_client.post(f"/api/v1/repositories/{repo_id}/opportunities/{uuid.uuid4()}/score")
    assert response.status_code == 404

    # Not indexed
    repo = Repository(id=repo_id, github_repo_id=223, owner="o4", name="n4", full_name="o4/n4_v2", html_url="h4")
    db_session.add(repo)
    await db_session.commit()
    response = await authenticated_client.post(f"/api/v1/repositories/{repo_id}/opportunities/{uuid.uuid4()}/score")
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_get_contribution_details_not_found(authenticated_client):
    response = await authenticated_client.get(f"/api/v1/repositories/{uuid.uuid4()}/contributions/{uuid.uuid4()}")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_approve_contribution_plan_api(authenticated_client, mocker):
    mock_svc = mocker.patch("backend.app.api.v1.repositories.contribution_service")
    mock_svc.approve_plan = AsyncMock(return_value={"status": "approved"})
    response = await authenticated_client.post(f"/api/v1/repositories/r1/plans/{uuid.uuid4()}/approve?approved=true")
    assert response.status_code == 200
    assert response.json()["status"] == "approved"

from backend.app.api.v1.repositories import (
    get_repository_details,
    initialize_repository,
    discover_opportunities,
    score_opportunity,
    run_indexing,
    run_discovery
)

@pytest.mark.asyncio
async def test_get_repository_details_direct_logic(db_session, mock_github_api):
    # Test UUID logic
    repo_id = uuid.uuid4()
    repo = Repository(id=repo_id, github_repo_id=101, owner="o", name="n", full_name="o/n", html_url="h")
    db_session.add(repo)
    await db_session.commit()

    mock_github_api.get_repository.return_value = {"id": 101, "name": "n", "owner": {"login": "o"}}

    # By UUID string
    res = await get_repository_details(repository_id=str(repo_id), current_user=dummy_user, db=db_session)
    assert res["loom_id"] == str(repo_id)

    # By GitHub ID string (in DB)
    res = await get_repository_details(repository_id="101", current_user=dummy_user, db=db_session)
    assert res["loom_id"] == str(repo_id)

@pytest.mark.asyncio
async def test_initialize_repository_direct(db_session, mock_github_api):
    mock_github_api.get_repository.return_value = {"id": 102, "name": "n2", "owner": {"login": "o2"}, "full_name": "o2/n2", "html_url": "h2"}
    mock_bg = MagicMock()
    res = await initialize_repository(background_tasks=mock_bg, github_id=102, current_user=dummy_user, db=db_session)
    assert res.github_repo_id == 102
    mock_bg.add_task.assert_called()

@pytest.mark.asyncio
async def test_get_repository_details_fallback_direct(db_session, mock_github_api):
    u = uuid.uuid4().hex[:6]
    repo = Repository(id=uuid.uuid4(), github_repo_id=2020, owner="o", name=f"n_{u}", full_name=f"o/n_{u}", html_url="h", description="D")
    db_session.add(repo)
    await db_session.commit()
    mock_github_api.get_repository.side_effect = Exception("GH Fail")
    res = await get_repository_details(repository_id="2020", current_user=dummy_user, db=db_session)
    assert res["is_imported"] is True
    assert res["description"] == "D"

@pytest.mark.asyncio
async def test_discover_opportunities_indexing_triggered(db_session, mock_github_api):
    u = uuid.uuid4().hex[:6]
    repo = Repository(id=uuid.uuid4(), github_repo_id=4040, owner="o", name=f"n_{u}", full_name=f"o/n_{u}", html_url="h")
    db_session.add(repo)
    await db_session.commit()

    mock_bg = MagicMock()
    # No index at all -> trigger indexing
    res = await discover_opportunities(repository_id=repo.id, background_tasks=mock_bg, current_user=dummy_user, db=db_session)
    assert res["status"] == "indexing"
    assert mock_bg.add_task.called

@pytest.mark.asyncio
async def test_run_discovery_direct(db_session):
    repo = Repository(id=uuid.uuid4(), github_repo_id=5050, owner="o", name="n", full_name="o/n_disc", html_url="h")
    db_session.add(repo)
    await db_session.commit()

    with patch("backend.app.api.v1.repositories.SessionLocal") as mock_session_local, \
         patch("backend.app.api.v1.repositories.opportunity_service", new_callable=AsyncMock) as mock_opp:
        mock_session_local.return_value.__aenter__.return_value = db_session
        await run_discovery(str(repo.id), "token")
        assert mock_opp.discover_and_persist_opportunities.called

@pytest.mark.asyncio
async def test_run_discovery_direct_failure(db_session):
    repo_id = uuid.uuid4()
    repo = Repository(id=repo_id, github_repo_id=5051, owner="o", name="n", full_name="o/n_fail", html_url="h")
    db_session.add(repo)
    await db_session.commit()

    with patch("backend.app.api.v1.repositories.SessionLocal") as mock_session_local:
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        # Fail during query execution inside the try block
        mock_db.execute.side_effect = Exception("Query error")

        await run_discovery(str(repo_id), "token")
        # Should not raise, just log
