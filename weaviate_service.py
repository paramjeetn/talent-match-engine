from fastapi import HTTPException
from pydantic import BaseModel
from typing import List, Optional
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.query import Filter
from sentence_transformers import SentenceTransformer
import numpy as np

# Weaviate configuration
class WeaviateConfig:
    CLUSTER_URL = "https://yazyk84ctl2eo4f2guj30a.c0.asia-southeast1.gcp.weaviate.cloud"
    API_KEY = "dummy-weaviate-api-key-value"
    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Models for Candidate Matching
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

def match_candidates(request: SkillsMatchRequest) -> BatchResponse:
    model = SentenceTransformer(WeaviateConfig.MODEL_NAME)
    
    # Step 1: Generate Query Embedding from Skills
    query_string = ", ".join(request.skills)
    query_embedding = model.encode(query_string).tolist()

    # Step 2: Connect to Weaviate client
    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=WeaviateConfig.CLUSTER_URL,
        auth_credentials=Auth.api_key(WeaviateConfig.API_KEY),
    )
    
    # Step 3: Fetch candidates based on skills
    collection = client.collections.get("Candidate_Data_embedded")
    
    response = collection.query.fetch_objects(
        filters=Filter.by_property("skills").contains_any(request.skills),
        limit=request.batch_size,
        include_vector=True,
    )

    # Step 4: Calculate similarity scores and prepare response
    results_with_similarity = []
    
    for o in response.objects:
        candidate_vector = o.vector['default']
        similarity = np.dot(query_embedding, candidate_vector) / (
            np.linalg.norm(query_embedding) * np.linalg.norm(candidate_vector)
        )
        experience = float(o.properties.get('experience', 0))
        cgpa = float(o.properties.get('cgpa', 0))
        
        results_with_similarity.append((o.properties, similarity, experience, cgpa))

    # Sort results by experience and return top candidates
    sorted_results = sorted(results_with_similarity, key=lambda x: x[2], reverse=True)
    
    candidates_response = [
        Candidate(
            name=properties['name'],
            skills=properties['skills'],
            similarity_score=similarity,
            experience=experience,
            cgpa=cgpa,
        ) for properties, similarity, experience, cgpa in sorted_results[:request.batch_size]
    ]

    return BatchResponse(batch_number=1, candidates=candidates_response)
