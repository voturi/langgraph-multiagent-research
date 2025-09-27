# LangGraph Studio Setup

This guide helps you run this project in LangGraph Studio on macOS.

Prerequisites
- Python 3.10+ (you have 3.11, which is fine)
- Git and pip

1) Create and activate a virtual environment
```bash
python -m venv .venv
source .venv/bin/activate
```

2) Install project and runtime dependencies
We’ll install the project in editable mode with extras and ensure compatible runtime packages for Studio and Starlette.
```bash
# Base project
pip install -e .

# Orchestration & LLM providers
pip install -e ".[langgraph,openai,fastapi]"

# Studio + runtime (versions known to work per your environment and prior fixes)
pip install "langgraph-cli>=0.3.0" \
            "langgraph-api>=0.4.15" \
            "starlette>=0.47.2" \
            "uvicorn>=0.30.0" \
            "sse-starlette>=2.1.3" \
            "tavily-python>=0.7.11"
```

Notes
- External context indicates Starlette import issues are resolved with: langgraph-api>=0.4.15 and starlette>=0.47.2. The above pins reflect that.
- Your current environment already shows compatible versions; these commands will align a fresh environment.

3) Configure environment variables
Copy the example file and fill in values (do not commit secrets):
```bash
cp .env.example .env
```
Supported variables:
- OPENAI_API_KEY: Required for OpenAI-backed nodes
- TAVILY_API_KEY: Required if using Tavily search
- LANGSMITH_API_KEY (optional): For tracing/telemetry

4) Provide a graph entrypoint for Studio (recommended)
LangGraph Studio expects a module path to a compiled graph or a factory. This repo already contains a LangGraph orchestrator, but for Studio we recommend a small entrypoint that exposes a `graph` variable.

Proposed file (not yet created) at:
- src/app/orchestration/langgraph/studio_entry.py

It should:
- Construct dependencies (mock or real) 
- Instantiate the LangGraphOrchestrator (or a research-specific orchestrator when added)
- Expose a `graph` variable or a `get_graph()` factory that returns the compiled graph

If you want, I can create this entrypoint for you—just say "create the Studio entrypoint".

5) Launch LangGraph Studio

**Option A: Using Makefile (Recommended)**
```bash
# Complete setup with one command
make dev-setup

# Launch Studio (requires API keys)
make studio

# Or launch in demo mode (works without API keys)
make studio-demo
```

**Option B: Manual launch**
```bash
langgraph dev --port 2024 --root src \
  --graph app.orchestration.langgraph.studio_entry:graph
```

6) Open the Studio UI
Open http://localhost:2024 in your browser.

7) Test the Graph
```bash
# Test graph compilation
make check-graph

# Run example workflows
make run-example

# Show environment info
make info
```

8) Troubleshooting
```bash
# Debug Studio issues
make debug-studio
```

Common issues:
- Starlette import errors: ensure `starlette>=0.47.2` and `langgraph-api>=0.4.15` are installed.
- Missing API keys: set OPENAI_API_KEY and TAVILY_API_KEY in `.env`.
- Module import errors: ensure you're in the project root and using `--root src`.

9) Available Make Commands
```bash
# See all available commands
make help

# Quick development cycle
make quick-test

# Complete validation
make validate-all
```
