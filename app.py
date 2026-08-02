import streamlit as st
import os
import shutil
import textwrap
from pathlib import Path
import pandas as pd
import json

from config import load_config
from utils import save_json_file, save_csv_file
from parser import load_all_resumes
from extractor import extract_job_requirements
from main import process_resume

# Page configurations
st.set_page_config(
    page_title="Resume Screening AI Agent",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif;
}

.dashboard-header {
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
    padding: 2.5rem;
    border-radius: 12px;
    color: white;
    margin-bottom: 2rem;
    box-shadow: 0 10px 25px -5px rgba(79, 70, 229, 0.2);
    text-align: center;
}

.dashboard-header h1 {
    font-size: 2.8rem;
    font-weight: 700;
    margin: 0;
    color: white !important;
    letter-spacing: -0.025em;
}

.dashboard-header p {
    font-size: 1.2rem;
    opacity: 0.9;
    color: #e0e7ff;
    margin: 0.5rem 0 0 0;
}

.card {
    background-color: #ffffff;
    padding: 1.5rem;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    margin-bottom: 1.5rem;
    color: #1e293b;
}

.top-match-card {
    background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
    border: 1.5px solid #818cf8;
    padding: 1.8rem;
    border-radius: 14px;
    margin-bottom: 1.5rem;
    box-shadow: 0 10px 15px -3px rgba(99, 102, 241, 0.1);
    color: #1e293b;
}

.top-match-badge {
    background-color: #4f46e5;
    color: white;
    padding: 0.3rem 0.8rem;
    font-size: 0.75rem;
    font-weight: 600;
    border-radius: 9999px;
    text-transform: uppercase;
    display: inline-block;
    margin-bottom: 0.8rem;
}

.metric-container {
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    margin-bottom: 1.5rem;
}

.metric-box {
    flex: 1;
    background-color: #ffffff;
    padding: 1.2rem;
    border-radius: 10px;
    border: 1px solid #e2e8f0;
    text-align: center;
    box-shadow: 0 2px 4px rgba(0,0,0,0.02);
}

.metric-number {
    font-size: 2.2rem;
    font-weight: 700;
    color: #4f46e5;
}

.metric-label {
    font-size: 0.8rem;
    color: #64748b;
    text-transform: uppercase;
    font-weight: 600;
    letter-spacing: 0.05em;
    margin-top: 0.2rem;
}

/* Primary Button Custom Color */
div.stButton > button[kind="primary"] {
    background-color: #4f46e5 !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
}
div.stButton > button[kind="primary"]:hover {
    background-color: #4338ca !important;
    color: white !important;
    box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3) !important;
}
</style>
""", unsafe_allow_html=True)

# Main Title Header
st.markdown("""
<div class="dashboard-header">
    <h1>💼 AI-Powered Recruiter Dashboard</h1>
    <p>Rank resumes semantically against job descriptions in seconds</p>
</div>
""", unsafe_allow_html=True)

# Config setup
config = load_config()

# Sidebar variables
with st.sidebar:
    st.markdown("### ⚙️ Engine Configurations")
    model_override = st.selectbox(
        "Semantic Model",
        ["all-MiniLM-L6-v2"],
        help="Target pre-trained Hugging Face embedding model"
    )
    
    st.info("The screening pipeline applies local vector embeddings (60%), skills matching (20%), work experience (10%), and education verification (10%).")
    
    st.markdown("---")
    st.markdown("#### 📂 Active Paths")
    st.text(f"Output folder: {config.output_dir}")
    st.text(f"Sample data folder: {config.sample_data_dir}")

# Upload Panels
col1, col2 = st.columns([2, 3])

with col1:
    st.markdown("### 📝 1. Job Description Ingestion")
    uploaded_jd = st.file_uploader(
        "Upload Job Description File (.txt)",
        type=["txt"],
        help="Upload the raw target job requirements document"
    )
    
    # Read JD contents if uploaded, otherwise fallback to default sample data JD
    jd_content = ""
    if uploaded_jd:
        jd_content = uploaded_jd.read().decode("utf-8")
        st.success(f"Custom Job Description '{uploaded_jd.name}' uploaded successfully.")
        with st.expander("Preview JD Text"):
            st.text(jd_content)
    else:
        default_jd_path = config.sample_data_dir / "job_description.txt"
        if default_jd_path.exists():
            with open(default_jd_path, "r", encoding="utf-8") as f:
                jd_content = f.read()
            st.caption("Using default job description sample data.")
            with st.expander("Preview Default JD"):
                st.text(jd_content)
        else:
            st.warning("Please upload a Job Description file.")

with col2:
    st.markdown("### 📂 2. Resumes Ingestion")
    uploaded_resumes = st.file_uploader(
        "Upload Resumes (.pdf, .docx, .txt)",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        help="Upload one or more candidate resumes to evaluate"
    )
    if uploaded_resumes:
        st.success(f"{len(uploaded_resumes)} resumes loaded to batch parser.")

# Action trigger
if st.button("🚀 Screen Candidates", use_container_width=True, type="primary"):
    if not jd_content:
        st.error("Please upload or ensure a job description exists before screening.")
    elif not uploaded_resumes:
        st.error("Please upload at least one candidate resume.")
    else:
        with st.spinner("Processing batch pipeline (Parsing, Extracting, Vectorizing)..."):
            # 1. Setup temporary directories inside workspace
            temp_resumes_dir = Path("temp_resumes")
            if temp_resumes_dir.exists():
                shutil.rmtree(temp_resumes_dir)
            temp_resumes_dir.mkdir(parents=True, exist_ok=True)
            
            # Save uploaded resumes to temp folder
            for resume in uploaded_resumes:
                save_path = temp_resumes_dir / resume.name
                with open(save_path, "wb") as f:
                    f.write(resume.getbuffer())
            
            try:
                # 2. Extract job description requirements
                job_reqs = extract_job_requirements(
                    job_description_text=jd_content,
                    model_name=config.gemini_model,
                    api_key=config.gemini_api_key
                )
                job_reqs["raw_text"] = jd_content
                
                # 3. Batch load and parse resumes
                resumes_data = load_all_resumes(temp_resumes_dir)
                
                if not resumes_data:
                    st.error("No resumes could be parsed successfully. Check for file corruption.")
                else:
                    # 4. Orchestrate evaluation loop
                    evaluations = []
                    for filename, raw_text in resumes_data.items():
                        evaluation = process_resume(filename, raw_text, job_reqs, config)
                        evaluations.append(evaluation)
                        
                    # 5. Rank and Sort
                    ranked_evaluations = sorted(evaluations, key=lambda x: x["final_score"], reverse=True)
                    
                    # 6. Save outputs to output folder
                    json_output_path = config.output_dir / "ranking.json"
                    csv_output_path = config.output_dir / "ranking.csv"
                    
                    save_json_file(ranked_evaluations, json_output_path)
                    
                    csv_rows = []
                    for rank, res in enumerate(ranked_evaluations, start=1):
                        reasoning_str = "; ".join(res.get("reasoning", []))
                        csv_rows.append({
                            "Rank": rank,
                            "Candidate": res.get("candidate_name", "Unknown"),
                            "Score": f"{res.get('final_score', 0.0):.2f}%",
                            "Similarity": f"{res.get('breakdown', {}).get('semantic_match', 0.0):.2f}%",
                            "Reason": reasoning_str
                        })
                    csv_headers = ["Rank", "Candidate", "Score", "Similarity", "Reason"]
                    save_csv_file(csv_rows, csv_output_path, csv_headers)
                    
                    # Keep rankings in Streamlit session state
                    st.session_state["results"] = ranked_evaluations
                    st.success(f"🎉 Screening complete. {len(ranked_evaluations)} candidates evaluated successfully! Reports generated.")
                    
            except Exception as e:
                st.error(f"Failed to run screening pipeline: {e}")
                st.exception(e)
            finally:
                # Clean up temporary directory
                if temp_resumes_dir.exists():
                    shutil.rmtree(temp_resumes_dir)

# Render results if they exist in state
if "results" in st.session_state and st.session_state["results"]:
    results = st.session_state["results"]
    
    st.markdown("---")
    st.markdown("## 📊 Screening Results & Insights")
    
    # Metrics Cards Row
    top_candidate = results[0]
    total_candidates = len(results)
    avg_score = sum(r["final_score"] for r in results) / total_candidates
    
    st.markdown(f"""<div class="metric-container">
<div class="metric-box">
<div class="metric-number">{total_candidates}</div>
<div class="metric-label">Total Evaluated</div>
</div>
<div class="metric-box">
<div class="metric-number">{top_candidate['final_score']:.1f}%</div>
<div class="metric-label">Top Score Match</div>
</div>
<div class="metric-box">
<div class="metric-number">{avg_score:.1f}%</div>
<div class="metric-label">Average Pool Match</div>
</div>
</div>""", unsafe_allow_html=True)
    
    # Featured Top Candidate Card
    top_reasoning_str = " • ".join(top_candidate.get("reasoning", []))
    st.markdown(f"""<div class="top-match-card">
<span class="top-match-badge">⭐ Top Match Recommendation</span>
<h2 style="color: #1e3a8a; margin: 0 0 0.5rem 0;">{top_candidate['candidate_name']}</h2>
<p style="font-size: 1.1rem; color: #1e293b; margin: 0 0 1rem 0;">
<strong>Email:</strong> {top_candidate.get('email', 'N/A')} | 
<strong>Total Match Score:</strong> {top_candidate['final_score']}% | 
<strong>Semantic Similarity:</strong> {top_candidate['breakdown']['semantic_match']}%
</p>
<div style="background-color: white; padding: 1rem; border-radius: 8px; border: 1px solid #c7d2fe;">
<strong>Highlights & Reasoning:</strong><br/>
<span style="color: #4f46e5; font-size: 0.95rem;">{top_reasoning_str}</span>
</div>
</div>""", unsafe_allow_html=True)
    
    # Leaderboard Table and Detailed Inspector columns
    col_table, col_inspect = st.columns([3, 2])
    
    with col_table:
        st.markdown("### 🏆 Leaderboard Rankings")
        
        # Build pandas DataFrame for sortable Streamlit view
        table_data = []
        for rank, res in enumerate(results, start=1):
            table_data.append({
                "Rank": rank,
                "Candidate": res.get("candidate_name", "Unknown"),
                "Score (%)": res.get("final_score", 0.0),
                "Semantic Similarity (%)": res.get("breakdown", {}).get("semantic_match", 0.0),
                "Skills Match (%)": res.get("breakdown", {}).get("skills_match", 0.0),
                "Email": res.get("email", "N/A")
            })
        df = pd.DataFrame(table_data)
        
        st.dataframe(
            df.set_index("Rank"),
            use_container_width=True,
            column_config={
                "Score (%)": st.column_config.NumberColumn(format="%.2f%%"),
                "Semantic Similarity (%)": st.column_config.NumberColumn(format="%.2f%%"),
                "Skills Match (%)": st.column_config.NumberColumn(format="%.2f%%")
            }
        )
        
        # Export Actions
        st.markdown("#### 💾 Export Report Reports")
        col_csv, col_json = st.columns(2)
        
        # Read CSV/JSON file outputs to construct downloads
        csv_file_path = config.output_dir / "ranking.csv"
        json_file_path = config.output_dir / "ranking.json"
        
        if csv_file_path.exists():
            with open(csv_file_path, "r", encoding="utf-8") as f:
                csv_data = f.read()
            col_csv.download_button(
                label="📥 Download ranking.csv",
                data=csv_data,
                file_name="ranking.csv",
                mime="text/csv",
                use_container_width=True
            )
            
        if json_file_path.exists():
            with open(json_file_path, "r", encoding="utf-8") as f:
                json_data = f.read()
            col_json.download_button(
                label="📥 Download ranking.json",
                data=json_data,
                file_name="ranking.json",
                mime="application/json",
                use_container_width=True
            )
            
    with col_inspect:
        st.markdown("### 🔍 Candidate Profile Inspector")
        selected_name = st.selectbox(
            "Select Candidate Profile to Inspect",
            options=[res["candidate_name"] for res in results]
        )
        
        # Find selected candidate evaluation dictionary
        candidate = next(res for res in results if res["candidate_name"] == selected_name)
        
        st.markdown(f"""<div class="card">
<h3 style="margin-top: 0; color: #4f46e5; margin-bottom: 0.5rem;">{candidate['candidate_name']}</h3>
<p style="margin: 0 0 1rem 0;"><strong>Email:</strong> {candidate.get('email', 'N/A')}</p>
<hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 1rem 0;"/>
<strong>Score Breakdown:</strong>
<ul style="padding-left: 1.2rem; margin-top: 0.5rem; margin-bottom: 1rem;">
<li><strong>Semantic Match (60% weight):</strong> {candidate['breakdown']['semantic_match']}%</li>
<li><strong>Skills Match (20% weight):</strong> {candidate['breakdown']['skills_match']}%</li>
<li><strong>Experience Match (10% weight):</strong> {candidate['breakdown']['experience_match']}%</li>
<li><strong>Education Match (10% weight):</strong> {candidate['breakdown']['education_match']}%</li>
</ul>
<strong>Evaluation Highlights & Reasoning:</strong>
<ul style="padding-left: 1.2rem; margin-top: 0.5rem; color: #334155;">
{"".join(f"<li>{bullet}</li>" for bullet in candidate.get('reasoning', []))}
</ul>
</div>""", unsafe_allow_html=True)
