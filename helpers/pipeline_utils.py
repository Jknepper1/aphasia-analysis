import json
import logging
import os
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    pass


def ensure_directory(path):
    os.makedirs(path, exist_ok=True)
    logger.debug("Ensured directory exists: %s", path)
    return path


def clean_directory(path):
    if not os.path.isdir(path):
        return

    for entry in os.listdir(path):
        full_path = os.path.join(path, entry)
        if os.path.isdir(full_path):
            shutil.rmtree(full_path)
            logger.debug("Removed directory: %s", full_path)
        else:
            os.remove(full_path)
            logger.debug("Removed file: %s", full_path)

    logger.info("Cleaned directory: %s", path)


def load_json_config(config_path):
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    text = config_file.read_text(encoding="utf-8")
    return json.loads(text)


def resolve_prompt_path(prompt_file):
    prompt_path = Path(prompt_file)
    if not prompt_path.is_absolute():
        candidate = Path("src") / "prompts" / prompt_file
        if candidate.exists():
            prompt_path = candidate
        else:
            prompt_path = Path(prompt_file)

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    return str(prompt_path.resolve())


def resolve_transcript_path(transcript_folder):
    transcript_path = Path(transcript_folder)
    if not transcript_path.is_absolute():
        candidate = Path("src") / "transcripts" / transcript_folder
        if candidate.exists():
            transcript_path = candidate
        else:
            transcript_path = Path(transcript_folder)

    if not transcript_path.exists() or not transcript_path.is_dir():
        raise FileNotFoundError(f"Transcript directory not found: {transcript_path}")
    return str(transcript_path.resolve())


def read_prompt(prompt_path):
    with open(prompt_path, "r", encoding="utf-8") as file:
        prompt = file.read().strip()

    if not prompt:
        raise ValidationError(f"Prompt file is empty: {prompt_path}")
    return prompt


def validate_transcript_folder(transcript_dir):
    path = Path(transcript_dir)
    if not path.exists() or not path.is_dir():
        raise ValidationError(f"Transcript directory not found: {transcript_dir}")

    txt_files = [entry for entry in sorted(path.iterdir()) if entry.is_file() and entry.suffix.lower() == ".txt"]
    if not txt_files:
        raise ValidationError(f"No .txt files found in transcript folder: {transcript_dir}")

    empty_files = [str(entry) for entry in txt_files if entry.stat().st_size == 0]
    if empty_files:
        raise ValidationError(f"Empty transcript files found: {empty_files}")

    return txt_files


def resolve_output_folder(root_folder, folder_name):
    if not folder_name:
        raise ValidationError("Output folder name is required")

    folder_path = Path(folder_name)
    if not folder_path.is_absolute():
        folder_path = Path(root_folder) / folder_name

    ensure_directory(folder_path)
    return folder_path.resolve()


def validate_output_folder(path):
    ensure_directory(path)
    return Path(path).resolve()
