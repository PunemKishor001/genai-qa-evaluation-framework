# Marlabs GenAI QA Candidate Assessment

## Overview

This project is an offline QA evaluation pack for the supplied
AI policy assistant assessment.

No live application, live model, API key, cloud account, or
external dataset is used.

## Technology

- Python 3
- PyTest
- JSON

## Project Structure

```text
corpus/
    policies.json

recordings/
    observations.json

expected/
    expected_results.json

evaluator/
    loader.py
    assertions.py
    evaluator.py

tests/
    test_evaluator.py
    test_variants.py

reports/
    evaluation_report.json

defects/
    defects.md

inventory/
    test_inventory.md

run_evaluation.py

# Marlabs GenAI QA Assessment

## Setup

```powershell
python -m pip install -r requirements.txt