# agents/evaluation_agent.py
import json
from typing import Dict, List
from core.gemini_client import GeminiClient

EVALUATION_PROMPT = '''
You are an expert evaluator. Evaluate this student's answer for a Python programming question.

QUESTION:
{question}

MAXIMUM POINTS: {max_points}

EXPECTED ANSWER ELEMENTS:
{expected_answer}

STUDENT'S ANSWER:
```python
{answer}
```

Evaluate the answer focusing on Python programming concepts and provide your evaluation in EXACTLY the following JSON format:
{{
    "points_awarded": number,
    "explanation": "evaluation explanation",
    "key_points_covered": [
        "point 1",
        "point 2"
    ],
    "missing_points": [
        "missing point 1",
        "missing point 2"
    ]
}}

IMPORTANT: You must respond ONLY with the JSON object, no additional text or explanation.
'''

FEEDBACK_PROMPT = '''
You are a supportive programming mentor. Review this student's Python assessment performance and provide personalized feedback.

Assessment Results:
{results}

Provide feedback in EXACTLY the following JSON format:
{{
    "overall_assessment": "brief analysis of overall Python skills",
    "strengths": [
        "strength 1",
        "strength 2"
    ],
    "areas_to_improve": [
        "area 1",
        "area 2"
    ],
    "learning_recommendations": [
        {{
            "topic": "specific Python concept",
            "reason": "why this needs focus",
            "resources": [
                "resource suggestion 1",
                "resource suggestion 2"
            ]
        }}
    ],
    "next_steps": [
        "step 1",
        "step 2"
    ],
    "encouragement": "motivational message"
}}

IMPORTANT: You must respond ONLY with the JSON object, no additional text or explanation.
'''

class EvaluationAgent:
    def __init__(self, gemini_client: GeminiClient):
        self.client = gemini_client

    async def evaluate_answer(self, question: Dict, answer: str) -> Dict:
        # Clean and format the answer for proper JSON handling
        cleaned_answer = answer.strip().replace('\r\n', '\n')
        
        prompt = EVALUATION_PROMPT.format(
            question=question["question"],
            max_points=question["max_points"],
            expected_answer=question["expected_answer"],
            answer=cleaned_answer
        )
        
        try:
            response = await self.client.generate_response(prompt)
            # Clean the response to ensure it's valid JSON
            cleaned_response = response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            
            evaluation = json.loads(cleaned_response.strip())
            
            # Validate the required fields
            required_fields = ["points_awarded", "explanation", "key_points_covered", "missing_points"]
            for field in required_fields:
                if field not in evaluation:
                    evaluation[field] = [] if field in ["key_points_covered", "missing_points"] else ""
            
            return evaluation
            
        except Exception as e:
            print(f"Error in evaluation: {str(e)}\nResponse was: {response}")
            return {
                "points_awarded": 0,
                "explanation": "Error in evaluation process",
                "key_points_covered": [],
                "missing_points": []
            }

class FeedbackAgent:
    def __init__(self, gemini_client: GeminiClient):
        self.client = gemini_client

    async def generate_feedback(self, evaluations: List[Dict], questions: List[Dict]) -> Dict:
        # Format results for the prompt
        results = []
        for q, e in zip(questions, evaluations):
            results.append({
                "question_topic": q["skill"],
                "points": f"{e['points_awarded']}/{q['max_points']}",
                "strengths": e["key_points_covered"],
                "weaknesses": e["missing_points"]
            })
        
        prompt = FEEDBACK_PROMPT.format(
            results=json.dumps(results, indent=2)
        )
        
        try:
            response = await self.client.generate_response(prompt)
            # Clean the response to ensure it's valid JSON
            cleaned_response = response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            
            feedback = json.loads(cleaned_response.strip())
            
            # Validate the required fields
            required_fields = ["overall_assessment", "strengths", "areas_to_improve", 
                             "learning_recommendations", "next_steps", "encouragement"]
            for field in required_fields:
                if field not in feedback:
                    feedback[field] = [] if field in ["strengths", "areas_to_improve", 
                                                    "learning_recommendations", "next_steps"] else ""
            
            return feedback
            
        except Exception as e:
            print(f"Error in feedback generation: {str(e)}\nResponse was: {response}")
            return {
                "overall_assessment": "Error generating feedback",
                "strengths": [],
                "areas_to_improve": [],
                "learning_recommendations": [],
                "next_steps": [],
                "encouragement": "Please try again"
            }