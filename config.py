import os
import logging
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

@dataclass
class AppConfig:
    """
    Data class representing the application configuration settings.
    """
    gemini_api_key: str
    gemini_model: str
    log_level: str
    output_dir: Path
    sample_data_dir: Path

def load_config() -> AppConfig:
    """
    Loads and validates the configuration from environment variables.
    
    Returns:
        AppConfig: An instance of AppConfig containing configuration settings.
    """
    load_dotenv()
    
    # Retrieve and process environment configurations
    gemini_api_key = os.getenv("GEMINI_API_KEY", "")
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    output_path = Path(os.getenv("OUTPUT_DIR", "output"))
    sample_data_path = Path(os.getenv("SAMPLE_DATA_DIR", "sample_data"))
    
    # Ensure necessary directory structures exist
    if not output_path.exists():
        output_path.mkdir(parents=True, exist_ok=True)
        
    config = AppConfig(
        gemini_api_key=gemini_api_key,
        gemini_model=gemini_model,
        log_level=log_level,
        output_dir=output_path,
        sample_data_dir=sample_data_path
    )
    
    logger.debug("Application configuration successfully initialized.")
    return config
