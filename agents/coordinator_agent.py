from langgraph.graph import Graph, StateGraph
from typing import Dict, Any
from pydantic import BaseModel
from core.gemini_client import GeminiClient

class AgentState(BaseModel):
    messages: list
    current_step: str
    results: Dict[str, Any]
    
class CoordinatorAgent:
    def __init__(self, gemini_client: GeminiClient):
        self.client = gemini_client
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(AgentState)
        
        # Add nodes for each step
        workflow.add_node("skill_assessment", self._run_skill_assessment)
        workflow.add_node("resume_review", self._run_resume_review)
        workflow.add_node("interview_assessment", self._run_interview_assessment)
        workflow.add_node("generate_feedback", self._generate_feedback)

        # Define the workflow
        workflow.add_edge("skill_assessment", "resume_review")
        workflow.add_edge("resume_review", "interview_assessment")
        workflow.add_edge("interview_assessment", "generate_feedback")
        
        return workflow.compile()

    async def _run_skill_assessment(self, state: AgentState) -> AgentState:
        # Implementation for skill assessment
        skills = state.messages[0].get("skills", [])
        response = await self.client.generate_response(
            SKILL_ASSESSMENT_PROMPT.substitute(skills=", ".join(skills))
        )
        state.results["skill_assessment"] = response
        state.current_step = "skill_assessment"
        return state

    async def _run_resume_review(self, state: AgentState) -> AgentState:
        # Implementation for resume review
        resume = state.messages[0].get("resume", "")
        response = await self.client.generate_response(
            RESUME_REVIEW_PROMPT.substitute(resume_content=resume)
        )
        state.results["resume_review"] = response
        state.current_step = "resume_review"
        return state

    async def _run_interview_assessment(self, state: AgentState) -> AgentState:
        # Implementation for interview assessment
        transcript = state.messages[0].get("interview_transcript", "")
        response = await self.client.generate_response(
            INTERVIEW_ASSESSMENT_PROMPT.substitute(interview_transcript=transcript)
        )
        state.results["interview_assessment"] = response
        state.current_step = "interview_assessment"
        return state

    async def _generate_feedback(self, state: AgentState) -> AgentState:
        # Compile all results and generate final feedback
        feedback = {
            "skill_assessment": state.results.get("skill_assessment"),
            "resume_review": state.results.get("resume_review"),
            "interview_assessment": state.results.get("interview_assessment")
        }
        state.results["final_feedback"] = feedback
        state.current_step = "completed"
        return state

    async def run_assessment(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        initial_state = AgentState(
            messages=[input_data],
            current_step="start",
            results={}
        )
        final_state = await self.graph.arun(initial_state)
        return final_state.results
