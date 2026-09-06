from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.database import RepositoryIndex
from backend.app.repository.service import repository_service, Workspace
from backend.app.ai import ai_gateway, ChatRequest, ChatMessage, MessageRole, TaskType
from backend.app.utils.logging import logger

class RepositorySummary(BaseModel):
    architecture_summary: str = Field(description="High-level overview of the project architecture")
    important_modules: List[str] = Field(description="List of key directories or files and their roles")
    technology_summary: str = Field(description="Summary of languages, frameworks, and tools used")
    development_workflow: str = Field(description="Instructions or inferred steps for local development")
    testing_workflow: str = Field(description="Instructions or inferred steps for running tests")

class RepositoryAnalyzer:
    async def generate_summary(
        self,
        workspace: Workspace,
        build_info: Dict[str, Any],
        test_info: Dict[str, Any],
        readme_info: Dict[str, Any],
        files_metadata: List[Dict[str, Any]]
    ) -> RepositorySummary:
        """
        Uses AI to generate a comprehensive summary of the repository.
        """
        # 1. Prepare context for the prompt
        # We don't send all files, just the first 100 or a summary
        file_paths = [f["path"] for f in files_metadata[:100]]
        if len(files_metadata) > 100:
            file_paths.append(f"... and {len(files_metadata) - 100} more files")

        readme_content = ""
        if readme_info.get("found"):
            # Use only relevant sections to save tokens
            sections = readme_info.get("sections", {})
            readme_content = f"""
            Description: {sections.get('description', '')}
            Installation: {sections.get('installation', '')}
            Architecture: {sections.get('architecture', '')}
            """

        context = f"""
        Files Structure (truncated):
        {chr(10).join(file_paths)}

        Detected Build Systems: {build_info.get('systems', [])}
        Primary Language: {build_info.get('primary_language')}

        Detected Test Frameworks: {test_info.get('frameworks', [])}
        Likely Test Commands: {test_info.get('test_commands', [])}

        README Highlights:
        {readme_content}
        """

        prompt = f"""
        You are an expert software architect. Analyze the provided repository context and generate a technical summary.

        Repository Context:
        {context}

        Your summary must be accurate, concise, and professional.
        """

        # 2. Call AI Gateway
        request = ChatRequest(
            messages=[
                ChatMessage(role=MessageRole.SYSTEM, content="You are a helpful assistant that analyzes software repositories."),
                ChatMessage(role=MessageRole.USER, content=prompt)
            ]
        )

        return await ai_gateway.chat_structured(
            request=request,
            response_model=RepositorySummary,
            task=TaskType.REPO_ANALYSIS
        )

    async def update_index_summary(self, db: AsyncSession, index: RepositoryIndex, workspace: Workspace):
        """
        Full orchestration of repository analysis and index update.
        """
        try:
            # Gather all metadata
            build_info = await repository_service.detect_build_system(workspace)
            test_info = await repository_service.detect_test_system(workspace, build_info)
            readme_info = await repository_service.extract_readme_info(workspace)
            files_metadata = await repository_service.discover_files(workspace)

            # Generate AI summary
            summary = await self.generate_summary(
                workspace=workspace,
                build_info=build_info,
                test_info=test_info,
                readme_info=readme_info,
                files_metadata=files_metadata
            )

            # Persist to DB
            index.summary = summary.model_dump()
            await db.commit()
            logger.info(f"AI summary generated and stored for index {index.id}")

        except Exception as e:
            logger.error(f"Failed to generate repository summary: {str(e)}")
            # We don't fail the whole indexing process if AI analysis fails,
            # but we should log it.
            if db.is_active:
                await db.rollback()

repository_analyzer = RepositoryAnalyzer()
