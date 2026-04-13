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

### Remaining improvements
These are the next items I would plan for the project:

### A. Strengthen dependency and environment documentation
**Why:** The project depends on OpenAI and BatchAlign environments, and these should be documented clearly.

**What to do:**
- Add explicit `.env` setup instructions for `OPENAI_API_KEY`
- Document Python environment creation and dependency installation
- Clarify external BatchAlign and CLAN requirements

**How to implement:**
1. Review `requirements.txt` and update pins if needed.
2. Add an `INSTALLATION` or `docs/setup.md` section.
3. Include `.venv` setup instructions and recommended command sequences.

### B. Add a formal data layout and naming conventions note
**Why:** The input/output relationships are important for reproducibility.

**What to do:**
- Add a data layout section in `process.md`
- Document naming conventions for transcript folders and output folders
- Clarify the difference between `aphasia-analysis` outputs and broader workspace corpora

**How to implement:**
1. Expand `process.md` with a directory table or data flow section.
2. Add a simple pipeline diagram or architecture note if useful.

### C. Include a CLI argument that allows the aphasiafier to run step 0 and 2 but skip 1

**Why:** This is necessary to set up the BA2 control and BA2 Aphasia data types

**What to do:**
- Add a new CLI argument to the parser
- Add new logic flow that allows main.py to run step 0 then step 2 without step 1