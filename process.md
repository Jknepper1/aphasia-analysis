# Aphasia Analysis Pipeline Process Documentation

## Overview

This documentation describes how the data moves through the `aphasia-analysis` pipeline, including the key folders, transcript sources, and Python scripts involved.

The pipeline is designed to:
1. Read plain-text transcript sentences from `src/transcripts/`
2. Generate normal speech audio using OpenAI TTS via `tts.py`
3. Convert normal speech audio into simulated aphasia audio using OpenAI Realtime via `normal_to_aphasia.py`
4. Transcribe the generated aphasia audio into CLAN-format `.cha` transcripts using BatchAlign via `batchalign_manual.py`

## Project Structure Context

### Top-level workspace folders

The broader workspace contains several data folders and archives, including:
- `aphasia/` — a large dataset of aphasia files and subfolders used for research. This is outside the `aphasia-analysis` pipeline and appears to contain a variety of existing TalkBank / CLAN corpora.
- `cinderella/` — likely story-task data sets for aphasia and control participants.
- `sandwich/` — likely sandwich-task data sets for aphasia and control participants.
- `talkbank_full_HC/` — a full, original TalkBank Healthy Control corpus.
- `talkbank_sorted_flo_HC/` and `talkbank_sorted_HC/` — sorted TalkBank subsets.
- `graphs/` and `naming_conventions.txt` — supporting analysis materials.

### `aphasia-analysis/` folder

The pipeline lives in the `aphasia-analysis` folder. Its important subfolders are:

- `src/prompts/` — contains prompt templates that instruct the OpenAI Realtime model how to simulate different aphasia profiles.
- `src/transcripts/` — contains transcript folders with plain `.txt` sentence lists used as input to TTS.
- `normal/` — output folder for generated normal-speech `.wav` files.
- `aphasia/` — output folder for aphasia-simulated `.wav` files.
- `final/` — output folder for BatchAlign-produced `.cha` transcripts.
- `helpers/` — utility scripts used for auxiliary processing or data management.

## Transcript Source Structure

The input transcript data is organized as directories inside `src/transcripts/`.
Each directory represents a transcript set or condition.

The folders under `src/transcripts/` include:
- `ano_cinderella/`
- `ano_sandwich/`
- `broca_cinderella/`
- `broca_sandwich/`
- `cont_cinderella/`
- `cont_sandwich/`
- `wern_cinderella/`
- `wern_sandwich/`

Each of these folders contains plain `.txt` documents. The `tts.py` script reads each `.txt` file, treats its lines as sentences, requests TTS audio for each line, and concatenates the results into a single `.wav` file.

## Key Python Scripts

### `main.py`

This is the pipeline entry point.

It performs these tasks:
- Creates and validates the `normal/`, `aphasia/`, and `final/` directories.
- Prompts the user to select:
  - a prompt file from `src/prompts/`
  - a transcript directory from `src/transcripts/`
  - target output subfolders inside `normal/`, `aphasia/`, and `final/`
- Depending on the selected start point, the pipeline runs:
  - `generate_normal_audio()` to create normal audio from transcripts
  - `generate_aphasia_audio()` to simulate aphasia audio from normal audio
  - `transcribe_morphotag()` to create CLAN transcripts from aphasia audio

The start-point options are:
- `0` — run the full pipeline from normal TTS through aphasia simulation and transcription
- `1` — start at speech-to-speech aphasia simulation
- `2` — run only the BatchAlign transcription stage

### `tts.py`

This script converts text transcripts into normal speech audio.

How it works:
- Reads all `.txt` files from a selected `src/transcripts/<folder>/`
- For each file:
  - reads lines of plain text
  - requests OpenAI TTS using `gpt-4o-mini-tts` and the voice `marin`
  - appends each response's PCM audio to a combined buffer
  - writes the combined buffer to `normal/<target_folder>/<basename>.wav`

Important details:
- Output sample rate is set to 24 kHz
- The audio is mono, 16-bit
- There is a small delay between requests to avoid rate limiting
- The generated normal-audio files are stored in the user-selected `normal/` subfolder

### `normal_to_aphasia.py`

This script transforms the generated normal speech into simulated aphasia speech.

How it works:
- Reads `.wav` files from a selected `normal/<folder>/`
- Opens a fresh WebSocket session to OpenAI Realtime for each file
- Sends the prompt instructions loaded from `src/prompts/<filename>`
- Sends the original normal speech as `input_audio`
- Requests a Realtime response, capturing streamed `response.output_audio.delta` chunks
- Writes the received audio back to `aphasia/<target_folder>/<same_basename>.wav`

Important details:
- Every file gets a new WebSocket session to avoid shared context
- The model URL is `wss://api.openai.com/v1/realtime?model=gpt-realtime-mini-2025-12-15`
- Output audio is written as a 24 kHz, mono, 16-bit WAV file
- This creates the simulated aphasia audio dataset used for transcription

### `batchalign_manual.py`

This script runs BatchAlign to transcribe generated aphasia audio into CLAN-like transcript files.

How it works:
- Instantiates BatchAlign pipeline objects:
  - `RevEngine` for ASR transcription
  - `StanzaEngine` for morphosyntax tagging
  - `BatchalignPipeline` combining them
- Reads `.wav` files from a selected `aphasia/<folder>/`
- For each audio file:
  - creates a `ba.Document` from the audio
  - runs the ASR + morph pipeline
  - converts the result into a `ba.CHATFile`
  - writes the transcript as `final/<target_folder>/<basename>.cha`

Important details:
- The output filenames mirror the input audio filenames
- This stage produces CLAN-compatible transcripts ready for further analysis
- The script is intended to be run after the aphasia audio generation step

## Folder Roles in the Pipeline

### `src/prompts/`

Contains prompt text files that define the aphasia simulation behavior. Example prompt files:
- `broca_language_3-1.txt`
- `broca_language_translation.txt`
- `broca_zero_shot.txt`
- `wernicke_very_severe.txt`

These files are loaded by `main.py` and passed into `generate_aphasia_audio()`.

### `src/transcripts/`

Contains folders of raw text transcript sources.
Each `.txt` file in these folders is converted into one normal audio `.wav` file.

Example transcript folders:
- `ano_cinderella/`
- `ano_sandwich/`
- `broca_cinderella/`
- `broca_sandwich/`
- `cont_cinderella/`
- `cont_sandwich/`
- `wern_cinderella/`
- `wern_sandwich/`

### `normal/`

Holds generated normal speech audio.
This is the intermediate output from `tts.py`.
The files are used as input to the aphasia simulation stage.

### `aphasia/`

Holds converted aphasia simulation audio.
This is the intermediate output from `normal_to_aphasia.py`.
The files are used as input to BatchAlign transcription.

### `final/`

Holds the final CLAN-format transcripts produced by BatchAlign.
Generated files are written as `.cha` and are suitable for further CLAN/EVAL analysis.

## Typical Pipeline Execution

1. Prepare the transcript source directory under `src/transcripts/`.
2. Choose a prompt file from `src/prompts/`.
3. Run `python main.py`.
4. In the interactive prompts:
   - select the start point (`0`, `1`, or `2`)
   - select the transcript folder
   - select the output subfolder names for `normal/`, `aphasia/`, and `final/`
5. If starting at point `0`:
   - `tts.py` generates normal audio into `normal/<subfolder>/`
   - `normal_to_aphasia.py` generates aphasia audio into `aphasia/<subfolder>/`
   - `batchalign_manual.py` transcribes aphasia audio into `final/<subfolder>/`
6. After `final/` transcripts are generated, use CLAN / BatchAlign evaluation tools externally to compute analysis metrics.

## Additional Notes

- The pipeline assumes that transcript files are plain `.txt` files and that audio input files are `.wav`.
- `main.py` deliberately avoids reusing open WebSocket sessions for multiple files.
- The `final/` directory is intended for CLAN-output transcripts, not raw audio.
- BatchAlign may require its own external setup and credentials separate from OpenAI.

## External Data and Research Context

Outside `aphasia-analysis`, the workspace contains research corpora and TalkBank resources, such as:
- `aphasia/`
- `cinderella/`
- `sandwich/`
- `talkbank_full_HC/`
- `talkbank_sorted_flo_HC/`
- `talkbank_sorted_HC/`