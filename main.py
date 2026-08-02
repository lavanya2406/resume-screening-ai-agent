import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any

from config import load_config, AppConfig
from utils import setup_logging, read_text_file, save_json_file, save_csv_file
from parser import load_all_resumes
from extractor import extract_resume_info, extract_job_requirements
from similarity import calculate_skill_overlap, calculate_semantic_similarity
from scorer import calculate_composite_score

logger = logging.getLogger(__name__)

def process_resume(
    filename: str,
    raw_text: str,
    job_reqs: Dict[str, Any],
    config: AppConfig
) -> Dict[str, Any]:
    """
    Orchestrates the parsing, extraction, similarity comparison, 
    and scoring for a single candidate resume.
    
    Args:
        filename (str): Name of the resume file.
        raw_text (str): Pre-loaded clean text from the resume.
        job_reqs (Dict[str, Any]): Parsed/extracted job requirements.
        config (AppConfig): Application configuration parameters.
        
    Returns:
        Dict[str, Any]: Scored evaluation details for the candidate.
    """
    logger.info("Processing resume: %s", filename)
    
    # 1. Extract structured candidate profile
    profile = extract_resume_info(
        raw_text=raw_text, 
        model_name=config.gemini_model, 
        api_key=config.gemini_api_key
    )
    
    # Override name to filename if default mock name is returned, for better tracking in structure
    if profile.name == "John Doe" and filename != "john_doe.txt":
        profile.name = Path(filename).stem.replace("_", " ").title()
    
    # 2. Calculate similarity score metrics
    req_skills = job_reqs.get("required_skills", [])
    skill_score = calculate_skill_overlap(profile.skills, req_skills)
    
    # Calculate semantic similarity between raw resume and raw job description
    semantic_score = calculate_semantic_similarity(raw_text, job_reqs.get("raw_text", ""))
    
    # 3. Generate final score breakdown
    evaluation = calculate_composite_score(
        profile=profile,
        requirements=job_reqs,
        skill_score=skill_score,
        semantic_score=semantic_score
    )
    
    return evaluation

def run_agent(config: AppConfig) -> List[Dict[str, Any]]:
    """
    Runs the main agent loop to parse job descriptions and batch process resumes.
    
    Args:
        config (AppConfig): Application configuration parameters.
        
    Returns:
        List[Dict[str, Any]]: Sorted leaderboard evaluations list.
    """
    logger.info("Starting Resume Screening Agent run...")
    
    # 1. Load job description
    jd_path = config.sample_data_dir / "job_description.txt"
    if not jd_path.exists():
        logger.error("Job description file not found at: %s", jd_path)
        raise FileNotFoundError(f"Missing job description file at {jd_path}")
        
    jd_text = read_text_file(jd_path)
    job_reqs = extract_job_requirements(
        job_description_text=jd_text,
        model_name=config.gemini_model,
        api_key=config.gemini_api_key
    )
    # Store raw job description text for semantic similarity calculations
    job_reqs["raw_text"] = jd_text
    
    # 2. Iterate and batch load through resume directory
    resumes_dir = config.sample_data_dir / "resumes"
    if not resumes_dir.exists():
        logger.warning("Resumes directory does not exist. Creating empty path: %s", resumes_dir)
        resumes_dir.mkdir(parents=True, exist_ok=True)
        return []
        
    # Batch load all resumes from folder
    resumes_data = load_all_resumes(resumes_dir)
    
    # Demonstrate loading all resumes and printing filenames
    print("\n--- Loaded Resumes ---")
    if not resumes_data:
        print("No resumes found.")
    for filename in resumes_data.keys():
        print(f"Loaded File: {filename}")
    print("----------------------\n")
    
    if not resumes_data:
        logger.info("No resumes found or successfully loaded in directory: %s", resumes_dir)
        return []
        
    evaluations: List[Dict[str, Any]] = []
    
    for filename, raw_text in resumes_data.items():
        try:
            evaluation = process_resume(filename, raw_text, job_reqs, config)
            evaluations.append(evaluation)
        except Exception as err:
            logger.exception("Failed to process resume %s: %s", filename, err)
            
    # 3. Rank candidates based on final score desc
    ranked_evaluations = sorted(evaluations, key=lambda x: x["final_score"], reverse=True)
    
    # 4. Save results reports (JSON and CSV)
    json_output_path = config.output_dir / "ranking.json"
    csv_output_path = config.output_dir / "ranking.csv"
    
    save_json_file(ranked_evaluations, json_output_path)
    
    csv_rows = []
    for rank, res in enumerate(ranked_evaluations, start=1):
        reasoning = res.get("reasoning", [])
        reason_str = "; ".join(reasoning) if reasoning else ""
        csv_rows.append({
            "Rank": rank,
            "Candidate": res.get("candidate_name", "Unknown"),
            "Score": f"{res.get('final_score', 0.0):.2f}%",
            "Similarity": f"{res.get('breakdown', {}).get('semantic_match', 0.0):.2f}%",
            "Reason": reason_str
        })
        
    csv_headers = ["Rank", "Candidate", "Score", "Similarity", "Reason"]
    save_csv_file(csv_rows, csv_output_path, csv_headers)
    
    logger.info("Evaluation loop complete. Reports saved to: %s and %s", json_output_path, csv_output_path)
    return ranked_evaluations

def print_rankings_table(results: List[Dict[str, Any]]) -> None:
    """
    Prints candidate evaluation results in a nicely formatted terminal table.
    
    Args:
        results (List[Dict[str, Any]]): List of candidate evaluation dictionaries.
    """
    if not results:
        print("No candidates to rank.")
        return
        
    headers = ["Rank", "Candidate", "Score", "Similarity", "Reason / Highlights"]
    col_widths = [6, 20, 8, 12, 55]
    
    # Format line separator
    separator = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
    
    print("\n" + separator)
    # Print headers
    header_str = "|"
    for h, w in zip(headers, col_widths):
        header_str += f" {h:<{w}} |"
    print(header_str)
    print(separator)
    
    # Print candidates
    for rank, res in enumerate(results, start=1):
        name = res.get("candidate_name", "Unknown")
        score = f"{res.get('final_score', 0.0):.2f}%"
        similarity = f"{res.get('breakdown', {}).get('semantic_match', 0.0):.2f}%"
        
        # Pick the top highlight or join reasoning sentences
        reasoning = res.get("reasoning", [])
        reason_str = ", ".join(reasoning) if reasoning else "N/A"
        if len(reason_str) > col_widths[4]:
            reason_str = reason_str[:col_widths[4] - 3] + "..."
            
        row_str = f"| {rank:<{col_widths[0]}} | {name:<{col_widths[1]}} | {score:<{col_widths[2]}} | {similarity:<{col_widths[3]}} | {reason_str:<{col_widths[4]}} |"
        print(row_str)
        
    print(separator + "\n")

def main() -> None:
    """
    Entry point for CLI parsing and agent execution.
    """
    parser = argparse.ArgumentParser(description="Resume Screening AI Agent CLI")
    parser.add_argument(
        "--config", 
        type=str, 
        default=None, 
        help="Optional path to dotenv configuration file override"
    )
    args = parser.parse_args()
    
    # Load configuration
    config = load_config()
    
    # Initialize logging using config parameters
    setup_logging(level=config.log_level)
    
    try:
        results = run_agent(config)
        print_rankings_table(results)
    except Exception as e:
        logger.critical("Agent execution terminated with critical failure: %s", e, exc_info=True)

if __name__ == "__main__":
    main()
