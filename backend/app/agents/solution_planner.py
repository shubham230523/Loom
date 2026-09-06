from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.database import Repository, RepositoryIndex, Opportunity, Issue
from backend.app.ai import ai_gateway, ChatRequest, ChatMessage, MessageRole, TaskType, semantic_search_service
from backend.app.utils.logging import logger

class SolutionPlanOutput(BaseModel):
    problem: str = Field(description="Summary of the technical problem being addressed")
    root_cause: str = Field(description="Identification of why the issue exists in the codebase")
    relevant_files: List[str] = Field(description="List of files that need to be modified or referenced")
    relevant_symbols: List[str] = Field(description="Specific classes, functions, or variables involved")
    implementation_steps: List[str] = Field(description="Step-by-step technical plan to solve the issue")
    testing_strategy: str = Field(description="How to verify the fix or implementation")
    risks: str = Field(description="Potential side effects or technical challenges")
    expected_diff_size: str = Field(description="Small, Medium, or Large estimation of the change")
    confidence: float = Field(description="Score from 0.0 to 1.0 based on feasibility and information clarity")

class SolutionPlannerAgent:
    async def create_plan(
        self,
        db: AsyncSession,
        repository: Repository,
        index: RepositoryIndex,
        opportunity: Opportunity,
        issue: Optional[Issue] = None
    ) -> SolutionPlanOutput:
        """
        Generates a detailed technical solution plan for a given opportunity.
        """
        logger.info(f"SolutionPlannerAgent: Creating plan for '{opportunity.title}' in {repository.full_name}")

        # 1. Gather Semantic Context
        # Search for code relevant to the opportunity title and description
        search_results = await semantic_search_service.search(
            db=db,
            repository_id=repository.id,
            query=f"{opportunity.title} {opportunity.description}",
            limit=10
        )

        code_context = ""
        for res in search_results:
            if res["type"] == "symbol":
                code_context += f"- {res['symbol_type'].capitalize()}: {res['name']} in {res['path']}\n"
            elif res["type"] == "file":
                code_context += f"- File: {res['path']}\n"

        # 2. Build Context prompt
        context = f"""
        Repository: {repository.full_name}
        Language: {repository.language}

        Project Summary:
        {index.summary.get('architecture_summary') if index.summary else 'Not available'}

        Opportunity: {opportunity.title}
        Type: {opportunity.type}
        Description:
        {opportunity.description}
        """

        if issue:
            context += f"\nLinked Issue #{issue.number}: {issue.title}\n{issue.body or ''}\n"

        context += f"\nPotentially Relevant Code Entities:\n{code_context}"

        prompt = f"""
        You are a principal software engineer. Create a comprehensive, executable solution plan for the following opportunity.

        {context}

        Your plan should be technically sound, detailed, and ready for an implementation agent to follow.
        Identify the root cause within the existing structure and provide precise implementation steps.
        DO NOT provide actual code changes, only the PLAN.
        """

        request = ChatRequest(
            messages=[
                ChatMessage(role=MessageRole.SYSTEM, content="You are a meticulous architect creating implementation blueprints."),
                ChatMessage(role=MessageRole.USER, content=prompt)
            ]
        )

        return await ai_gateway.chat_structured(
            request=request,
            response_model=SolutionPlanOutput,
            task=TaskType.PLANNING
        )

solution_planner_agent = SolutionPlannerAgent()
