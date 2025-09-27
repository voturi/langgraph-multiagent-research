# Research Assistant Plan

## 🎯 **Project Overview**

Transform the monolithic `research-assistant.py` (414 lines) into a clean architecture implementation that demonstrates advanced LangGraph capabilities while maintaining all existing functionality.

## 📊 **Current State Analysis**

### **Existing research-assistant.py Features**
- ✅ **Dual Workflow System**: Analyst generation + research interviews  
- ✅ **Human-in-the-Loop**: Interactive analyst refinement with interruptions
- ✅ **Multi-Agent Research**: Analyst-expert interview coordination
- ✅ **Multi-Source Search**: Tavily web search + Wikipedia integration
- ✅ **Structured Output**: Pydantic models with validation
- ✅ **Advanced LangGraph**: Checkpointing, state management, routing
- ✅ **Report Generation**: Automated research document creation

### **Architectural Problems**
- ❌ **Monolithic Design**: All concerns mixed in single 414-line file
- ❌ **Hard Dependencies**: Direct LangGraph, OpenAI, Tavily coupling
- ❌ **No Abstraction**: External services used directly in nodes
- ❌ **Untestable Logic**: Business rules embedded in LangGraph code
- ❌ **Framework Lock-in**: Cannot swap orchestration frameworks

## 🏗️ **Clean Architecture Integration Strategy**

### **Target Architecture**
```
Research System Architecture
├── 🎯 Domain Layer (Pure business logic)
│   ├── Entities: Analyst, Interview, Report
│   ├── Services: ResearchService, QuestionService
│   └── Events: AnalystCreated, InterviewCompleted
├── 🔌 Infrastructure Layer (External dependencies)
│   ├── OpenAI: Analyst generation, Q&A
│   ├── Tavily: Web search integration
│   └── Repositories: Data persistence
├── 🎪 Orchestration Layer (Framework wrappers)
│   ├── LangGraph: Advanced workflow orchestration
│   ├── Simple: Sequential workflow execution
│   └── Base: Framework-agnostic interface
└── 🌐 API Layer (User interfaces)
    ├── REST: HTTP endpoints
    └── CLI: Command-line interface
```

## 📅 **Implementation Roadmap**

### **Phase 1: Domain Layer Foundation (Week 1)**

#### **🎯 Domain Entities**
```python
# Target: src/app/domain/models/entities.py

class Analyst(BaseEntity):
    """Research analyst with expertise and focus areas"""
    id: AnalystId
    name: str
    affiliation: str  
    role: str
    description: str
    expertise_areas: List[str] = Field(default_factory=list)
    
    def get_persona_description(self) -> str:
        """Business logic for persona generation"""
        
    def is_suitable_for_topic(self, topic: str) -> bool:
        """Domain logic for analyst-topic matching"""

class ResearchInterview(BaseEntity):
    """Interview session between analyst and expert"""
    id: InterviewId
    analyst_id: AnalystId
    topic: str
    questions: List[Question] = Field(default_factory=list)
    answers: List[Answer] = Field(default_factory=list)
    max_turns: int = 3
    status: InterviewStatus = InterviewStatus.PENDING
    
    def is_complete(self) -> bool:
        """Business rule: interview completion logic"""

class ResearchReport(BaseEntity):
    """Generated research report from interview"""
    id: ReportId
    title: str
    topic: str
    analyst_id: AnalystId
    interview_id: InterviewId
    sections: List[ReportSection] = Field(default_factory=list)
    word_count: int = 0
    
    def calculate_metrics(self) -> Dict[str, Any]:
        """Business logic for report analysis"""
```

#### **🏷️ Value Objects** 
```python
# Target: src/app/domain/models/value_objects.py

@dataclass(frozen=True)
class AnalystId:
    value: str
    
@dataclass(frozen=True)
class SearchQuery:
    query: str
    max_results: int = 3
    sources: List[str] = field(default_factory=lambda: ["web", "wikipedia"])

@dataclass(frozen=True)
class InterviewContext:
    topic: str
    analyst_persona: str
    max_turns: int = 3
    research_focus: Optional[str] = None

class InterviewStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress" 
    COMPLETED = "completed"
    FAILED = "failed"
```

#### **📢 Domain Events**
```python
# Target: src/app/domain/models/events.py

class AnalystCreated(DomainEvent):
    analyst_id: AnalystId
    topic: str
    analyst_details: Dict[str, Any]

class InterviewStarted(DomainEvent):
    interview_id: InterviewId
    analyst_id: AnalystId
    topic: str

class QuestionGenerated(DomainEvent):
    interview_id: InterviewId
    question: str
    question_number: int

class InterviewCompleted(DomainEvent):
    interview_id: InterviewId
    total_questions: int
    total_sources: int
```

#### **⚙️ Domain Services**
```python
# Target: src/app/domain/services/research_service.py

class ResearchService:
    """Core research business logic"""
    
    async def generate_analysts_for_topic(
        self,
        uow: UnitOfWork,
        topic: str,
        max_analysts: int = 3,
        human_feedback: Optional[str] = None
    ) -> List[Analyst]:
        """Business logic for analyst creation"""
        
    async def start_research_interview(
        self,
        uow: UnitOfWork,
        analyst: Analyst,
        topic: str,
        max_turns: int = 3
    ) -> ResearchInterview:
        """Business logic for interview initiation"""
        
    async def generate_research_report(
        self,
        uow: UnitOfWork,
        interview: ResearchInterview,
        analyst: Analyst
    ) -> ResearchReport:
        """Business logic for report creation"""

# Target: src/app/domain/services/question_generation_service.py

class QuestionGenerationService:
    """Question generation business logic"""
    
    def generate_interview_question(
        self,
        analyst: Analyst,
        conversation_history: List[Message],
        context: InterviewContext
    ) -> str:
        """Business rules for question quality"""
        
    def should_end_interview(
        self,
        conversation_history: List[Message],
        max_turns: int
    ) -> bool:
        """Business logic for completion detection"""
```

#### **Week 1 Deliverables**
- [ ] Domain entities with business logic methods
- [ ] Value objects with validation rules  
- [ ] Domain events for all key actions
- [ ] Domain services with pure business logic
- [ ] Unit tests for all domain logic (>90% coverage)

---

### **Phase 2: Infrastructure Layer (Week 2)**

#### **🔌 Abstract Interfaces**
```python
# Target: src/app/domain/interfaces/services.py

class AnalystGenerationService(ABC):
    """Abstract interface for AI analyst generation"""
    @abstractmethod
    async def generate_analysts(
        self, topic: str, max_analysts: int, feedback: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        pass

class SearchService(ABC):
    """Abstract interface for search operations"""
    @abstractmethod
    async def search_web(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def search_wikipedia(self, query: str, max_docs: int = 2) -> List[Dict[str, Any]]:
        pass

class QuestionAnswerService(ABC):
    """Abstract interface for Q&A operations"""
    @abstractmethod
    async def generate_question(self, persona: str, history: List[Dict]) -> str:
        pass
    
    @abstractmethod  
    async def generate_answer(self, question: str, context: List[str], focus: str) -> str:
        pass
```

#### **🛠️ Concrete Implementations**
```python
# Target: src/app/infrastructure/services/openai_research_service.py

class OpenAIAnalystGenerationService(AnalystGenerationService):
    """OpenAI implementation for analyst generation"""
    
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
    
    async def generate_analysts(
        self, topic: str, max_analysts: int, feedback: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Use existing LLMService abstraction"""
        prompt = self._build_analyst_prompt(topic, max_analysts, feedback)
        result = await self.llm_service.generate_structured_response(
            messages=[{"role": "system", "content": prompt}],
            response_schema=PerspectivesSchema,
            model="gpt-4o"
        )
        return [analyst.dict() for analyst in result.analysts]

# Target: src/app/infrastructure/services/tavily_search_service.py

class TavilySearchService(SearchService):
    """Tavily implementation for web search"""
    
    def __init__(self, api_key: str):
        self.search_tool = TavilySearchResults(max_results=10)
    
    async def search_web(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        results = await self.search_tool.ainvoke(query)
        return results[:max_results]
    
    async def search_wikipedia(self, query: str, max_docs: int = 2) -> List[Dict[str, Any]]:
        loader = WikipediaLoader(query=query, load_max_docs=max_docs)
        docs = await loader.aload()
        return [{"content": doc.page_content, "source": doc.metadata.get("source")} for doc in docs]
```

#### **📊 Repository Implementations**
```python
# Target: src/app/infrastructure/repositories/memory_research_repositories.py

class MemoryAnalystRepository(AnalystRepository):
    """In-memory implementation for development"""
    
    def __init__(self):
        self._analysts: Dict[str, Analyst] = {}
        self._by_topic: Dict[str, List[AnalystId]] = defaultdict(list)
    
    async def save(self, analyst: Analyst) -> None:
        self._analysts[analyst.id.value] = analyst
    
    async def find_by_id(self, analyst_id: AnalystId) -> Optional[Analyst]:
        return self._analysts.get(analyst_id.value)
    
    async def find_by_topic(self, topic: str) -> List[Analyst]:
        analyst_ids = self._by_topic.get(topic, [])
        return [self._analysts[aid.value] for aid in analyst_ids if aid.value in self._analysts]
```

#### **Week 2 Deliverables**
- [ ] Abstract interfaces for all external services
- [ ] OpenAI service implementations using existing LLMService
- [ ] Tavily and Wikipedia search service implementations
- [ ] In-memory repositories for development and testing
- [ ] Integration tests with mock external services

---

### **Phase 3: LangGraph Orchestration Layer (Week 3)**

#### **🎭 Framework-Agnostic Workflows**
```python
# Target: src/app/orchestration/workflows/research_workflow.py

class ResearchWorkflow(BaseWorkflow):
    """Pure business logic workflows - no framework dependencies"""
    
    def __init__(
        self,
        research_service: ResearchService,
        question_service: QuestionGenerationService,
        analyst_service: AnalystGenerationService,
        search_service: SearchService,
        qa_service: QuestionAnswerService
    ):
        # Inject all dependencies
        pass
    
    async def generate_analysts_workflow(
        self,
        uow: UnitOfWork,
        topic: str,
        max_analysts: int = 3,
        human_feedback: Optional[str] = None
    ) -> List[Analyst]:
        """Framework-agnostic analyst generation"""
        return await self.research_service.generate_analysts_for_topic(
            uow, topic, max_analysts, human_feedback
        )
    
    async def conduct_interview_workflow(
        self,
        uow: UnitOfWork,
        analyst: Analyst,
        topic: str,
        max_turns: int = 3
    ) -> ResearchReport:
        """Framework-agnostic interview orchestration"""
        # Pure business logic using domain services
        interview = await self.research_service.start_research_interview(
            uow, analyst, topic, max_turns
        )
        
        conversation_history = []
        for turn in range(max_turns):
            # Generate question
            question = self.question_service.generate_interview_question(
                analyst, conversation_history, InterviewContext(topic=topic, analyst_persona=analyst.get_persona_description())
            )
            
            # Search for context
            search_results = await self.search_service.search_web(question)
            
            # Generate answer
            answer = await self.qa_service.generate_answer(question, search_results, analyst.description)
            
            # Update conversation
            conversation_history.extend([
                {"role": "analyst", "content": question},
                {"role": "expert", "content": answer}
            ])
            
            # Check completion
            if self.question_service.should_end_interview(conversation_history, max_turns):
                break
        
        # Generate report
        return await self.research_service.generate_research_report(uow, interview, analyst)
```

#### **🎪 LangGraph Orchestrator**
```python  
# Target: src/app/orchestration/langgraph/research_orchestrator.py

class LangGraphResearchOrchestrator(LangGraphOrchestrator):
    """LangGraph-specific orchestration - thin wrapper over domain workflows"""
    
    def __init__(self, research_workflow: ResearchWorkflow, **kwargs):
        super().__init__(**kwargs)
        self.research_workflow = research_workflow
        self.analyst_graph = self._build_analyst_graph()
        self.interview_graph = self._build_interview_graph()
    
    def _build_analyst_graph(self) -> StateGraph:
        """Build LangGraph for analyst generation with human-in-the-loop"""
        
        class AnalystState(TypedDict):
            topic: str
            max_analysts: int
            human_feedback: Optional[str]
            analysts: List[Dict[str, Any]]
            requires_human_input: bool
        
        def generate_analysts_node(state: AnalystState) -> AnalystState:
            """Thin wrapper - delegates to domain workflow"""
            analysts = await self.research_workflow.generate_analysts_workflow(
                self.uow, state["topic"], state["max_analysts"], state.get("human_feedback")
            )
            return {
                "analysts": [a.dict() for a in analysts],
                "requires_human_input": state.get("human_feedback") is None
            }
        
        def human_feedback_node(state: AnalystState) -> AnalystState:
            """LangGraph-specific: pause for human input"""
            return state  # Pauses due to interrupt_before
        
        def route_human_feedback(state: AnalystState) -> str:
            return "generate_analysts" if state.get("human_feedback") else END
        
        # Build graph with interruption capability
        builder = StateGraph(AnalystState)
        builder.add_node("generate_analysts", generate_analysts_node)
        builder.add_node("human_feedback", human_feedback_node)
        
        builder.add_edge(START, "generate_analysts")
        builder.add_edge("generate_analysts", "human_feedback")
        builder.add_conditional_edges("human_feedback", route_human_feedback, ["generate_analysts", END])
        
        return builder.compile(interrupt_before=["human_feedback"], checkpointer=self.checkpointer)
    
    async def execute_analyst_generation(
        self, topic: str, max_analysts: int = 3, thread_id: str = None
    ) -> ExecutionResult:
        """Execute analyst generation with LangGraph features"""
        initial_state = {
            "topic": topic, 
            "max_analysts": max_analysts,
            "human_feedback": None,
            "analysts": [],
            "requires_human_input": False
        }
        
        config = {"configurable": {"thread_id": thread_id or f"analyst_{int(time.time())}"}}
        
        try:
            final_state = await self.analyst_graph.ainvoke(initial_state, config)
            return ExecutionResult.success_result(data={"analysts": final_state["analysts"]})
        except Exception as e:
            return ExecutionResult.error_result(str(e))
```

#### **Week 3 Deliverables**
- [ ] Framework-agnostic research workflows
- [ ] LangGraph orchestrator with human-in-the-loop
- [ ] Checkpointing and state persistence
- [ ] Interview workflow with multi-source search
- [ ] Report generation integration
- [ ] Workflow visualization capabilities

---

### **Phase 4: API Layer Integration (Week 4)**

#### **🌐 REST API Endpoints**
```python
# Target: src/app/api/rest/research_endpoints.py

from fastapi import APIRouter, HTTPException, Depends

router = APIRouter(prefix="/api/v1/research", tags=["research"])

@router.post("/analysts/generate")
async def generate_analysts(
    request: GenerateAnalystsRequest,
    orchestrator: LangGraphResearchOrchestrator = Depends(get_research_orchestrator)
):
    """Generate AI analysts for research topic"""
    result = await orchestrator.execute_analyst_generation(
        topic=request.topic,
        max_analysts=request.max_analysts,
        thread_id=request.session_id
    )
    
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error_message)
    
    return {
        "analysts": result.data["analysts"],
        "session_id": request.session_id,
        "execution_time": result.execution_time
    }

@router.post("/interviews/conduct")
async def conduct_interview(
    request: ConductInterviewRequest,
    orchestrator: LangGraphResearchOrchestrator = Depends(get_research_orchestrator)
):
    """Conduct research interview between analyst and expert"""
    result = await orchestrator.execute_research_interview(
        analyst=request.analyst,
        topic=request.topic,
        max_turns=request.max_turns,
        thread_id=request.session_id
    )
    
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error_message)
    
    return {
        "interview_transcript": result.data["interview_transcript"],
        "total_turns": result.data["total_turns"],
        "sources_used": result.data["sources"]
    }

@router.post("/analysts/{analyst_id}/feedback")
async def provide_human_feedback(
    analyst_id: str,
    feedback: HumanFeedbackRequest,
    orchestrator: LangGraphResearchOrchestrator = Depends(get_research_orchestrator)
):
    """Provide human feedback for analyst refinement"""
    config = {"configurable": {"thread_id": feedback.session_id}}
    
    # Resume workflow with human feedback
    orchestrator.analyst_graph.update_state(
        config, {"human_feedback": feedback.feedback_text}, as_node="human_feedback"
    )
    
    # Continue execution
    final_state = None
    async for event in orchestrator.analyst_graph.astream(None, config):
        final_state = event
    
    return {
        "updated_analysts": final_state.get("analysts", []),
        "session_id": feedback.session_id
    }
```

#### **💻 CLI Interface**
```python
# Target: src/app/api/cli/research_cli.py

import click

@click.group()
def research():
    """Research Assistant CLI"""
    pass

@research.command()
@click.option("--topic", required=True, help="Research topic")
@click.option("--max-analysts", default=3, help="Maximum number of analysts")
@click.option("--interactive", is_flag=True, help="Enable human feedback")
async def generate_analysts(topic: str, max_analysts: int, interactive: bool):
    """Generate AI analysts for research topic"""
    orchestrator = get_research_orchestrator()
    
    result = await orchestrator.execute_analyst_generation(topic=topic, max_analysts=max_analysts)
    
    if result.success:
        analysts = result.data["analysts"]
        click.echo(f"\\n🎯 Generated {len(analysts)} analysts for: {topic}")
        
        for i, analyst in enumerate(analysts, 1):
            click.echo(f"\\n{i}. {analyst['name']}")
            click.echo(f"   Role: {analyst['role']}")
            click.echo(f"   Affiliation: {analyst['affiliation']}")
            click.echo(f"   Description: {analyst['description']}")
        
        if interactive:
            feedback = click.prompt("\\n💬 Provide feedback to refine analysts (or Enter to continue)")
            if feedback.strip():
                # Handle human feedback workflow
                pass
    else:
        click.echo(f"❌ Error: {result.error_message}")

@research.command()
@click.option("--topic", required=True, help="Research topic")
@click.option("--analyst-name", required=True, help="Analyst name for interview")
@click.option("--max-turns", default=3, help="Maximum interview turns")
async def conduct_interview(topic: str, analyst_name: str, max_turns: int):
    """Conduct research interview"""
    orchestrator = get_research_orchestrator()
    
    click.echo(f"🎤 Starting interview on: {topic}")
    click.echo(f"👤 Analyst: {analyst_name}")
    click.echo(f"🔄 Max turns: {max_turns}")
    
    # For CLI, create simplified analyst object
    result = await orchestrator.execute_research_interview(
        analyst={"name": analyst_name, "description": f"Research analyst for {topic}"},
        topic=topic,
        max_turns=max_turns
    )
    
    if result.success:
        click.echo("\\n📝 Interview completed!")
        click.echo("\\n📊 Results:")
        click.echo(f"Total turns: {result.data['total_turns']}")
        click.echo(f"Sources used: {len(result.data['sources'])}")
        click.echo(f"\\n📄 Transcript:\\n{result.data['interview_transcript']}")
    else:
        click.echo(f"❌ Error: {result.error_message}")
```

#### **Week 4 Deliverables**
- [ ] REST API endpoints for all research operations
- [ ] CLI commands for analyst generation and interviews
- [ ] Human feedback integration via API and CLI
- [ ] Request/response models with validation
- [ ] API documentation and examples

---

### **Phase 5: Testing & Integration (Week 5)**

#### **🧪 Unit Tests (Domain Layer)**
```python
# Target: tests/unit/domain/services/test_research_service.py

class TestResearchService:
    
    async def test_generate_analysts_for_topic(self):
        """Test pure domain logic without LangGraph or infrastructure"""
        mock_event_publisher = Mock()
        mock_uow = Mock()
        service = ResearchService(mock_event_publisher)
        
        result = await service.generate_analysts_for_topic(
            mock_uow, "AI Ethics", max_analysts=2
        )
        
        assert len(result) == 2
        assert all(isinstance(analyst, Analyst) for analyst in result)
    
    def test_interview_completion_logic(self):
        """Test business rules for interview completion"""
        service = QuestionGenerationService()
        
        # Test max turns completion
        messages = [Mock(role="expert")] * 3
        assert service.should_end_interview(messages, max_turns=3) == True
        
        # Test thank you phrase completion
        messages = [Mock(content="Thank you so much for your help!")]
        assert service.should_end_interview(messages, max_turns=5) == True
```

#### **🔗 Integration Tests**
```python
# Target: tests/integration/orchestration/test_research_orchestrator.py

class TestLangGraphResearchOrchestrator:
    
    async def test_complete_analyst_generation_workflow(self):
        """Test end-to-end analyst generation with mock services"""
        mock_services = create_mock_research_services()
        orchestrator = LangGraphResearchOrchestrator(mock_services)
        
        result = await orchestrator.execute_analyst_generation(
            topic="Clean Architecture", max_analysts=2
        )
        
        assert result.success == True
        assert "analysts" in result.data
        assert len(result.data["analysts"]) == 2
    
    async def test_human_feedback_interruption(self):
        """Test LangGraph human-in-the-loop functionality"""
        orchestrator = create_test_orchestrator()
        config = {"configurable": {"thread_id": "test_session"}}
        
        # Should pause at human_feedback node
        result = await orchestrator.analyst_graph.ainvoke(
            {"topic": "Test Topic", "max_analysts": 2}, config
        )
        
        state = orchestrator.analyst_graph.get_state(config)
        assert state.next == ("human_feedback",)
        
        # Provide feedback and continue
        orchestrator.analyst_graph.update_state(
            config, {"human_feedback": "Add startup perspective"}, as_node="human_feedback"
        )
        
        final_result = None
        async for event in orchestrator.analyst_graph.astream(None, config):
            final_result = event
        
        assert "analysts" in final_result
```

#### **📊 Performance Tests**
```python
# Target: tests/performance/test_research_performance.py

class TestResearchPerformance:
    
    async def test_analyst_generation_performance(self):
        """Ensure analyst generation completes within acceptable time"""
        orchestrator = create_performance_test_orchestrator()
        
        start_time = time.time()
        result = await orchestrator.execute_analyst_generation(
            topic="Performance Test Topic", max_analysts=3
        )
        execution_time = time.time() - start_time
        
        assert result.success == True
        assert execution_time < 5.0  # Should complete within 5 seconds
    
    async def test_concurrent_interviews(self):
        """Test system handles multiple concurrent interviews"""
        orchestrator = create_performance_test_orchestrator()
        
        # Run 5 concurrent interviews
        tasks = [
            orchestrator.execute_research_interview(
                analyst={"name": f"Analyst {i}"}, topic=f"Topic {i}", max_turns=2
            )
            for i in range(5)
        ]
        
        results = await asyncio.gather(*tasks)
        assert all(r.success for r in results)
```

#### **Week 5 Deliverables**
- [ ] Comprehensive unit test suite (>90% coverage)
- [ ] Integration tests for all workflows
- [ ] Performance benchmarks and optimization
- [ ] End-to-end API testing
- [ ] Documentation and usage examples

---

## 🎯 **Success Metrics**

### **Technical Quality**
- [ ] **Code Coverage**: >90% for domain services, >80% for orchestration
- [ ] **Performance**: Analyst generation <5s, interviews <30s
- [ ] **Reliability**: >99% success rate for valid inputs
- [ ] **Maintainability**: Framework changes require <15% code modification

### **Functional Completeness**
- [ ] **Feature Parity**: All original research-assistant.py functionality preserved
- [ ] **Enhanced Capabilities**: Human-in-the-loop, checkpointing, streaming
- [ ] **API Coverage**: Complete REST and CLI interfaces
- [ ] **Documentation**: Comprehensive usage guides and examples

### **Architecture Compliance**
- [ ] **Domain Purity**: No framework dependencies in domain layer
- [ ] **Interface Adherence**: All external dependencies properly abstracted  
- [ ] **Event-Driven**: Proper domain event publishing and handling
- [ ] **SOLID Principles**: Single responsibility, dependency inversion

## 🚀 **Getting Started**

### **Quick Setup Commands**
```bash
# Install research-specific dependencies
pip install -e ".[research,tavily,wikipedia]"

# Generate analysts via CLI
python -m app.api.cli.research_cli generate-analysts --topic "AI Ethics" --interactive

# Conduct interview via CLI  
python -m app.api.cli.research_cli conduct-interview --topic "AI Ethics" --analyst-name "Dr. Smith"

# Start REST API with research endpoints
python -m app.api.rest.main --enable-research
```

### **Development Workflow**
1. **Domain First**: Implement business logic in domain services
2. **Test Coverage**: Write unit tests for domain layer before infrastructure
3. **Infrastructure**: Implement external service integrations behind abstractions
4. **Orchestration**: Create LangGraph workflows as thin wrappers over domain logic
5. **API Integration**: Build REST and CLI interfaces
6. **End-to-End Testing**: Validate complete workflows with integration tests

## 💡 **Key Benefits**

### **Clean Architecture Advantages**
1. **Testable Business Logic**: Research rules tested independently of frameworks
2. **Framework Independence**: Same logic works with any orchestration framework
3. **Swappable Infrastructure**: Easy to replace OpenAI, Tavily, or add new services
4. **Clear Separation**: Distinct concerns with proper dependency direction

### **Advanced LangGraph Features**
1. **Human-in-the-Loop**: Interactive analyst refinement with workflow interruption
2. **State Management**: Checkpointing, persistence, and recovery capabilities
3. **Multi-Agent Coordination**: Sophisticated analyst-expert interaction patterns
4. **Streaming Support**: Real-time workflow progress and intermediate results

### **Production Readiness**
1. **Error Recovery**: Robust error handling and retry mechanisms
2. **Monitoring**: Comprehensive observability and performance metrics
3. **Scalability**: Handle concurrent research sessions efficiently
4. **Maintainability**: Easy to extend with new research capabilities

---

This plan transforms a 414-line monolithic file into a comprehensive, maintainable, and scalable research system that demonstrates the power of Clean Architecture while showcasing advanced LangGraph capabilities.