import json
import logging
import sys
from pathlib import Path
from typing import Any

def setup_logging(level: str = "INFO") -> None:
    """
    Initializes a standardized application logging configuration.
    
    Args:
        level (str): The string representing the minimum logging level.
    """
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO

    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Logging configured at level %s", level)

def read_text_file(file_path: Path) -> str:
    """
    Utility function to safely read contents of a text file.
    
    Args:
        file_path (Path): Path to the target text file.
        
    Returns:
        str: Content of the text file.
    """
    logger = logging.getLogger(__name__)
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        logger.debug("Successfully read file at %s", file_path)
        return content
    except Exception as e:
        logger.error("Failed to read file at %s: %s", file_path, e)
        raise e

def save_json_file(data: Any, file_path: Path) -> None:
    """
    Utility function to safely save data structure as formatted JSON.
    
    Args:
        data (Any): Python data structure to serialize.
        file_path (Path): Target save location.
    """
    logger = logging.getLogger(__name__)
    try:
        # Automatically create the parent directory if it does not exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.debug("Successfully wrote JSON to %s", file_path)
    except Exception as e:
        logger.error("Failed to write JSON to %s: %s", file_path, e)
        raise e

def save_csv_file(data: list[dict[str, Any]], file_path: Path, headers: list[str]) -> None:
    """
    Utility function to safely save list of dictionary rows as a CSV file.
    
    Args:
        data (list[dict[str, Any]]): List of dictionaries representing table rows.
        file_path (Path): Target save location.
        headers (list[str]): List of header strings.
    """
    import csv
    logger = logging.getLogger(__name__)
    try:
        # Automatically create the parent directory if it does not exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for row in data:
                writer.writerow(row)
        logger.debug("Successfully wrote CSV to %s", file_path)
    except Exception as e:
        logger.error("Failed to write CSV to %s: %s", file_path, e)
        raise e

