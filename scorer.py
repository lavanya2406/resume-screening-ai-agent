import logging
from typing import Dict, Any, List
from extractor import ResumeProfile

logger = logging.getLogger(__name__)

def score_experience(candidate_years: float, required_years: float) -> float:
    """
    Computes a score based on candidate years of experience vs required.
    
    Args:
        candidate_years (float): Candidate's total years of experience.
        required_years (float): Minimum required years of experience.
        
    Returns:
        float: Experience score between 0.0 and 1.0.
    """
    if required_years <= 0:
        return 1.0
    
    # Calculate ratio, capped at 1.2, and normalize relative to that cap
    score = min(candidate_years / required_years, 1.2)
    normalized_score = min(score / 1.2, 1.0)
    logger.debug("Experience scoring: Candidate=%.1f, Required=%.1f, Score=%.2f", candidate_years, required_years, normalized_score)
    return normalized_score

def score_education(candidate_education: List[Dict[str, str]], required_education: str) -> float:
    """
    Scores the candidate's education against job requirements.
    
    Args:
        candidate_education (List[Dict[str, str]]): Extracted education history lines.
        required_education (str): Job description education level requirement.
        
    Returns:
        float: Education score between 0.0 and 1.0.
    """
    if not required_education:
        return 1.0
        
    req_edu_lower = required_education.lower()
    edu_text = " ".join(item.get("details", "").lower() for item in candidate_education)
    
    # Doctoral level requirement
    if any(term in req_edu_lower for term in ["ph.d", "phd", "doctorate", "doctor"]):
        if any(term in edu_text for term in ["phd", "ph.d", "doctor"]):
            return 1.0
        elif any(term in edu_text for term in ["master", "ms", "m.s", "m.tech", "mtech"]):
            return 0.6
        elif any(term in edu_text for term in ["bachelor", "bs", "b.s", "b.tech", "btech"]):
            return 0.3
        return 0.0
        
    # Master's level requirement
    if any(term in req_edu_lower for term in ["master", "ms", "m.s", "m.tech", "mtech"]):
        if any(term in edu_text for term in ["phd", "ph.d", "doctor", "master", "ms", "m.s", "m.tech", "mtech"]):
            return 1.0
        elif any(term in edu_text for term in ["bachelor", "bs", "b.s", "b.tech", "btech"]):
            return 0.5
        return 0.0
        
    # Bachelor's level requirement (default)
    if any(term in req_edu_lower for term in ["bachelor", "bs", "b.s", "b.tech", "btech", "degree"]):
        if any(term in edu_text for term in ["phd", "ph.d", "doctor", "master", "ms", "m.s", "bachelor", "bs", "b.s", "degree", "university", "college"]):
            return 1.0
        return 0.0
        
    return 1.0

def generate_reasoning(
    profile: ResumeProfile,
    requirements: Dict[str, Any],
    skill_score: float,
    semantic_score: float,
    exp_score: float,
    edu_score: float
) -> List[str]:
    """
    Generates structured reasoning bullets explaining the candidate score.
    
    Args:
        profile (ResumeProfile): Candidate profile.
        requirements (Dict[str, Any]): Job description requirements.
        skill_score (float): Skill overlap score ratio.
        semantic_score (float): Cosine similarity score.
        exp_score (float): Experience score ratio.
        edu_score (float): Education score ratio.
        
    Returns:
        List[str]: List of reasoning items.
    """
    reasoning = []
    cand_skills_lower = {s.lower().strip() for s in profile.skills}
    req_skills = requirements.get("required_skills", [])
    req_skills_lower = {s.lower().strip() for s in req_skills}
    
    # 1. Individual Skills Matches
    if "python" in cand_skills_lower:
        if "python" in req_skills_lower:
            reasoning.append("Strong Python match")
        else:
            reasoning.append("Has Python programming experience")
            
    if any(s in cand_skills_lower for s in ["nlp", "natural language processing"]):
        reasoning.append("Has NLP experience")
        
    if "aws" in req_skills_lower and "aws" not in cand_skills_lower:
        reasoning.append("Missing AWS")
        
    # 2. Skill Overlap Matching
    if skill_score >= 0.8:
        reasoning.append("Excellent technical skills matching job requirements")
    elif skill_score >= 0.5:
        reasoning.append("Good technical skills matching job requirements")
    elif skill_score > 0.0:
        reasoning.append("Possesses some requested technical skills")
    else:
        reasoning.append("Technical skills overlap is low")
        
    # 3. Experience Match
    req_exp = float(requirements.get("min_experience_years", 0.0))
    if profile.experience_years >= req_exp and req_exp > 0:
        reasoning.append(f"Meets minimum experience requirement ({profile.experience_years:.1f} years)")
    elif profile.experience_years > 0:
        reasoning.append(f"Has {profile.experience_years:.1f} years of experience, but less than requested {req_exp:.1f} years")
        
    # 4. Education Match
    if edu_score >= 1.0:
        reasoning.append("Good education background matching job requirement")
    elif edu_score >= 0.5:
        reasoning.append("Education background partially meets requirements")
    else:
        reasoning.append("Education details do not explicitly show matching degree")
        
    # 5. Semantic Match
    if semantic_score >= 0.75:
        reasoning.append("High semantic similarity matching job profile")
    elif semantic_score >= 0.5:
        reasoning.append("Moderate semantic match with the job description")
    else:
        reasoning.append("Low overall semantic overlap with target job profile")
        
    return reasoning

def calculate_composite_score(
    profile: ResumeProfile, 
    requirements: Dict[str, Any], 
    skill_score: float, 
    semantic_score: float
) -> Dict[str, Any]:
    """
    Generates a final screening report and score for a candidate using a weighted system.
    
    Args:
        profile (ResumeProfile): Extracted candidate profile details.
        requirements (Dict[str, Any]): Extracted requirements from job description.
        skill_score (float): Skill overlap score.
        semantic_score (float): Text semantic similarity score.
        
    Returns:
        Dict[str, Any]: Dictionary containing final breakdown, total score, and reasoning.
    """
    logger.info("Calculating composite score for candidate: %s", profile.name)
    
    req_exp = float(requirements.get("min_experience_years", 0.0))
    exp_score = score_experience(profile.experience_years, req_exp)
    
    req_edu = requirements.get("required_education", "Bachelor's Degree")
    edu_score = score_education(profile.education, req_edu)
    
    # Calculate composite score based on user requested weights
    final_score = (
        (semantic_score * 0.60) +
        (skill_score * 0.20) +
        (exp_score * 0.10) +
        (edu_score * 0.10)
    ) * 100.0
    
    reasoning_list = generate_reasoning(
        profile=profile,
        requirements=requirements,
        skill_score=skill_score,
        semantic_score=semantic_score,
        exp_score=exp_score,
        edu_score=edu_score
    )
    
    score_details = {
        "candidate_name": profile.name,
        "email": profile.email,
        "final_score": round(final_score, 2),
        "breakdown": {
            "semantic_match": round(semantic_score * 100, 2),
            "skills_match": round(skill_score * 100, 2),
            "experience_match": round(exp_score * 100, 2),
            "education_match": round(edu_score * 100, 2)
        },
        "reasoning": reasoning_list
    }
    
    logger.info("Composite score for %s calculated: %.2f", profile.name, final_score)
    return score_details
