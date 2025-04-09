# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Setup
- Python project with Flask, LangChain, OpenAI, and Twilio dependencies
- Use virtual environment with `python -m venv venv` and `source venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`
- Run local server: `python app.py`

## Code Style Guidelines
- Follow PEP 8 for Python code style
- Organize imports: standard library, third-party, local modules
- Use type hints for all function parameters and return values
- Use descriptive variable names following snake_case convention
- Class names should use PascalCase
- Error handling: use try/except blocks with specific exceptions
- Add docstrings for all functions and classes
- Limit line length to 88 characters (Black formatter compatible)
- Keep functions focused and under 50 lines when possible

## Testing
- Write unit tests in the tests/ directory using pytest
- Run all tests: `pytest`
- Run single test: `pytest tests/test_file.py::test_function`
- Include integration tests for Twilio webhook endpoints