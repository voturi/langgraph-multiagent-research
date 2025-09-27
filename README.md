# LangGraph Research Agent - Production

🔬 **A production-ready AI research assistant built with LangGraph and clean architecture principles**

This system creates AI analyst personas, conducts structured interviews, performs web research, and generates comprehensive research reports with human-in-the-loop feedback.

## 🎯 Project Objectives

- **Multi-Analyst Research**: Generate diverse AI analyst personas to explore topics from multiple perspectives
- **Interactive Workflow**: Human-in-the-loop feedback system for analyst refinement
- **Structured Intelligence**: Conduct AI-driven interviews with expert search and synthesis
- **Production Ready**: Clean architecture, robust error handling, and comprehensive testing
- **Framework Agnostic**: Easily swap orchestration frameworks while preserving business logic

## 🏗️ Architecture Overview

This research agent follows **Clean Architecture** principles with clear separation of concerns:

```
┌─────────────────────────────────────────────────┐
│           Interactive Interface                 │
│        (interactive_research_assistant.py)     │
├─────────────────────────────────────────────────┤
│              Orchestration Layer                │
│         (LangGraph Research Workflow)          │
├─────────────────────────────────────────────────┤
│            Application Layer                    │
│          (Research Workflows)                   │
├─────────────────────────────────────────────────┤
│               Domain Layer                      │
│     (Research Logic, Analysts, Interviews)     │
├─────────────────────────────────────────────────┤
│            Infrastructure Layer                 │
│    (OpenAI, Tavily, Wikipedia, Storage)       │
└─────────────────────────────────────────────────┘
```

### Research Workflow

1. **Topic Analysis** → AI analyzes research topic and context
2. **Analyst Generation** → Creates diverse expert personas (2-5 analysts)
3. **Human Feedback** → User reviews and refines analyst selection
4. **Interview Execution** → AI conducts structured interviews with each analyst
5. **Research Synthesis** → Searches web, processes information, generates sections
6. **Report Compilation** → Produces comprehensive research report with citations

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd langgraph-research-agent-prod

# Install dependencies
pip install -e .
```

### 2. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
vim .env
```

Required API keys:
- `OPENAI_API_KEY` - For LLM operations
- `TAVILY_API_KEY` - For web search
- `LANGSMITH_API_KEY` - (Optional) For tracing

### 3. Run Research Assistant

```bash
# Start interactive research session
python interactive_research_assistant.py
```

### Example Research Session

```
🔍 Research topic: "AI applications in sustainable energy"
📊 Configuration: 3 analysts, 2 interview turns

👥 Generated Analysts:
1. Dr. Sarah Chen - Renewable Energy Systems Engineer
2. Prof. Michael Torres - AI Policy Researcher  
3. Lisa Zhang - Clean Tech Venture Capitalist

💬 Human Feedback: "Add more focus on policy implications"

🔄 Research Execution:
   ✅ Conducted 3 expert interviews
   ✅ Searched 15 information sources
   ✅ Generated 3 research sections
   ✅ Compiled final report with 25+ citations
```

## 📁 Project Structure

```
src/app/
├── domain/                          # 🎯 Core research logic
│   ├── entities/
│   │   └── research.py              # Analyst, Interview, ResearchProject
│   ├── services/
│   │   ├── research_service.py      # Research coordination
│   │   ├── analyst_service.py       # Analyst generation & validation
│   │   └── interview_service.py     # Interview management
│   ├── interfaces/
│   │   ├── research_repositories.py # Data access contracts
│   │   ├── services.py             # External service contracts
│   │   └── events.py               # Event handling
│   └── models/
│       ├── entities.py             # Base domain entities
│       ├── value_objects.py        # Immutable value types
│       └── events.py               # Domain events
├── application/
│   └── workflows/
│       └── research_workflow.py     # 🔄 Main research workflow
├── orchestration/
│   └── langgraph/                   # 🔀 LangGraph implementation
│       ├── research_orchestrator.py # Workflow orchestration
│       ├── research_nodes.py        # Individual workflow nodes
│       ├── research_state.py        # Workflow state management
│       └── research_entry.py        # Entry point & dependencies
└── infrastructure/                   # 🏗️ External integrations
    ├── services/
    │   ├── research_llm_service.py  # OpenAI integration
    │   ├── tavily_service.py        # Web search integration
    │   ├── wikipedia_service.py     # Wikipedia integration
    │   └── mock_research_service.py # Testing mock services
    └── repositories/
        ├── memory_research_repositories.py  # In-memory storage
        └── research_unit_of_work.py         # Transaction management
```

## 🎯 Key Features

### 🧠 AI Research Capabilities

- **Multi-Perspective Analysis**: Generate 2-5 expert analyst personas per topic
- **Structured Interviews**: AI-driven expert interviews with contextual search
- **Web Research Integration**: Real-time search via Tavily and Wikipedia APIs
- **Citation Management**: Automatic source tracking and citation generation
- **Quality Control**: Analyst validation and content quality assurance

### 🤝 Human-AI Collaboration

- **Interactive Feedback Loop**: Review and refine AI-generated analysts
- **Progressive Disclosure**: Step-by-step workflow with user control points
- **Transparency**: Full visibility into research process and sources
- **Customization**: Configurable analyst count and interview depth

### 🏛️ Production Architecture

- **Clean Architecture**: Domain-driven design with clear separation of concerns
- **Framework Agnostic**: Swap LangGraph for other orchestration frameworks
- **Dependency Inversion**: All dependencies point toward domain layer
- **Unit of Work Pattern**: Consistent data access and transaction management
- **Repository Pattern**: Abstracted data access with in-memory and persistent options

### 🔧 Technical Excellence

- **Type Safety**: Full type hints with mypy validation
- **Error Handling**: Comprehensive error handling and recovery
- **Async/Await**: Non-blocking I/O for external API calls
- **Logging**: Structured logging for debugging and monitoring
- **Testing**: Unit, integration, and contract testing support

## 🛠️ Configuration

### Environment Variables

```bash
# Core APIs
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini
TAVILY_API_KEY=your_key_here

# Research Configuration
MAX_ANALYSTS_DEFAULT=3
MAX_INTERVIEW_TURNS_DEFAULT=2
SEARCH_MAX_RESULTS=5
WIKIPEDIA_MAX_DOCS=2

# Optional: LangSmith Tracing
LANGSMITH_API_KEY=your_key_here
LANGSMITH_PROJECT_NAME=langgraph-research-agent-prod
LANGSMITH_TRACING=true
```

### Research Parameters

- **Analyst Count**: 2-5 diverse expert perspectives
- **Interview Turns**: 1-3 rounds of AI expert interviews per analyst
- **Search Results**: 3-10 web sources per interview turn
- **Wikipedia Docs**: 1-5 Wikipedia articles for additional context

## 🧪 Usage Examples

### Programmatic Usage

```python
from app.orchestration.langgraph.research_entry import create_research_dependencies
from app.orchestration.langgraph.research_orchestrator import ResearchOrchestrator

# Initialize research system
research_workflow = create_research_dependencies()
orchestrator = ResearchOrchestrator(research_workflow)

# Run research with human feedback
result = await orchestrator.run_research_with_interruption(
    topic="Future of quantum computing",
    max_analysts=3,
    max_interview_turns=2
)

# Process human feedback and continue
final_result = await orchestrator.continue_research_with_feedback(
    human_feedback="Focus more on practical applications",
    thread_config=result["thread_config"]
)
```

### Command Line Usage

```bash
# Interactive mode (recommended)
python interactive_research_assistant.py

# Direct execution with parameters
python -c "
from interactive_research_assistant import InteractiveResearchTester
import asyncio
tester = InteractiveResearchTester()
asyncio.run(tester.run_interactive_test())
"
```

## 🔄 Extending the System

### Adding New Search Providers

```python
class CustomSearchService:
    async def search(self, query: str) -> List[SearchResult]:
        # Implement your search logic
        pass

# Register in research_entry.py
research_workflow = ResearchWorkflow(
    custom_search_service=CustomSearchService(),
    # ... other dependencies
)
```

### Adding New LLM Providers

```python
class CustomLLMService(LLMService):
    async def generate_response(self, messages, **kwargs) -> ExecutionResult:
        # Implement your LLM integration
        pass

# Use in workflow configuration
research_workflow = ResearchWorkflow(
    llm_service=CustomLLMService(),
    # ... other dependencies
)
```

### Alternative Orchestration Frameworks

Replace LangGraph with other orchestration systems:

```python
# Hypothetical Airflow integration
from app.orchestration.airflow import AirflowResearchOrchestrator

orchestrator = AirflowResearchOrchestrator(research_workflow)
# Same interface, different execution engine
```

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