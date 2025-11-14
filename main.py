
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.query import Filter
from sentence_transformers import SentenceTransformer
import numpy as np
import uvicorn
from dotenv import load_dotenv
from core.config import Config
from core.gemini_client import GeminiClient
from agents.evaluation_agent import EvaluationAgent, FeedbackAgent
from agents.resume_analysis_agent import ResumeAnalysisAgent
from services.resume_service import ResumeService
from services.skill_assessment_service import SkillAssessmentService
from weaviate_service import SkillsMatchRequest, match_candidates


# Load environment variables and config
load_dotenv()
config = Config.from_env()
gemini_client = GeminiClient(config)

# Initialize agents and services
evaluation_agent = EvaluationAgent(gemini_client)
feedback_agent = FeedbackAgent(gemini_client)
resume_agent = ResumeAnalysisAgent(gemini_client)
resume_service = ResumeService(gemini_client)
skill_service = SkillAssessmentService(gemini_client)

# Weaviate configuration
class WeaviateConfig:
    CLUSTER_URL = "https://yazyk84ctl2eo4f2guj30a.c0.asia-southeast1.gcp.weaviate.cloud"
    API_KEY = "dummy-weaviate-api-key-value"
    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # React app address
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize sentence transformer model
model = SentenceTransformer(WeaviateConfig.MODEL_NAME)

# Existing Models
class BatchEvaluationRequest(BaseModel):
    questions: List[Dict]
    answers: Dict[int, str]

class EvaluationResponse(BaseModel):
    evaluations: List[Dict]
    total_points: int
    max_possible: int
    feedback: Dict

class ResumeRequest(BaseModel):
    resume_text: str
    job_role: Optional[str] = ""

class ImprovedResumeRequest(BaseModel):
    resume_text: str
    resume_analysis: Dict
    ats_analysis: Dict
    job_role: Optional[str] = ""

class FullResumeResponse(BaseModel):
    resume_analysis: Dict
    ats_analysis: Dict
    improved_resume: str

class ATSResponse(BaseModel):
    ats_analysis: Dict

class ImprovedResumeResponse(BaseModel):
    improved_resume: str

class AssessmentRequest(BaseModel):
    skills: List[str]
    levels: List[str]

# New Models for Candidate Matching
class SkillsMatchRequest(BaseModel):
    skills: List[str]
    batch_size: Optional[int] = 15

class Candidate(BaseModel):
    name: str
    skills: List[str]
    similarity_score: float
    experience: float
    cgpa: float

class BatchResponse(BaseModel):
    batch_number: int
    candidates: List[Candidate]

# Utility functions for candidate matching
def get_weaviate_client():
    """Create and return a Weaviate client"""
    return weaviate.connect_to_weaviate_cloud(
        cluster_url=WeaviateConfig.CLUSTER_URL,
        auth_credentials=Auth.api_key(WeaviateConfig.API_KEY),
    )

def process_candidates(query_embedding: List[float], candidates_data: List[tuple], batch_size: int) -> List[List[Dict]]:
    """Process candidates and return them in batches"""
    results_with_similarity = []
    
    for o in candidates_data:
        candidate_vector = o[0].vector['default']
        similarity = np.dot(query_embedding, candidate_vector) / (
            np.linalg.norm(query_embedding) * np.linalg.norm(candidate_vector)
        )
        experience = float(o[0].properties.get('experience', 0))
        cgpa = float(o[0].properties.get('cgpa', 0))
        results_with_similarity.append((o[0].properties, similarity, experience, cgpa))

    # Sort by experience
    sorted_results = sorted(results_with_similarity, key=lambda x: x[2], reverse=True)

    # Apply similarity and CGPA adjustments
    for i in range(len(sorted_results) - 1):
        current = sorted_results[i]
        next_candidate = sorted_results[i + 1]
        
        if abs(current[1] - next_candidate[1]) < 0.05 and next_candidate[3] > current[3]:
            sorted_results[i], sorted_results[i + 1] = sorted_results[i + 1], sorted_results[i]

    # Split into three batches
    batches = []
    for i in range(0, min(len(sorted_results), batch_size * 3), batch_size):
        batch = sorted_results[i:i + batch_size]
        formatted_batch = [
            {
                "name": props['name'],
                "skills": props['skills'],
                "similarity_score": float(sim),
                "experience": float(exp),
                "cgpa": float(cgpa)
            }
            for props, sim, exp, cgpa in batch
        ]
        batches.append(formatted_batch)
    
    return batches

# Existing endpoints
@app.post("/evaluate")
async def evaluate_assessment(request: BatchEvaluationRequest):
    try:
        evaluations = []
        total_points = 0
        max_possible = 0

        for idx, question in enumerate(request.questions):
            evaluation = await evaluation_agent.evaluate_answer(
                question,
                request.answers.get(idx, "")
            )
            evaluations.append(evaluation)
            total_points += evaluation["points_awarded"]
            max_possible += question["max_points"]

        feedback = await feedback_agent.generate_feedback(
            evaluations,
            request.questions
        )

        return {
            "evaluations": evaluations,
            "total_points": total_points,
            "max_possible": max_possible,
            "feedback": feedback
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze-resume")
async def analyze_resume(request: ResumeRequest):
    try:
        resume_analysis = await resume_agent.analyze_resume(
            request.resume_text,
            request.job_role
        )
        ats_analysis = await resume_agent.check_ats_compatibility(
            request.resume_text,
            request.job_role
        )

        improved_resume = await resume_service.improve_resume(
            request.resume_text,
            resume_analysis,
            ats_analysis,
            request.job_role
        )

        return {
            "resume_analysis": resume_analysis,
            "ats_analysis": ats_analysis,
            "improved_resume": improved_resume
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze-ats")
async def analyze_ats(request: ResumeRequest):
    try:
        ats_analysis = await resume_agent.check_ats_compatibility(
            request.resume_text,
            request.job_role
        )
        
        return {
            "ats_analysis": ats_analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/improve-resume")
async def improve_resume(request: ImprovedResumeRequest):
    try:
        improved_resume = await resume_service.improve_resume(
            request.resume_text,
            request.resume_analysis,
            request.ats_analysis,
            request.job_role
        )
        
        return {
            "improved_resume": improved_resume
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-assessment")
async def generate_assessment(request: AssessmentRequest):
    try:
        skills_with_levels = [
            {"skill": skill, "level": level} 
            for skill, level in zip(request.skills, request.levels)
        ]
        
        assessment = await skill_service.generate_assessment(skills_with_levels)
        
        return {
            "success": True,
            "questions": assessment["questions"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# New endpoint for candidate matching
@app.post("/match-candidates", response_model=Dict[str, Any])
async def match_candidates_endpoint(request: SkillsMatchRequest):
    try:
        return match_candidates(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8500, reload=True)