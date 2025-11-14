class ResumeAnalysisService:
    def __init__(self, gemini_client: GeminiClient):
        self.client = gemini_client

    async def analyze_resume(self, resume_content: str) -> Dict[str, Any]:
        # Analyze resume content
        ats_score = await self._check_ats_compatibility(resume_content)
        skill_gaps = await self._identify_skill_gaps(resume_content)
        improvements = await self._suggest_improvements(resume_content)
        
        return {
            "ats_score": ats_score,
            "skill_gaps": skill_gaps,
            "improvements": improvements
        }

    async def _check_ats_compatibility(self, resume_content: str) -> float:
        prompt = f"Analyze this resume for ATS compatibility and provide a score out of 100:\n\n{resume_content}"
        response = await self.client.generate_response(prompt)
        # Extract score from response
        try:
            return float(response.split("/")[0])
        except:
            return 0.0

    async def _identify_skill_gaps(self, resume_content: str) -> List[str]:
        prompt = f"Identify missing critical skills in this resume:\n\n{resume_content}"
        response = await self.client.generate_response(prompt)
        return [skill.strip() for skill in response.split("\n") if skill.strip()]

    async def _suggest_improvements(self, resume_content: str) -> List[str]:
        prompt = f"Suggest specific improvements for this resume:\n\n{resume_content}"
        response = await self.client.generate_response(prompt)
        return [imp.strip() for imp in response.split("\n") if imp.strip()]
