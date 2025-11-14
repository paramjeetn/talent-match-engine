# services/resume_service.py
import json
from typing import Dict, Optional
from core.gemini_client import GeminiClient

RESUME_IMPROVEMENT_PROMPT = '''
You are an expert resume writer. Improve this resume based on the provided analysis and job role requirements.

ORIGINAL RESUME:
{resume_text}

ANALYSIS RESULTS:
{analysis_results}

JOB ROLE (if provided):
{job_role}

ATS ANALYSIS:
{ats_analysis}

Generate an improved version of the resume that addresses the identified issues and follows these guidelines:
1. Use clear, impactful bullet points
2. Focus on quantifiable achievements
3. Use industry-standard formatting
4. Incorporate relevant keywords
5. Address identified gaps
6. Follow ATS-friendly formatting

The improved resume should be provided in a clean, properly formatted text format suitable for a resume.
Keep the overall structure professional and consistent.
'''

class ResumeService:
    def __init__(self, gemini_client: GeminiClient):
        self.client = gemini_client

    async def improve_resume(
        self,
        resume_text: str,
        analysis_results: Dict,
        ats_analysis: Dict,
        job_role: str = ""
    ) -> str:
        try:
            prompt = RESUME_IMPROVEMENT_PROMPT.format(
                resume_text=resume_text,
                analysis_results=json.dumps(analysis_results, indent=2),
                ats_analysis=json.dumps(ats_analysis, indent=2),
                job_role=job_role
            )
            
            improved_resume = await self.client.generate_response(prompt)
            return self._clean_resume_text(improved_resume)
            
        except Exception as e:
            print(f"Error improving resume: {str(e)}")
            return resume_text

    def _clean_resume_text(self, text: str) -> str:
        # Remove any markdown formatting or extra whitespace
        cleaned = text.strip()
        if cleaned.startswith('```'):
            cleaned = '\n'.join(cleaned.split('\n')[1:-1])
        return cleaned.strip()