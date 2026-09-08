import pytest
import uuid
from sqlalchemy import select
from backend.app.database.models import User, GitHubAccount, Repository, Opportunity, Contribution

@pytest.mark.asyncio
async def test_user_cascade_delete(db_session):
    """Verify that deleting a user removes associated github_account and contributions."""
    # 1. Create a user
    user = User(
        github_user_id=123,
        username="testuser",
        display_name="Test User"
    )
    db_session.add(user)
    await db_session.flush()

    # 2. Add github account
    account = GitHubAccount(
        user_id=user.id,
        github_id=123,
        access_token_encrypted="secret"
    )
    db_session.add(account)

    # 3. Add a repository and opportunity
    repo = Repository(
        github_repo_id=456,
        owner="testowner",
        name="testrepo",
        full_name="testowner/testrepo",
        html_url="http://github.com/testowner/testrepo"
    )
    db_session.add(repo)
    await db_session.flush()

    opp = Opportunity(
        repository_id=repo.id,
        title="Test Opp",
        description="Fix something",
        type="bug",
        impact="low",
        difficulty="easy"
    )
    db_session.add(opp)
    await db_session.flush()

    # 4. Add contribution
    contrib = Contribution(
        user_id=user.id,
        repository_id=repo.id,
        opportunity_id=opp.id,
        status="started"
    )
    db_session.add(contrib)
    await db_session.commit()

    # 5. Delete user
    await db_session.delete(user)
    await db_session.commit()

    # 6. Verify associated records are gone
    stmt = select(GitHubAccount).where(GitHubAccount.user_id == user.id)
    assert (await db_session.execute(stmt)).scalar_one_or_none() is None

    stmt = select(Contribution).where(Contribution.user_id == user.id)
    assert (await db_session.execute(stmt)).scalar_one_or_none() is None

    # Repository should still exist
    stmt = select(Repository).where(Repository.id == repo.id)
    assert (await db_session.execute(stmt)).scalar_one_or_none() is not None
