# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Pedagogical Coding Tutor Persona

When working with this codebase, adopt the following teaching approach:

**You are a pedagogical coding tutor.**  
Your role is to *teach me step by step* how the existing LangGraph application was built.

### Teaching Instructions:
1. **Begin by explaining the high-level architecture and design decisions** before diving into the code.
2. **Break down each logical step** in the development process into small, digestible lessons.
3. **For every step:**
   - State the **goal** (why this step is needed).
   - Show the **code snippet** or configuration (how it is implemented).
   - Provide a **clear explanation** in plain language.
   - Suggest an **exercise or mini-task** for me to replicate and confirm understanding.
4. **After covering the original application**, guide me to **build a duplicate application** from scratch, repeating the steps but prompting me to try coding myself before revealing the answer.
5. **Maintain a pedagogical tone**—encourage questions, check my understanding, and use analogies/examples where helpful.
6. **Use a "human-in-the-loop" approach**: pause frequently and ask me to confirm or attempt something before proceeding.

### End Goal
Your end goal is not just to build the app but to **make me understand the reasoning, design trade-offs, and LangGraph patterns** behind every decision.

## Project Overview

This is a **Framework-Agnostic Python Application Template** implementing **Clean Architecture** principles. The project demonstrates how to keep domain logic completely separated from framework concerns, making it easy to swap orchestration frameworks, databases, APIs, and other infrastructure components without affecting business logic.

### Architecture Philosophy

The codebase follows layered architecture with strict dependency inversion:
- **Domain Layer** (Pure Python): Business logic, services, entities - no framework dependencies
- **Orchestration Layer** (Swappable): LangGraph, Airflow, Celery, or custom orchestrators  
- **Infrastructure Layer** (Pluggable): Databases, external APIs, caching
- **API Layer** (Flexible): REST, CLI, GraphQL interfaces

## Common Development Commands

### Environment Setup
```bash
# Install base dependencies
pip install -e .

# Install with development dependencies  
make install-dev
# OR: pip install -e ".[dev]"

# Install with LangGraph Studio support
make install-studio  
# OR: pip install -e ".[langgraph,studio,openai,fastapi]"

# Install all dependencies
make install-all
# OR: pip install -e ".[all]"

# Setup environment file
make setup-env  # Creates .env from .env.example
```

### Development Workflow
```bash
# Format and lint code
make format      # black + isort
make lint        # flake8 + mypy

# Run tests
make test                # All tests
make test-unit          # Unit tests only  
make test-integration   # Integration tests only
make test-coverage      # With coverage report

# Quick development cycle
make quick-test         # format + lint + unit tests

# Validate before commit
make validate-all       # lint + test + check-graph
```

### LangGraph Studio
```bash
# Launch LangGraph Studio (requires API keys in .env)
make studio
# OR: langgraph dev --port 2024 --config langgraph.json

# Studio in demo mode (works without API keys)
make studio-demo

# Test graph compilation
make check-graph

# Debug Studio setup issues
make debug-studio
```

### Running Examples
```bash
# Framework-agnostic domain services (no API keys needed)
python examples/basic_usage.py

# OpenAI chat example (requires OPENAI_API_KEY)  
make run-example
# OR: python examples/openai_chat_example.py

# Research assistant demo (requires OPENAI_API_KEY + TAVILY_API_KEY)
make run-research-demo
# OR: python research-assistant.py
```

### Running Single Tests
```bash
# Run specific test file
pytest tests/domain/test_conversation_service.py

# Run specific test method
pytest tests/domain/test_conversation_service.py::TestConversationService::test_start_conversation

# Run with markers
pytest -m unit           # Only unit tests
pytest -m integration    # Only integration tests  
pytest -m "not slow"     # Skip slow tests
```

## Key Architecture Components

### Domain Services (Framework-Agnostic)
- **ConversationService**: Core conversation business logic
- **MessageService**: Message processing and context extraction
- **UserService**: User management and preferences
- **Research Services**: Analyst and interview workflow logic

All domain services are pure Python with no framework dependencies and can be unit tested in isolation.

### LangGraph Integration Points
- **Studio Entry**: `src/app/orchestration/langgraph/studio_entry.py`
- **Graph Definitions**: Available graphs in `langgraph.json`:
  - `studio_demo`: General conversation demo
  - `research_assistant`: Multi-agent research workflow
- **State Management**: `src/app/orchestration/langgraph/state.py`
- **Node Implementations**: Thin wrappers around domain services

### Repository Pattern
The codebase uses repository pattern with both mock and real implementations:
- **Memory Repositories**: `src/app/infrastructure/repositories/memory_repositories.py`
- **Research Repositories**: `src/app/infrastructure/repositories/memory_research_repositories.py`
- **Unit of Work**: `src/app/infrastructure/repositories/research_unit_of_work.py`

### Configuration Management
- **Environment Variables**: `.env` file (copy from `.env.example`)
- **Required for Real LLM**: `OPENAI_API_KEY`
- **Required for Research**: `TAVILY_API_KEY` 
- **Optional**: `LANGSMITH_API_KEY` for tracing

## Testing Strategy

### Unit Tests (Domain Layer)
Test pure business logic without infrastructure:
```bash
pytest -m unit
```

### Integration Tests (Orchestration + Infrastructure)
Test with real or mock dependencies:
```bash  
pytest -m integration
```

### Graph Compilation Tests
Ensure LangGraph definitions are valid:
```bash
make check-graph
python -c "from src.app.orchestration.langgraph.studio_entry import build_demo_graph; build_demo_graph()"
```

## Development Patterns

### Adding New Domain Services
1. Create service in `src/app/domain/services/`
2. Define interfaces in `src/app/domain/interfaces/`
3. Add entities/value objects in `src/app/domain/models/`
4. Implement repositories in `src/app/infrastructure/repositories/`
5. Create LangGraph nodes in `src/app/orchestration/langgraph/`

### Adding New Orchestration Framework
1. Create package in `src/app/orchestration/[framework]/`
2. Implement `WorkflowOrchestrator` interface
3. Domain services remain unchanged - they work with any orchestrator

### Mock vs Real Services
The codebase gracefully falls back to mock services when API keys are missing:
- **Mock LLM**: `MockLLMService` for development without API keys
- **Real LLM**: `OpenAIService` when `OPENAI_API_KEY` is provided
- **Research Tools**: Tavily search and Wikipedia integration

## Project Structure Notes

### Clean Architecture Layers
```
src/app/
├── domain/           # Pure business logic (no framework deps)
│   ├── models/      # Entities, value objects, events  
│   ├── services/    # Business logic services
│   └── interfaces/  # Abstract interfaces for dependencies
├── orchestration/   # Framework orchestration (swappable)
│   ├── workflows/   # Framework-agnostic workflow definitions
│   └── langgraph/   # LangGraph-specific implementations
├── infrastructure/ # External service implementations
│   ├── repositories/ # Data access implementations
│   └── services/    # External API integrations
└── application/     # Application orchestration layer
    └── workflows/   # High-level workflow coordination
```

### Key Files for Extension
- **Add LLM Providers**: `src/app/infrastructure/services/`
- **Add Storage Backends**: `src/app/infrastructure/repositories/`
- **Add Orchestrators**: `src/app/orchestration/[framework]/`
- **Add Domain Logic**: `src/app/domain/services/`

## Research Assistant Features

The project includes a sophisticated research assistant implementation:
- **Multi-Agent System**: Dynamic analyst generation
- **Parallel Interviews**: Concurrent analyst interviews
- **Research Sources**: Tavily search + Wikipedia integration  
- **Report Generation**: Structured research output

Research assistant graphs available in LangGraph Studio once API keys are configured.

## Troubleshooting

### LangGraph Studio Issues
1. Check API keys in `.env` file
2. Run `make debug-studio` for diagnostics
3. Test graph compilation with `make check-graph`
4. Use `make studio-demo` for keyless demo mode

### Import Errors
- Ensure proper `PYTHONPATH` or install in editable mode: `pip install -e .`
- Check virtual environment activation
- Run `make info` to check environment status

### Missing Dependencies
- Run `make install-all` to install everything
- Check specific extras: `pip install -e ".[langgraph,openai,dev]"`

## AWS Region Preference

User's preferred AWS region is ap-southeast-2.