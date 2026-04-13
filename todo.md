# Project Improvement Plan

## Role: Project Manager

This document describes the next improvements I would plan for the `aphasia-analysis` project based on the current codebase and structure. It does not change the code. It only defines priorities, rationale, and implementation steps.

## High-Level Priorities

1. Stabilize and standardize the pipeline interface
2. Improve reliability, observability, and recoverability
3. Separate configuration from logic
4. Add lightweight validation and quality controls
5. Prepare the project for easier research and collaboration

## Recommended Improvements

### 1. Replace interactive CLI flow with explicit configuration

**Why:** The current `main.py` relies on repeated `input()` prompts, which is fragile and hard to automate.

**What to do:**
- Add a single CLI entrypoint using `argparse` or `typer`
- Support flags for:
  - `--prompt-file`
  - `--transcript-folder`
  - `--normal-folder`
  - `--aphasia-folder`
  - `--final-folder`
  - `--start-point` (`0`, `1`, `2`)
- Add a config file option such as `--config config.yml`

**How to implement:**
1. Refactor `main.py` to separate `setup()` from user interaction.
2. Add an argument parser at the top-level.
3. Preserve the existing interactive fallback only for manual runs.
4. Document the new command usage in `README.md` and `process.md`.

### 2. Make folder creation and cleanup deterministic

**Why:** Directory setup is partly handled manually and can leave stale files in `normal/`, `aphasia/`, or `final/`.

**What to do:**
- Add robust directory creation logic with clear behavior:
  - create missing directories automatically
  - optionally clean existing directories if requested
  - preserve existing data unless explicitly asked to overwrite
- Remove the `ERROR: ... would you like to wipe files?` prompt in favor of explicit flags like `--clean` or `--overwrite`

**How to implement:**
1. Add helper functions for `ensure_directory()` and `clean_directory()`.
2. Use a configuration mode such as `--reset-output`.
3. Log directory state decisions clearly.

### 3. Add structured logging and progress reporting

**Why:** The current `print()` output is useful but hard to parse consistently.

**What to do:**
- Replace raw prints with Python `logging`
- Use info/debug/error levels
- Add per-file progress logs and summary metrics
- Consider JSON log export for later analysis

**How to implement:**
1. Add `logging.basicConfig()` in `main.py`
2. Update `tts.py`, `normal_to_aphasia.py`, and `batchalign_manual.py` to use `logger = logging.getLogger(__name__)`
3. Add a final summary in `main.py` after each stage completes

### 4. Improve error handling and retries

**Why:** The current pipeline retries WebSocket failures, but other failure modes may stop the whole run.

**What to do:**
- Add robust handling for missing input files and invalid prompt file paths
- Add a retry policy for transient API failures in `tts.py` and `normal_to_aphasia.py`
- Add `continue` semantics to skip failed files without stopping the pipeline
- Report failed files clearly in the final summary

**How to implement:**
1. Add input validation to `main.py` and each module.
2. Wrap the audio generation loop in a retry decorator or helper.
3. Capture and log file-level failures; continue processing remaining files.

### 5. Add explicit dependency and environment documentation

**Why:** The existing `README.md` explains usage but the environment and dependency assumptions are not formally documented.

**What to do:**
- Add a `requirements.txt` review note in `todo.md` for potential updates
- Make sure `.env` usage is documented for `OPENAI_API_KEY`
- Add `python -m venv .venv` instructions and dependency install commands
- Document any external BatchAlign or CLAN requirements

**How to implement:**
1. Confirm current `requirements.txt` contents and pin versions where needed.
2. Add an INSTALLATION section to `README.md` and `process.md`.
3. Add a `setup.md` or a `docs/` note if necessary.

### 6. Add a lightweight validation/pre-check stage

**Why:** The pipeline currently assumes valid file contents and formats.

**What to do:**
- Validate that input text files are non-empty and well-formed
- Validate `.wav` audio properties before sending them to OpenAI or BatchAlign
- Validate prompt files are not empty and contain sensible instructions
- Add pre-check commands like `python main.py --validate-only`

**How to implement:**
1. Add helper validation functions in `helpers/` or within script modules.
2. Add a validation-only mode to `main.py`.
3. Return an explicit non-zero exit code when validation fails.

### 7. Add a formal data layout and naming conventions section

**Why:** The project has several input/output folders and the relationships should be clear to new collaborators.

**What to do:**
- Add a short `DATA_LAYOUT.md` or expand `process.md`
- Make explicit the relationship between transcript folder names and generated output folder names
- Note the difference between `aphasia-analysis` outputs and the broader workspace corpora

**How to implement:**
1. Update `process.md` with a `Data Flow Diagram` section or a directory table.
2. Optionally add a `todo` item for a diagram or drawing later.

### 8. Prepare a small test harness for the pipeline

**Why:** There is no automated way to verify the pipeline end-to-end before running on large data.

**What to do:**
- Add an example minimal dataset in `src/transcripts/` or `src/transcripts/sample/`
- Add a basic smoke test script to verify the pipeline stages work end-to-end on a few small files
- Keep tests lightweight and independent of external API calls if feasible

**How to implement:**
1. Add a `tests/` or `scripts/` folder with sample inputs and a smoke test command.
2. Add a `TODO` note for mocking the OpenAI Realtime and TTS APIs in future automated tests.

## Implementation Roadmap

### Phase 1: Make the runner stable and scriptable
- Refactor `main.py` to use CLI arguments
- Add deterministic output directory handling
- Add structured logging
- Add input validation and pre-checks

### Phase 2: Harden the API stages
- Improve retry and error handling in `tts.py`
- Improve retry and failure handling in `normal_to_aphasia.py`
- Add file-level failure summaries

### Phase 3: Documentation and developer experience
- Document installation and environment setup clearly
- Add data layout and naming conventions notes
- Add sample transcript data and a basic execution example

### Phase 4: Prepare for future automation
- Add a minimal smoke test harness
- Add explicit batchalign setup notes and dependency checks
- Plan a future integration test for the full end-to-end flow

## Short-Term Tactical Tasks

1. Refactor `main.py` to accept CLI arguments and optional config
2. Add `logging` to all core modules
3. Change directory cleanup to explicit flags
4. Add a `--validate-only` mode
5. Document how to run the pipeline non-interactively

## Mid-Term Strategic Tasks

1. Add file-level retry and skip logic for unreliable API calls
2. Add a small sample dataset for fast validation
3. Add a `docs/setup.md` or `docs/usage.md` section describing external tool requirements
4. Add a simple `pipeline.md` diagram or file relationship chart

## Long-Term Improvement Items

1. Split the pipeline into a reusable package or library with clear stage APIs
2. Add automated tests with dependency mocking
3. Add improved prompt management and versioning for aphasia simulation
4. Add support for alternative TTS or ASR backends if OpenAI APIs change

## Risks and Dependencies

- OpenAI API usage: prompt behavior and output audio format may change
- BatchAlign dependencies: external setup is required and not fully managed in code
- TalkBank / CLAN file formats: output quality depends on correct `CHAT` representation
- Data privacy: if any real TalkBank transcripts are used with external APIs, the project must be careful with compliance

## Summary

The next phase of improvement is not code refactoring for its own sake. It is about making the pipeline more reliable, reproducible, and easy to run by researchers. The highest-value changes are:
- predictable CLI configuration
- deterministic directory handling
- better logging and error recovery
- explicit validation before expensive API calls
- clearer documentation for collaborators
