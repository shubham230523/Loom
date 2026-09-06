from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum
from backend.app.ai import ai_gateway, ChatRequest, ChatMessage, MessageRole, TaskType
from backend.app.database import SolutionPlan, TestRun
from backend.app.utils.logging import logger

class ReviewDecision(str, Enum):
    APPROVE = "APPROVE"
    REQUEST_CHANGES = "REQUEST_CHANGES"
    REJECT = "REJECT"

class ReviewIssue(BaseModel):
    file_path: Optional[str] = Field(description="Path of the file containing the issue")
    line_number: Optional[int] = Field(description="Specific line number if applicable")
    category: str = Field(description="correctness, security, performance, style, etc.")
    description: str = Field(description="Detailed explanation of the issue")
    suggestion: Optional[str] = Field(description="How to fix the issue")
    severity: str = Field(description="low, medium, high, critical")

class CodeReviewResult(BaseModel):
    decision: ReviewDecision
    summary: str = Field(description="High-level overview of the review findings")
    issues: List[ReviewIssue] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1, description="Agent's confidence in the review")

class CodeReviewAgent:
    async def review_changes(
        self,
        plan: SolutionPlan,
        diff: str,
        test_run: Optional[TestRun] = None
    ) -> CodeReviewResult:
        """
        Performs an independent technical review of the implemented changes.
        """
        logger.info(f"CodeReviewAgent: Reviewing changes for contribution {plan.contribution_id}")

        test_context = "No tests were run."
        if test_run:
            test_context = f"""
            TEST COMMAND: {test_run.command}
            STATUS: {test_run.status}
            EXIT CODE: {test_run.exit_code}

            STDOUT:
            {test_run.stdout[-1000:] if test_run.stdout else "None"}

            STDERR:
            {test_run.stderr[-1000:] if test_run.stderr else "None"}
            """

        prompt = f"""
        You are an elite principal engineer and security auditor. Your task is to perform an independent, critical review of the following implementation.

        GOAL & PLAN:
        {plan.problem}
        {plan.root_cause}

        IMPLEMENTED CHANGES (Unified Diff):
        ```diff
        {diff}
        ```

        VALIDATION CONTEXT:
        {test_context}

        REVIEW CRITERIA:
        1. Correctness: Does the code solve the root problem without side effects?
        2. Architecture: Is the solution well-structured and idiomatic?
        3. Edge Cases: Does it handle empty inputs, nulls, and error states?
        4. Security: Are there any vulnerabilities (injections, leaks, unsafe ops)?
        5. Performance: Is the solution efficient?
        6. Regression Risk: Could this break existing functionality?
        7. Scope: Are there any unnecessary changes or "dead code" introduced?

        INSTRUCTIONS:
        - Be objective. Do not blindly trust the implementation.
        - If tests failed, you must identify if the failure is related to the implementation.
        - Decision must be one of: APPROVE, REQUEST_CHANGES, REJECT.
        """

        request = ChatRequest(
            messages=[
                ChatMessage(role=MessageRole.SYSTEM, content="You are a meticulous and skeptical principal code reviewer."),
                ChatMessage(role=MessageRole.USER, content=prompt)
            ]
        )

        return await ai_gateway.chat_structured(
            request=request,
            response_model=CodeReviewResult,
            task=TaskType.CODE_REVIEW
        )

code_reviewer_agent = CodeReviewAgent()
