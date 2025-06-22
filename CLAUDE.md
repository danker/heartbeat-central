# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is Heartbeat Central - a Flask-based centralized heartbeat monitoring service with pluggable alerting system. Applications register with the service and send periodic heartbeats. The system alerts when applications miss their expected heartbeat windows.

## Development Commands

### Setup
```bash
# Using uv (recommended)
uv pip install -e ".[dev]"
cp .env.example .env

# Or using pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
cp .env.example .env
```

### Running the Application
```bash
python app.py
```

### Testing
```bash
pytest
```

### Code Quality
```bash
black .
flake8 .
```

## Specification Workflow

Before implementing new features or making significant changes, create a detailed specification:

### Creating a Specification
1. Use `/new-spec [name]` to create a new specification from template
2. Or manually copy `specifications/TEMPLATE.md` to `specifications/[feature-name].md`
3. Fill out all relevant sections in the specification
4. Review with stakeholders before implementation

### Viewing Specifications
- Use `/list-specs` to see all existing specifications
- Specifications are stored in the `/specifications` directory

### Implementation Process
1. Always create a specification first for non-trivial features
2. Get the specification reviewed and approved
3. Use the specification as your implementation guide
4. Update the specification if requirements change during implementation
5. Check off acceptance criteria as you complete them

### Benefits
- Clear requirements before coding
- Better design decisions
- Fewer surprises during implementation
- Built-in documentation
- Easier code reviews