from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from backend.app.ai import ai_gateway, ChatRequest, ChatMessage, MessageRole, TaskType
from backend.app.database import TestRun
from backend.app.utils.logging import logger

class DebuggingAnalysis(BaseModel):
    root_cause_analysis: str = Field(description="Identification of why the tests failed")
    suggested_fix: str = Field(description="Clear instructions on how to fix the code to make tests pass")
    affected_files: List[str] = Field(description="Files that need further modification")

class DebuggerAgent:
    async def analyze_failure(
        self,
        test_run: TestRun,
        plan_context: str,
        code_context: str
    ) -> DebuggingAnalysis:
        """
        Analyzes a test failure and suggests a fix.
        """
        logger.info(f"DebuggerAgent: Analyzing failure for test command: {test_run.command}")

        prompt = f"""
        You are a debugging expert. A technical change was implemented but the tests failed.

        GOAL & PLAN:
        {plan_context}

        FAILED TEST COMMAND: {test_run.command}
        STDOUT:
        {test_run.stdout[-2000:] if test_run.stdout else "None"}

        STDERR:
        {test_run.stderr[-2000:] if test_run.stderr else "None"}

        RELEVANT CODE SNIPPETS:
        {code_context}

        Analyze the failure and provide a clear root cause and a suggested fix.
        Be extremely precise so the implementation agent can apply the fix correctly.
        """

        request = ChatRequest(
            messages=[
                ChatMessage(role=MessageRole.SYSTEM, content="You are a senior developer specializing in root cause analysis and debugging."),
                ChatMessage(role=MessageRole.USER, content=prompt)
            ]
        )

        return await ai_gateway.chat_structured(
            request=request,
            response_model=DebuggingAnalysis,
            task=TaskType.DEBUGGING
        )

debugger_agent = DebuggerAgent()
