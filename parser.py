import re
import logging
from pathlib import Path
from typing import Dict

import pdfplumber
import docx

logger = logging.getLogger(__name__)

def clean_whitespace(text: str) -> str:
    """
    Cleans up extra whitespaces, including replacing multiple consecutive 
    spaces or newlines with a single space or newline, and stripping edges.
    
    Args:
        text (str): Raw input text.
        
    Returns:
        str: Normalized clean text.
    """
    if not text:
        return ""
    # Normalize unicode spaces and non-breaking spaces
    text = text.replace("\xa0", " ")
    # Replace multiple spaces/tabs with a single space
    text = re.sub(r"[ \t]+", " ", text)
    # Remove spaces/tabs at the beginning and end of lines
    text = re.sub(r"[ \t]*\n[ \t]*", "\n", text)
    # Replace three or more newlines with two newlines (to preserve paragraph breaks)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def parse_pdf(file_path: Path) -> str:
    """
    Parses and extracts text from a PDF file using pdfplumber.
    
    Args:
        file_path (Path): Path to the target PDF file.
        
    Returns:
        str: Extracted raw text content, or empty string on failure.
    """
    logger.info("Parsing PDF file: %s", file_path)
    text_content = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_content.append(page_text)
    except Exception as e:
        logger.error("Failed to parse PDF file at %s: %s", file_path, e, exc_info=True)
        return ""
        
    return "\n".join(text_content)

def parse_docx(file_path: Path) -> str:
    """
    Parses and extracts text from a Word DOCX file using python-docx.
    
    Args:
        file_path (Path): Path to the target DOCX file.
        
    Returns:
        str: Extracted raw text content, or empty string on failure.
    """
    logger.info("Parsing Word DOCX file: %s", file_path)
    try:
        doc = docx.Document(file_path)
        text_content = [paragraph.text for paragraph in doc.paragraphs if paragraph.text]
        return "\n".join(text_content)
    except Exception as e:
        logger.error("Failed to parse DOCX file at %s: %s", file_path, e, exc_info=True)
        return ""

def load_resume(path: str | Path) -> str:
    """
    Loads and cleans text content from a resume file (PDF, DOCX, or TXT).
    
    Args:
        path (str | Path): Path to the target resume file.
        
    Returns:
        str: Extracted and cleaned text content. Returns empty string if parsing fails.
    """
    file_path = Path(path)
    if not file_path.exists():
        logger.error("Resume file does not exist at path: %s", file_path)
        return ""
        
    suffix = file_path.suffix.lower()
    raw_text = ""
    
    try:
        if suffix == ".pdf":
            raw_text = parse_pdf(file_path)
        elif suffix in (".docx", ".doc"):
            raw_text = parse_docx(file_path)
        elif suffix == ".txt":
            logger.info("Reading plain text file: %s", file_path)
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                raw_text = f.read()
        else:
            logger.warning("Unsupported file type: %s for file: %s", suffix, file_path.name)
            return ""
    except Exception as e:
        logger.error("Error occurred while loading resume %s: %s", file_path, e, exc_info=True)
        return ""
        
    return clean_whitespace(raw_text)

def load_all_resumes(folder: str | Path) -> Dict[str, str]:
    """
    Loads all resumes of supported formats from the specified folder.
    
    Args:
        folder (str | Path): Path to the directory containing resumes.
        
    Returns:
        Dict[str, str]: Dictionary mapping file names to cleaned text content.
    """
    folder_path = Path(folder)
    resumes_data: Dict[str, str] = {}
    
    if not folder_path.is_dir():
        logger.error("Provided path is not a directory: %s", folder_path)
        return resumes_data
        
    supported_extensions = ("*.pdf", "*.docx", "*.doc", "*.txt")
    resume_files = []
    for ext in supported_extensions:
        resume_files.extend(folder_path.glob(ext))
        
    logger.info("Found %d potential resume files in %s", len(resume_files), folder_path)
    
    for file_path in resume_files:
        # Skip temp / hidden files
        if file_path.name.startswith("~") or file_path.name.startswith("."):
            continue
        try:
            cleaned_text = load_resume(file_path)
            if cleaned_text:
                resumes_data[file_path.name] = cleaned_text
            else:
                logger.warning("No content extracted from resume: %s", file_path.name)
        except Exception as e:
            logger.error("Failed to load resume %s in batch: %s", file_path.name, e, exc_info=True)
            
    return resumes_data
