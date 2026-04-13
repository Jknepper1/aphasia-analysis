import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI

from batchalign_manual import transcribe_morphotag
from normal_to_aphasia import generate_aphasia_audio
from tts import generate_normal_audio
from helpers.pipeline_utils import (
    ValidationError,
    clean_directory,
    load_json_config,
    read_prompt,
    resolve_output_folder,
    resolve_prompt_path,
    resolve_transcript_path,
    validate_transcript_folder,
)

logger = logging.getLogger(__name__)


def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Aphasia analysis pipeline runner."
    )
    parser.add_argument("--config", type=str, help="Optional JSON config file.")
    parser.add_argument("--prompt-file", type=str, help="Prompt file path or name under src/prompts/")
    parser.add_argument("--transcript-folder", type=str, help="Transcript folder path or name under src/transcripts/")
    parser.add_argument("--normal-folder", type=str, help="Name of target folder under normal/")
    parser.add_argument("--aphasia-folder", type=str, help="Name of target folder under aphasia/")
    parser.add_argument("--final-folder", type=str, help="Name of target folder under final/")
    parser.add_argument(
        "--start-point",
        choices=["0", "1", "2", "3"],
        default="0",
        help="Pipeline start point: 0=tts->aphasia->transcribe, 1=aphasia->transcribe, 2=transcribe only, 3=tts->transcribe (skip aphasia)",
    )
    parser.add_argument(
        "--clean-output",
        action="store_true",
        help="Remove existing files in selected output folders before running.",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate configuration and inputs without running the pipeline.",
    )
    return parser.parse_args(argv)


def load_config(config_path):
    if not config_path:
        return {}

    config = load_json_config(config_path)
    if not isinstance(config, dict):
        raise ValidationError("Config file must contain a JSON object.")
    return config


def merge_config(args):
    config = load_config(args.config)
    option_keys = [
        "prompt_file",
        "transcript_folder",
        "normal_folder",
        "aphasia_folder",
        "final_folder",
        "start_point",
        "clean_output",
        "validate_only",
    ]

    for key in option_keys:
        value = getattr(args, key)
        if value is not None:
            config[key] = value

    return config


def resolve_paths(config):
    start_point = str(config.get("start_point", "0"))
    if start_point not in {"0", "1", "2", "3"}:
        raise ValidationError("start_point must be one of 0, 1, 2, or 3")

    paths = {
        "prompt_file": None,
        "transcript_folder": None,
        "normal_folder": None,
        "aphasia_folder": None,
        "final_folder": None,
        "start_point": start_point,
    }

    if start_point in {"0", "3"}:
        transcript_folder = config.get("transcript_folder")
        if not transcript_folder:
            raise ValidationError("transcript-folder is required for start-point 0 or 3")
        paths["transcript_folder"] = resolve_transcript_path(transcript_folder)

    if start_point in {"0", "1"}:
        prompt_file = config.get("prompt_file")
        if not prompt_file:
            raise ValidationError("prompt-file is required for start-point 0 or 1")
        paths["prompt_file"] = resolve_prompt_path(prompt_file)

    if start_point in {"0", "1", "3"}:
        paths["normal_folder"] = resolve_output_folder("normal", config.get("normal_folder"))

    if start_point in {"0", "1", "2"}:
        paths["aphasia_folder"] = resolve_output_folder("aphasia", config.get("aphasia_folder"))
        paths["final_folder"] = resolve_output_folder("final", config.get("final_folder"))

    if start_point == "3":
        paths["final_folder"] = resolve_output_folder("final", config.get("final_folder"))

    return paths


def clean_directories(paths):
    if paths["start_point"] == "0":
        clean_directory(paths["normal_folder"])
        clean_directory(paths["aphasia_folder"])
        clean_directory(paths["final_folder"])
    elif paths["start_point"] == "1":
        clean_directory(paths["aphasia_folder"])
        clean_directory(paths["final_folder"])
    elif paths["start_point"] == "2":
        clean_directory(paths["final_folder"])
    elif paths["start_point"] == "3":
        clean_directory(paths["normal_folder"])
        clean_directory(paths["final_folder"])


def interactive_setup():
    logger.info("Entering interactive setup mode.")

    while True:
        start_point = input("Where would you like to start? [0: Beginning, 1: NormalToAphasia, 2: Transcription]\n").strip()
        if start_point in {"0", "1", "2"}:
            break
        print("Please select 0, 1, or 2.")

    prompt_path = None
    if start_point in {"0", "1"}:
        while True:
            prompt_input = input("Input the name of your aphasia prompt in /src/prompts/: ").strip()
            try:
                prompt_path = resolve_prompt_path(prompt_input)
                read_prompt(prompt_path)
                break
            except (FileNotFoundError, ValidationError) as exc:
                print(str(exc))

    transcripts_dir = None
    if start_point == "0":
        while True:
            transcript_input = input("Input a set of transcripts from /src/transcripts/: ").strip()
            try:
                transcripts_dir = resolve_transcript_path(transcript_input)
                validate_transcript_folder(transcripts_dir)
                break
            except (FileNotFoundError, ValidationError) as exc:
                print(str(exc))

    normal_folder = None
    if start_point in {"0", "1"}:
        while True:
            normal_input = input("Input the name of your normal audio directory in /normal/: ").strip()
            if normal_input:
                normal_folder = resolve_output_folder("normal", normal_input)
                break
            print("Please enter a normal audio folder name.")

    aphasia_folder = None
    if start_point in {"0", "1", "2"}:
        while True:
            aphasia_input = input("Input the name of your aphasia audio directory in /aphasia/: ").strip()
            if aphasia_input:
                aphasia_folder = resolve_output_folder("aphasia", aphasia_input)
                break
            print("Please enter an aphasia audio folder name.")

    final_folder = None
    while True:
        final_input = input("Input the name of your batchalign transcript directory in /final/: ").strip()
        if final_input:
            final_folder = resolve_output_folder("final", final_input)
            break
        print("Please enter an output folder name under /final/.")

    clean_output = False
    answer = input("Clean selected output folders before running? [y/N]: ").strip().lower()
    clean_output = answer == "y"

    return {
        "prompt_file": prompt_path,
        "transcript_folder": transcripts_dir,
        "normal_folder": str(normal_folder) if normal_folder else None,
        "aphasia_folder": str(aphasia_folder) if aphasia_folder else None,
        "final_folder": str(final_folder) if final_folder else None,
        "start_point": start_point,
        "clean_output": clean_output,
        "validate_only": False,
    }


async def main():
    configure_logging()
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

    args = parse_args()
    if args.config or any([args.prompt_file, args.transcript_folder, args.normal_folder, args.aphasia_folder, args.final_folder, args.clean_output, args.validate_only]):
        config = merge_config(args)
    else:
        config = interactive_setup()

    try:
        paths = resolve_paths(config)
    except ValidationError as exc:
        logger.error("Configuration validation failed: %s", exc)
        sys.exit(1)

    if config.get("clean_output"):
        clean_directories(paths)

    if config.get("validate_only"):
        logger.info("Validation-only check completed successfully.")
        return

    if api_key is None:
        logger.error("OPENAI_API_KEY is not set. Set it in .env or environment variables.")
        sys.exit(1)

    client = AsyncOpenAI(api_key=api_key)

    start_point = paths["start_point"]
    prompt = None
    if start_point in {"0", "1"}:
        try:
            prompt = read_prompt(paths["prompt_file"])
        except ValidationError as exc:
            logger.error("Invalid prompt file: %s", exc)
            sys.exit(1)

    if start_point == "0":
        logger.info("Starting TTS stage.")
        await generate_normal_audio(paths["transcript_folder"], client, str(paths["normal_folder"]))
        logger.info("Completed TTS stage.")

    if start_point in {"0", "1"}:
        logger.info("Starting aphasia simulation stage.")
        await generate_aphasia_audio(prompt, api_key, str(paths["normal_folder"]), str(paths["aphasia_folder"]))
        logger.info("Completed aphasia simulation stage.")

    if start_point in {"0", "1", "2"}:
        logger.info("Starting BatchAlign transcription stage.")
        transcribe_morphotag(str(paths["aphasia_folder"]), str(paths["final_folder"]))
        logger.info("Completed BatchAlign transcription stage.")

    if start_point == "3":
        logger.info("Starting TTS stage.")
        await generate_normal_audio(paths["transcript_folder"], client, str(paths["normal_folder"]))
        logger.info("Completed TTS stage.")
        logger.info("Starting BatchAlign transcription stage on normal audio.")
        transcribe_morphotag(str(paths["normal_folder"]), str(paths["final_folder"]))
        logger.info("Completed BatchAlign transcription stage.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Pipeline interrupted by user.")
        sys.exit(1)
