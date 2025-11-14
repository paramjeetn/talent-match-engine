class InterviewService:
    def __init__(self, gemini_client: GeminiClient):
        self.client = gemini_client

    async def analyze_interview(self, transcript: str) -> Dict[str, Any]:
        # Analyze interview transcript
        communication_score = await self._assess_communication(transcript)
        technical_score = await self._assess_technical_knowledge(transcript)
        personality_fit = await self._assess_personality_fit(transcript)
        
        return {
            "communication_score": communication_score,
            "technical_score": technical_score,
            "personality_fit": personality_fit,
            "overall_feedback": await self._generate_overall_feedback(transcript)
        }

    async def _assess_communication(self, transcript: str) -> float:
        prompt = f"Rate the communication skills in this interview (0-100):\n\n{transcript}"
        response = await self.client.generate_response(prompt)
        try:
            return float(response.split("/")[0])
        except:
            return 0.0

    async def _assess_technical_knowledge(self, transcript: str) -> float:
        prompt = f"Rate the technical knowledge demonstrated (0-100):\n\n{transcript}"
        response = await self.client.generate_response(prompt)
        try:
            return float(response.split("/")[0])
        except:
            return 0.0

    async def _assess_personality_fit(self, transcript: str) -> str:
        prompt = f"Assess the candidate's personality fit:\n\n{transcript}"
        return await self.client.generate_response(prompt)

    async def _generate_overall_feedback(self, transcript: str) -> str:
        prompt = f"Provide comprehensive interview feedback:\n\n{transcript}"
        return await self.client.generate_response(prompt)
