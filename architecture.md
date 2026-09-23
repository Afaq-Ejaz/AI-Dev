# TicketWise — Project Architecture

```
AI-DEV/
│
├── .git/                          # Git version control history
├── .venv/                         # Python virtual environment (managed by uv)
│
├── .gitignore                     # Specifies files/folders Git should ignore
├── .env                           # Environment variables (GEMINI_API_KEY)
├── .python-version                # Pins the Python interpreter version for the project
├── pyproject.toml                 # Project metadata, dependencies, and build config (uv)
├── uv.lock                        # Locked dependency versions for reproducible installs
├── README.md                      # Project overview and documentation (currently empty)
├── architecture.md                # This file — folder structure reference
│
├── Progress/                      # Development roadmap and learning documentation
│   ├── status.md                  # Phase-by-phase task tracker with checkboxes
│   ├── learning_objectives        # Skill domains the project is designed to teach
│   ├── learning_track.md          # AI-assisted learning methodology and progression
│   └── system_pipeline            # Placeholder for pipeline flow documentation
│
└── src/                           # Application source code
    └── ai_dev/                    # Main Python package
        ├── __init__.py            # Package entry point; defines the CLI main() function
        ├── contract.py            # Pydantic data models (TicketInput, TicketClassification, TriageResult)
        ├── kb.json                # Knowledge base — 8 company support policies as structured JSON
        ├── main.py                # FastAPI app initialization, env loading, and GenAI client setup
        └── retrieval.py           # Embedding generation, cosine similarity, and KB policy retrieval
```
