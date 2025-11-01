# agents/resume_analysis_agent.py
import json
from typing import Dict, List
from core.gemini_client import GeminiClient

ATS_ANALYSIS_PROMPT = '''
You are an expert ATS (Applicant Tracking System) analyzer. Review this resume and provide detailed ATS compatibility analysis.

RESUME:
{resume_text}

JOB ROLE (if provided):
{job_role}

Analyze the resume for ATS compatibility and provide your analysis in EXACTLY the following JSON format:
{{
    "ats_score": 0,
    "format_issues": [],
    "keyword_analysis": {{
        "present_keywords": [],
        "missing_keywords": []
    }},
    "formatting_suggestions": []
}}

IMPORTANT: Respond ONLY with a valid JSON object exactly matching the above format.
'''

RESUME_ANALYSIS_PROMPT = '''
You are an expert resume reviewer. Analyze this resume for content, impact, and industry alignment.

RESUME:
{resume_text}

DESIRED ROLE (if provided):
{job_role}

Analyze the resume and provide your analysis in EXACTLY the following JSON format:
{{
    "overall_score": 0,
    "section_scores": {{
        "professional_experience": 0,
        "education": 0,
        "skills": 0,
        "achievements": 0
    }},
    "strengths": [],
    "gaps_identified": [
        {{
            "type": "skill/experience/education",
            "description": "gap description",
            "recommendation": "how to address this gap"
        }}
    ],
    "recommended_skills": [
        {{
            "skill": "skill name",
            "reason": "why it's important",
            "learning_resources": []
        }}
    ],
    "improvement_suggestions": [
        {{
            "section": "section name",
            "current_issue": "what's wrong",
            "suggestion": "how to improve",
            "example": "improvement example"
        }}
    ]
}}

IMPORTANT: Respond ONLY with a valid JSON object exactly matching the above format.
'''

class ResumeAnalysisAgent:
    def __init__(self, gemini_client: GeminiClient):
        self.client = gemini_client

    async def analyze_resume(self, resume_text: str, job_role: str = "") -> Dict:
        response = None
        try:
            response = await self.client.generate_response(
                RESUME_ANALYSIS_PROMPT.format(
                    resume_text=resume_text,
                    job_role=job_role
                )
            )
            
            cleaned_response = self._clean_response(response)
            analysis = json.loads(cleaned_response)
            return self._validate_analysis(analysis)
            
        except Exception as e:
            print(f"Error in resume analysis: {str(e)}")
            if response:
                print(f"Response was: {response}")
            return self._get_default_analysis()

    async def check_ats_compatibility(self, resume_text: str, job_role: str = "") -> Dict:
        response = None
        try:
            response = await self.client.generate_response(
                ATS_ANALYSIS_PROMPT.format(
                    resume_text=resume_text,
                    job_role=job_role
                )
            )
            
            cleaned_response = self._clean_response(response)
            ats_analysis = json.loads(cleaned_response)
            return self._validate_ats_analysis(ats_analysis)
            
        except Exception as e:
            print(f"Error in ATS analysis: {str(e)}")
            if response:
                print(f"Response was: {response}")
            return self._get_default_ats_analysis()

    def _clean_response(self, response: str) -> str:
        cleaned = response.strip()
        if cleaned.startswith('```json'):
            cleaned = cleaned[7:]
        if cleaned.endswith('```'):
            cleaned = cleaned[:-3]
        return cleaned.strip()

    def _validate_analysis(self, analysis: Dict) -> Dict:
        required_fields = {
            "overall_score": 0,
            "section_scores": {
                "professional_experience": 0,
                "education": 0,
                "skills": 0,
                "achievements": 0
            },
            "strengths": [],
            "gaps_identified": [],
            "recommended_skills": [],
            "improvement_suggestions": []
        }
        
        return {**required_fields, **analysis}

    def _validate_ats_analysis(self, analysis: Dict) -> Dict:
        required_fields = {
            "ats_score": 0,
            "format_issues": [],
            "keyword_analysis": {
                "present_keywords": [],
                "missing_keywords": []
            },
            "formatting_suggestions": []
        }
        
        return {**required_fields, **analysis}

    def _get_default_analysis(self) -> Dict:
        return {
            "overall_score": 0,
            "section_scores": {
                "professional_experience": 0,
                "education": 0,
                "skills": 0,
                "achievements": 0
            },
            "strengths": ["Error generating analysis"],
            "gaps_identified": [],
            "recommended_skills": [],
            "improvement_suggestions": []
        }

    def _get_default_ats_analysis(self) -> Dict:
        return {
            "ats_score": 0,
            "format_issues": ["Error generating ATS analysis"],
            "keyword_analysis": {
                "present_keywords": [],
                "missing_keywords": []
            },
            "formatting_suggestions": []
        }