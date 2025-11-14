import chromadb
from sentence_transformers import SentenceTransformer
import json
import hashlib
from typing import List, Dict, Tuple
import os
from dataclasses import dataclass
from math import ceil

@dataclass
class PaginationInfo:
    page: int
    total_pages: int
    total_results: int
    page_size: int

class PriorityMatchingSystem:
    def __init__(self, persistent_path: str = "./chroma_data"):
        self.client = chromadb.PersistentClient(path=persistent_path)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Create collections
        self.candidates = self.client.get_or_create_collection(
            name="candidates",
            metadata={"description": "Candidate profiles"}
        )
        
        self.jobs = self.client.get_or_create_collection(
            name="jobs",
            metadata={"description": "Job profiles"}
        )
        
        print(f"ChromaDB initialized with persistence at {persistent_path}")

    def _create_skills_embedding(self, skills: List[str]) -> List[float]:
        """Create embedding only for skills"""
        text = ", ".join(skills)
        return self.model.encode(text).tolist()

    def _prepare_metadata(self, profile: Dict) -> Dict:
        """Prepare metadata for ChromaDB storage"""
        return {
            "skills_str": ",".join(profile['skills']),
            "CGPA": float(profile['CGPA']),
            "exp": int(profile['exp'])
        }

    def _generate_id(self, profile: Dict) -> str:
        profile_str = f"{'-'.join(sorted(profile['skills']))}-{profile['CGPA']}-{profile['exp']}"
        return hashlib.md5(profile_str.encode()).hexdigest()

    def ingest_profiles(self, file_path: str, collection_type: str) -> List[str]:
        try:
            with open(file_path, 'r') as file:
                profiles = json.load(file)
            
            print(f"Found {len(profiles)} profiles in {file_path}")
            collection = self.candidates if collection_type == "candidates" else self.jobs
            
            embeddings = []
            metadatas = []
            ids = []
            
            for profile in profiles:
                try:
                    # Create embedding only from skills
                    embedding = self._create_skills_embedding(profile['skills'])
                    profile_id = self._generate_id(profile)
                    metadata = self._prepare_metadata(profile)
                    
                    embeddings.append(embedding)
                    metadatas.append(metadata)
                    ids.append(profile_id)
                    
                except Exception as e:
                    print(f"Error processing profile: {e}")
                    continue
            
            if embeddings:
                collection.add(
                    embeddings=embeddings,
                    metadatas=metadatas,
                    ids=ids
                )
            
            return ids
            
        except Exception as e:
            print(f"Error during ingestion: {e}")
            raise

    def _calculate_scores(self, required_profile: Dict, candidate_profile: Dict) -> Tuple[float, float, float]:
        """Calculate individual scores for skills, experience, and CGPA"""
        # Skills match score is handled by vector similarity
        
        # Experience score (closer to required = better)
        exp_diff = abs(required_profile['exp'] - candidate_profile['exp'])
        exp_score = 1.0 / (1.0 + exp_diff)  # Normalize to 0-1
        
        # CGPA score (meeting or exceeding requirement = 1, below = proportional)
        cgpa_score = min(1.0, candidate_profile['CGPA'] / required_profile['CGPA'])
        
        return exp_score, cgpa_score

    def search_matches(
        self, 
        profile: Dict, 
        collection_type: str = "jobs", 
        page: int = 1, 
        page_size: int = 5,
        exp_weight: float = 0.3,
        cgpa_weight: float = 0.2
    ) -> Tuple[List[Dict], PaginationInfo]:
        """
        Search for matching profiles with pagination and weighted scoring
        """
        try:
            # Create embedding from only skills
            query_embedding = self._create_skills_embedding(profile['skills'])
            
            # Get more results than needed for post-processing
            fetch_size = page_size * 3  # Fetch extra to allow for sorting
            collection = self.jobs if collection_type == "candidates" else self.candidates
            
            # Initial vector search based on skills
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=fetch_size,
                include=["metadatas", "distances"]
            )
            
            # Process and sort results
            processed_matches = []
            for i in range(len(results['ids'][0])):
                stored_metadata = results['metadatas'][0][i]
                candidate_profile = {
                    'skills': stored_metadata['skills_str'].split(','),
                    'CGPA': stored_metadata['CGPA'],
                    'exp': stored_metadata['exp']
                }
                
                # Calculate individual scores
                exp_score, cgpa_score = self._calculate_scores(profile, candidate_profile)
                
                # Skills similarity from vector search (convert distance to similarity)
                skills_score = 1 - results['distances'][0][i]
                
                # Calculate final weighted score
                final_score = (
                    skills_score * 0.5 +  # 50% weight to skills
                    exp_score * exp_weight +  # 30% weight to experience
                    cgpa_score * cgpa_weight  # 20% weight to CGPA
                )
                
                processed_matches.append({
                    'profile': candidate_profile,
                    'similarity_score': final_score,
                    'individual_scores': {
                        'skills_match': skills_score,
                        'experience_match': exp_score,
                        'cgpa_match': cgpa_score
                    }
                })
            
            # Sort by final score
            processed_matches.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            # Calculate pagination
            total_results = len(processed_matches)
            total_pages = ceil(total_results / page_size)
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            
            pagination_info = PaginationInfo(
                page=page,
                total_pages=total_pages,
                total_results=total_results,
                page_size=page_size
            )
            
            return processed_matches[start_idx:end_idx], pagination_info
            
        except Exception as e:
            print(f"Error searching matches: {e}")
            raise

def main():
    matcher = PriorityMatchingSystem()
    
    # Ingest profiles
    candidates_file = "student.json"
    jobs_file = "companies.json"
    
    print("\nIngesting candidates...")
    matcher.ingest_profiles(candidates_file, "candidates")
    
    print("\nIngesting jobs...")
    matcher.ingest_profiles(jobs_file, "jobs")
    
    # Example search
    with open(candidates_file, 'r') as file:
        candidates = json.load(file)
        if candidates:
            print("\nSearching matches for first candidate...")
            matches, pagination = matcher.search_matches(
                candidates[0], 
                "companies",
                page=1, 
                page_size=5
            )
            
            print(f"\nShowing page {pagination.page} of {pagination.total_pages}")
            print(f"Total results: {pagination.total_results}")
            
            for i, match in enumerate(matches, 1):
                print(f"\nMatch {i}:")
                print(f"Skills: {match['profile']['skills']}")
                print(f"Experience: {match['profile']['exp']} years")
                print(f"CGPA: {match['profile']['CGPA']}")
                print("Scores:")
                print(f"  Overall: {match['similarity_score']:.2f}")
                print(f"  Skills Match: {match['individual_scores']['skills_match']:.2f}")
                print(f"  Experience Match: {match['individual_scores']['experience_match']:.2f}")
                print(f"  CGPA Match: {match['individual_scores']['cgpa_match']:.2f}")

if __name__ == "__main__":
    main()