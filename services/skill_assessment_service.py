import json
import re
from typing import List, Dict, Any

ASSESSMENT_PROMPT = """
Generate a total of exactly 5 assessment questions for the following skill(s) and level(s):
Skills and Levels: {skills_info}

Return the response in the following JSON format:
{{
    "questions": [
        {{
            "skill": "skill_name",
            "difficulty": "easy/medium/hard",
            "question": "question text",
            "expected_answer": "brief explanation of what a good answer should contain",
            "max_points": points_value
        }}
    ]
}}

Important:
- Generate EXACTLY 5 questions in total
- Distribute questions fairly among the provided skills
- Mix difficulty levels appropriately based on the skill levels
- Points: easy=10, medium=15, hard=20
- Make questions clear and specific
"""

class SkillAssessmentService:
    def __init__(self, gemini_client):
        self.client = gemini_client

    def safe_load_json(self, text: str) -> Dict[str, Any]:
        try:
            # Extract JSON content using regex
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                json_string = match.group(0)
                return json.loads(json_string)
            else:
                print("No valid JSON found in the input text.")
                return {"questions": []}
        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {e}")
            return {"questions": []}

    async def generate_assessment(self, skills_with_levels: List[Dict[str, str]]) -> Dict[str, Any]:
        # Format skills info for prompt
        skills_info = ", ".join([f"{s['skill']} ({s['level']})" for s in skills_with_levels])
        
        prompt = ASSESSMENT_PROMPT.format(skills_info=skills_info)
        
        try:
            response = await self.client.generate_response(prompt)
            print("Response:", response)
            
            questions = self.safe_load_json(response)
            print("Parsed Questions:", questions)
            return questions
        except Exception as e:
            print(f"Error generating questions: {e}")
            return {"questions": []}
