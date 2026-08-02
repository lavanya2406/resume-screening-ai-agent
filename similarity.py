import logging
from typing import List, Set, Any
import numpy as np

logger = logging.getLogger(__name__)

# Cache for the loaded sentence-transformers model
_MODEL_CACHE = None

def load_model() -> Any:
    """
    Loads and caches the SentenceTransformer model 'all-MiniLM-L6-v2'.
    
    Returns:
        SentenceTransformer: Cached model instance, or None if loading fails.
    """
    global _MODEL_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE
        
    try:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading SentenceTransformer model 'all-MiniLM-L6-v2'...")
        _MODEL_CACHE = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("SentenceTransformer model loaded successfully.")
    except Exception as e:
        logger.error("Failed to load SentenceTransformer model: %s", e, exc_info=True)
        _MODEL_CACHE = None
        
    return _MODEL_CACHE

def calculate_similarity(job_description: str, resume_text: str) -> float:
    """
    Calculates the cosine similarity between the job description and the resume text.
    
    Args:
        job_description (str): Text of the job description.
        resume_text (str): Text of the candidate's resume.
        
    Returns:
        float: Cosine similarity score between 0.0 and 1.0. Returns 0.0 if loading or computation fails.
    """
    model = load_model()
    if model is None:
        logger.warning("Similarity model not available. Returning default similarity score (0.0).")
        return 0.0
        
    try:
        # Encode both texts to get embeddings
        embeddings = model.encode([job_description, resume_text])
        
        emb_jd = embeddings[0]
        emb_res = embeddings[1]
        
        # Calculate cosine similarity: (A . B) / (||A|| * ||B||)
        dot_product = np.dot(emb_jd, emb_res)
        norm_jd = np.linalg.norm(emb_jd)
        norm_res = np.linalg.norm(emb_res)
        
        if norm_jd == 0.0 or norm_res == 0.0:
            return 0.0
            
        similarity = dot_product / (norm_jd * norm_res)
        
        # Clip score between 0.0 and 1.0 (sometimes float precision can yield minor out of bounds)
        similarity_score = float(np.clip(similarity, 0.0, 1.0))
        logger.debug("Cosine similarity calculated: %.4f", similarity_score)
        return similarity_score
    except Exception as e:
        logger.error("Error occurred while calculating similarity: %s", e, exc_info=True)
        return 0.0

def calculate_jaccard_similarity(set_a: Set[str], set_b: Set[str]) -> float:
    """
    Computes Jaccard Similarity score between two sets of strings.
    
    Args:
        set_a (Set[str]): First set of tokens.
        set_b (Set[str]): Second set of tokens.
        
    Returns:
        float: Similarity score between 0.0 and 1.0.
    """
    if not set_a or not set_b:
        return 0.0
    intersection = set_a.intersection(set_b)
    union = set_a.union(set_b)
    score = len(intersection) / len(union)
    logger.debug("Jaccard similarity calculated: %d intersection / %d union = %.4f", len(intersection), len(union), score)
    return score

def calculate_skill_overlap(candidate_skills: List[str], required_skills: List[str]) -> float:
    """
    Calculates the ratio of required skills that are possessed by the candidate.
    
    Args:
        candidate_skills (List[str]): List of candidate's skills.
        required_skills (List[str]): List of required skills from the job description.
        
    Returns:
        float: Overlap score between 0.0 and 1.0.
    """
    if not required_skills:
        return 1.0
    cand_set = {skill.strip().lower() for skill in candidate_skills}
    req_set = {skill.strip().lower() for skill in required_skills}
    
    overlap = cand_set.intersection(req_set)
    score = len(overlap) / len(req_set)
    logger.info("Skill overlap score: %.2f (%d of %d required skills matched)", score, len(overlap), len(req_set))
    return score

def calculate_semantic_similarity(text_a: str, text_b: str) -> float:
    """
    Wrapper for semantic similarity mapping to calculate_similarity.
    
    Args:
        text_a (str): Source text (e.g. Job Description).
        text_b (str): Target text (e.g. Resume).
        
    Returns:
        float: Cosine similarity score.
    """
    return calculate_similarity(text_a, text_b)
