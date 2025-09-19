# Framework-Agnostic Application Template

A comprehensive Python application template that follows **Clean Architecture** principles to keep domain logic completely separated from framework concerns. This design makes it easy to swap out orchestration frameworks, databases, APIs, and other infrastructure components without affecting business logic.

## 🏗️ Architecture Overview

This template implements a **layered architecture** that isolates concerns and dependencies:

```
┌─────────────────────────────────────────────────┐
│                 API Layer                       │
│            (REST, CLI, GraphQL)                 │
├─────────────────────────────────────────────────┤
│              Orchestration Layer                │
│         (LangGraph, Airflow, etc.)             │
├─────────────────────────────────────────────────┤
│               Domain Layer                      │
│    (Business Logic, Services, Entities)        │
├─────────────────────────────────────────────────┤
│            Infrastructure Layer                 │
│    (Databases, External APIs, Caching)         │
└─────────────────────────────────────────────────┘
```

### Key Principles

- **🎯 Domain-First**: Business logic lives in framework-agnostic domain services
- **🔌 Pluggable**: Swap LangGraph for other orchestration frameworks easily  
- **📦 Dependency Inversion**: Dependencies point inward to domain layer
- **🧪 Testable**: Pure domain logic can be unit tested without infrastructure
- **📈 Scalable**: Clean separation allows independent scaling of components

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd langgraph-audio-agnostic

# Install base dependencies
pip install -e .

# Install with specific extras
pip install -e ".[langgraph,openai,dev]"  # For LangGraph + OpenAI
pip install -e ".[all]"                   # Install everything
```

### 2. Basic Usage

The application is designed to be framework-agnostic. Here's how to use it:

#### Option A: Direct Domain Services (Framework-Agnostic)

```python
from app.domain.services import ConversationService
from app.domain.models.value_objects import ExecutionContext, UserId, ConversationId

# Use domain services directly (no framework required)
context = ExecutionContext(
    user_id=UserId("user_123"),
    conversation_id=None,  # Will create new
    session_id="session_456"
)

# Business logic is completely framework-independent
result = await conversation_workflow.execute_workflow(
    "simple_chat",
    context,
    {"message": "Hello, world!"}
)
```

#### Option B: LangGraph Orchestration

```python
from app.orchestration.langgraph import LangGraphOrchestrator

# LangGraph is just one possible orchestration layer
orchestrator = LangGraphOrchestrator(conversation_workflow, **deps)

result = await orchestrator.execute_workflow(
    "simple_chat",
    context, 
    {"message": "Hello, world!"}
)
```

#### Option C: Alternative Orchestration

```python
# Easy to swap to different orchestration frameworks
from app.orchestration.airflow import AirflowOrchestrator  # Hypothetical
from app.orchestration.celery import CeleryOrchestrator    # Hypothetical

# Same interface, different implementation
orchestrator = AirflowOrchestrator(conversation_workflow, **deps)
```

## 📁 Project Structure

```
src/app/
├── domain/                     # 🎯 Core business logic (framework-agnostic)
│   ├── models/                 #   Domain entities & value objects
│   │   ├── entities.py         #   Business entities (User, Conversation, etc.)
│   │   ├── value_objects.py    #   Immutable value objects & IDs
│   │   └── events.py           #   Domain events
│   ├── services/               #   Business logic services  
│   │   ├── conversation_service.py  #   Conversation business logic
│   │   ├── task_service.py          #   Task management logic
│   │   └── user_service.py          #   User management logic
│   └── interfaces/             #   Abstract interfaces for external dependencies
│       ├── repositories.py     #   Data access interfaces
│       ├── services.py         #   External service interfaces (LLM, etc.)
│       └── events.py           #   Event handling interfaces
├── orchestration/              # 🔌 Orchestration layer (swappable)
│   ├── workflows/              #   Framework-agnostic workflow definitions
│   │   ├── base.py             #   Base orchestrator interface
│   │   └── conversation_workflow.py  #   Conversation workflow logic
│   └── langgraph/              #   LangGraph-specific implementation
│       ├── orchestrator.py     #   LangGraph orchestrator
│       ├── nodes.py            #   LangGraph nodes (thin wrappers)
│       └── state.py            #   LangGraph state schema
├── infrastructure/             # 🏗️ Infrastructure implementations
│   ├── repositories/           #   Database implementations
│   ├── integrations/           #   External service integrations
│   └── config/                 #   Configuration management
└── api/                        # 🌐 API layer (also swappable)
    ├── rest/                   #   REST API (FastAPI, Flask, etc.)
    └── cli/                    #   Command-line interface
```

## 🎯 Key Features

### Framework Agnostic Design

- **Domain Logic**: Pure Python business logic with no framework dependencies
- **Swappable Orchestration**: LangGraph, Airflow, Celery, or custom orchestrators
- **Pluggable Storage**: SQLite, PostgreSQL, MongoDB, or any database
- **Flexible APIs**: FastAPI, Flask, Django, or any web framework

### Clean Architecture

- **Dependency Inversion**: All dependencies point toward the domain layer
- **Interface Segregation**: Small, focused interfaces for external dependencies  
- **Single Responsibility**: Each layer has a clear, single purpose
- **Open/Closed Principle**: Easy to extend without modifying existing code

### Testing Strategy

- **Unit Tests**: Test domain logic without any infrastructure
- **Integration Tests**: Test orchestration with real or mock dependencies
- **Contract Tests**: Ensure interfaces are correctly implemented

## 🛠️ Development

### Available Commands

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only  

# Code quality
black src tests         # Format code
isort src tests         # Sort imports
flake8 src tests        # Lint code
mypy src                # Type checking
```

### Adding New Orchestration Frameworks

To add support for a new orchestration framework (e.g., Apache Airflow):

1. **Create orchestration package**:
   ```
   src/app/orchestration/airflow/
   ├── __init__.py
   ├── orchestrator.py     # Implement WorkflowOrchestrator interface
   └── dag_builder.py      # Framework-specific logic
   ```

2. **Implement the interface**:
   ```python
   class AirflowOrchestrator(WorkflowOrchestrator):
       async def execute_workflow(self, workflow_name, context, input_data):
           # Translate to Airflow DAG execution
           # Business logic stays in domain services
   ```

3. **Business logic remains unchanged** - domain services work with any orchestrator!

### Adding New Storage Backends

To add a new database (e.g., MongoDB):

1. **Create repository implementation**:
   ```python
   class MongoUserRepository(UserRepository):
       async def find_by_id(self, user_id: UserId) -> Optional[User]:
           # MongoDB-specific implementation
   ```

2. **Domain services remain unchanged** - they only depend on the interface!

## 🔧 Configuration

The application supports multiple configuration methods:

```python
# 1. Environment variables
export OPENAI_API_KEY="your-key"
export DATABASE_URL="sqlite:///app.db"

# 2. Configuration files
# config/development.yaml
# config/production.yaml

# 3. Dependency injection container
from app.infrastructure.config import Container
container = Container()
```

## 📚 Examples

See the `examples/` directory for complete usage examples:

- `examples/basic_usage.py` - Pure domain services
- `examples/langgraph_example.py` - Using LangGraph orchestration  
- `examples/custom_orchestrator.py` - Custom orchestration implementation
- `examples/testing_examples.py` - Testing patterns

## 🤔 Why This Architecture?

### Traditional Problem
```python
# Tightly coupled to LangGraph
from langgraph import StateGraph
from langchain_openai import ChatOpenAI

def my_business_logic(state):
    # Business logic mixed with LangGraph specifics
    llm = ChatOpenAI()  # Hard dependency
    # ... LangGraph-specific code
```

### Our Solution
```python
# Domain service - framework agnostic  
class ConversationService:
    def __init__(self, llm_service: LLMService):  # Abstract interface
        self.llm_service = llm_service
    
    async def process_message(self, user_id, message):
        # Pure business logic, no framework dependencies
        # Can be tested in isolation
        # Works with any LLM service implementation
```

### Benefits

1. **🔄 Easy Migration**: Swap LangGraph for other frameworks without touching business logic
2. **🧪 Better Testing**: Unit test domain logic without infrastructure complexity  
3. **📈 Team Scalability**: Frontend/backend teams can work independently
4. **🛡️ Risk Reduction**: Framework changes don't break business logic
5. **💰 Cost Efficiency**: Choose optimal infrastructure for each use case

## 🔗 Related Patterns

- **Clean Architecture** (Robert C. Martin)
- **Hexagonal Architecture** (Ports & Adapters)
- **Domain-Driven Design** (DDD)
- **Dependency Injection** & **Inversion of Control**

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

**🎯 The key insight**: Keep your business logic pure and framework-agnostic. Use frameworks as implementation details, not architectural foundations.