import re
import logging
from typing import Dict, Any, List
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Configurable section header patterns
SECTION_HEADERS = {
    "education": [r"\beducation\b", r"\bacademics?\b", r"\bstudy\b", r"\bstudies\b", r"\bqualification\b", r"\bqualifications\b"],
    "experience": [r"\bexperience\b", r"\bemployment\b", r"\bwork\s+history\b", r"\bprofessional\s+background\b", r"\bcareer\b"],
    "certifications": [r"\bcertifications?\b", r"\bcertificates?\b", r"\bcredentials?\b", r"\bcourses?\b"],
    "projects": [r"\bprojects?\b", r"\bacacademic\s+projects\b", r"\bpersonal\s+projects\b"]
}

# Configurable skill lists
DEFAULT_SKILLS = {
    "programming": ["Python", "Java", "C++", "JavaScript"],
    "web": ["React", "Node", "HTML", "CSS"],
    "ai": ["Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "LLMs", "NLP"],
    "cloud": ["AWS", "Azure", "GCP"],
    "database": ["MySQL", "MongoDB", "PostgreSQL"]
}

class ResumeProfile(BaseModel):
    """
    Pydantic schema representing the parsed candidate details.
    """
    name: str = Field(default="", description="Name of the candidate")
    email: str = Field(default="", description="Email address")
    phone: str = Field(default="", description="Contact number")
    skills: List[str] = Field(default_factory=list, description="Extracted skills")
    experience_years: float = Field(default=0.0, description="Total years of work experience")
    education: List[Dict[str, str]] = Field(default_factory=list, description="Education history details")
    work_history: List[Dict[str, str]] = Field(default_factory=list, description="Work history details")
    certifications: List[str] = Field(default_factory=list, description="Extracted certifications")
    projects: List[str] = Field(default_factory=list, description="Extracted projects")

def extract_name(text: str) -> str:
    """
    Extracts candidate name from text.
    
    Args:
        text (str): Resume text content.
        
    Returns:
        str: Extracted candidate name.
    """
    # 1. Try explicit label pattern: "Name: John Doe"
    match = re.search(r"(?:name|candidate\s+name)\s*:\s*([A-Za-z\s'\.-]+)", text, re.IGNORECASE)
    if match:
        name = match.group(1).strip()
        name = name.split("\n")[0].strip()
        if name:
            return name

    # 2. Grab first few non-empty lines
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    for line in lines[:5]:
        # Skip lines containing common header or contact info keywords
        if not re.search(r"(resume|cv|curriculum|contact|email|phone|address|profile|about|summary|objective|skills|education)", line, re.IGNORECASE):
            words = line.split()
            # Most names are 2-3 words (up to 4)
            if 2 <= len(words) <= 4:
                return line
                
    return "Unknown Candidate"

def extract_email(text: str) -> str:
    """
    Extracts email address using standard regex pattern.
    
    Args:
        text (str): Resume text content.
        
    Returns:
        str: Extracted email address, or empty string.
    """
    match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
    return match.group(0) if match else ""

def extract_phone(text: str) -> str:
    """
    Extracts phone number using general phone number regex pattern.
    
    Args:
        text (str): Resume text content.
        
    Returns:
        str: Extracted phone number, or empty string.
    """
    match = re.search(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
    return match.group(0) if match else ""

def extract_experience_years(text: str) -> float:
    """
    Extracts total years of experience using regex patterns.
    
    Args:
        text (str): Input text content.
        
    Returns:
        float: Calculated years of experience.
    """
    patterns = [
        r"(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|work|dev)",
        r"experience\s*:\s*(\d+(?:\.\d+)?)\s*(?:years?|yrs?)"
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            try:
                return max(float(m) for m in matches)
            except ValueError:
                continue
    return 0.0

def extract_skills(text: str, skill_map: Dict[str, List[str]] = None) -> Dict[str, List[str]]:
    """
    Performs boundary-safe keyword matching for configurable skill sets.
    
    Args:
        text (str): Input text.
        skill_map (Dict[str, List[str]]): Dictionary mapping categories to skill lists.
        
    Returns:
        Dict[str, List[str]]: Extracted skills categorized by area.
    """
    if skill_map is None:
        skill_map = DEFAULT_SKILLS
        
    extracted: Dict[str, List[str]] = {}
    lower_text = text.lower()
    
    for category, skills in skill_map.items():
        matched_skills = []
        for skill in skills:
            escaped_skill = re.escape(skill)
            # Safe boundary check handling alphanumeric and non-alphanumeric trailing symbols like C++
            if re.match(r"^\w", skill):
                pattern = r"\b" + escaped_skill
            else:
                pattern = escaped_skill
                
            if re.search(r"\w$", skill):
                pattern = pattern + r"\b"
            else:
                pattern = pattern
                
            if re.search(pattern, lower_text, re.IGNORECASE):
                matched_skills.append(skill)
        extracted[category] = matched_skills
        
    return extracted

def extract_sections(text: str) -> Dict[str, List[str]]:
    """
    Splits the resume text into sections using common header patterns.
    
    Args:
        text (str): Full resume text.
        
    Returns:
        Dict[str, List[str]]: Mapping of section categories to lines of content.
    """
    lines = text.split("\n")
    sections: Dict[str, List[str]] = {
        "education": [],
        "experience": [],
        "certifications": [],
        "projects": []
    }
    
    current_section = None
    
    for line in lines:
        cleaned_line = line.strip()
        if not cleaned_line:
            continue
            
        lower_line = cleaned_line.lower()
        is_header = False
        
        # Check if line contains a section header, and is short (<= 4 words)
        if len(cleaned_line.split()) <= 4:
            for sec_name, patterns in SECTION_HEADERS.items():
                for pattern in patterns:
                    if re.search(pattern, lower_line):
                        current_section = sec_name
                        is_header = True
                        break
                if is_header:
                    break
                    
        if is_header:
            continue
            
        if current_section:
            sections[current_section].append(cleaned_line)
            
    return sections

def extract_education(text: str) -> List[str]:
    """
    Extracts education details from sections or line-by-line fallback.
    
    Args:
        text (str): Resume text content.
        
    Returns:
        List[str]: Extracted education details lines.
    """
    sections = extract_sections(text)
    edu_lines = sections.get("education", [])
    if edu_lines:
        return edu_lines
        
    fallback = []
    keywords = [r"bachelor", r"master", r"degree", r"university", r"college", r"school", r"\bb\.?s\b", r"\bm\.?s\b"]
    for line in text.split("\n"):
        line_clean = line.strip()
        if any(re.search(kw, line_clean.lower()) for kw in keywords):
            if len(line_clean) < 100:
                fallback.append(line_clean)
    return fallback

def extract_experience(text: str) -> List[str]:
    """
    Extracts professional work experience details.
    
    Args:
        text (str): Resume text content.
        
    Returns:
        List[str]: Lines of work experience records.
    """
    sections = extract_sections(text)
    return sections.get("experience", [])

def extract_certifications(text: str) -> List[str]:
    """
    Extracts certifications details from section or fallback match.
    
    Args:
        text (str): Resume text content.
        
    Returns:
        List[str]: Lines of certifications.
    """
    sections = extract_sections(text)
    cert_lines = sections.get("certifications", [])
    if cert_lines:
        return cert_lines
        
    fallback = []
    keywords = [r"certified", r"certification", r"certificate"]
    for line in text.split("\n"):
        line_clean = line.strip()
        if any(re.search(kw, line_clean.lower()) for kw in keywords):
            if len(line_clean) < 120:
                fallback.append(line_clean)
    return fallback

def extract_projects(text: str) -> List[str]:
    """
    Extracts academic or software project details.
    
    Args:
        text (str): Resume text content.
        
    Returns:
        List[str]: Lines of project details.
    """
    sections = extract_sections(text)
    return sections.get("projects", [])

def extract_resume_data(text: str, skill_list: Dict[str, List[str]] = None) -> Dict[str, Any]:
    """
    Extracts candidate attributes as a structured dictionary.
    
    Args:
        text (str): Resume text.
        skill_list (Dict[str, List[str]]): Optional skill category map.
        
    Returns:
        Dict[str, Any]: Structured dictionary representation of the resume.
    """
    skills_by_cat = extract_skills(text, skill_list)
    
    # Flatten skills list
    all_skills = []
    for cat_skills in skills_by_cat.values():
        all_skills.extend(cat_skills)
        
    return {
        "candidate_name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "skills_by_category": skills_by_cat,
        "skills": all_skills,
        "education": extract_education(text),
        "experience": extract_experience(text),
        "experience_years": extract_experience_years(text),
        "certifications": extract_certifications(text),
        "projects": extract_projects(text)
    }

def extract_resume_info(raw_text: str, model_name: str = "", api_key: str = "") -> ResumeProfile:
    """
    Rule-based extraction runner mapping findings to standard ResumeProfile Pydantic objects.
    
    Args:
        raw_text (str): Raw resume plain text.
        model_name (str): Unused parameter for AI compatibility.
        api_key (str): Unused parameter for AI compatibility.
        
    Returns:
        ResumeProfile: Populated candidate profile object.
    """
    logger.info("Extracting candidate details via rule-based parsers.")
    data = extract_resume_data(raw_text)
    
    edu_list = [{"details": item} for item in data["education"]]
    work_list = [{"details": item} for item in data["experience"]]
    
    return ResumeProfile(
        name=data["candidate_name"],
        email=data["email"],
        phone=data["phone"],
        skills=data["skills"],
        experience_years=data["experience_years"],
        education=edu_list,
        work_history=work_list,
        certifications=data["certifications"],
        projects=data["projects"]
    )

def extract_job_requirements(job_description_text: str, model_name: str = "", api_key: str = "") -> Dict[str, Any]:
    """
    Extracts key requirements and target skills from Job Description using rule-based matches.
    
    Args:
        job_description_text (str): Job Description plain text.
        model_name (str): Unused parameter.
        api_key (str): Unused parameter.
        
    Returns:
        Dict[str, Any]: Map of required fields.
    """
    logger.info("Extracting job requirements using rule-based matching.")
    skills_data = extract_skills(job_description_text)
    
    required_skills = []
    for cat_skills in skills_data.values():
        required_skills.extend(cat_skills)
        
    exp_years = extract_experience_years(job_description_text)
    
    required_education = "Bachelor's Degree"
    if re.search(r"master", job_description_text, re.IGNORECASE):
        required_education = "Master's Degree"
    elif re.search(r"ph\.?d", job_description_text, re.IGNORECASE):
        required_education = "Ph.D."
        
    return {
        "required_skills": required_skills,
        "preferred_skills": [],
        "min_experience_years": exp_years if exp_years > 0 else 3.0,
        "required_education": required_education
    }
