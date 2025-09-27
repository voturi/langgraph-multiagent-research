# Research Assistant Integration Plan for Clean Architecture

## 🎯 **Overview**

This document outlines the plan to refactor and integrate the existing `research-assistant.py` file into your clean architecture framework-agnostic project. The goal is to separate concerns properly while maintaining all functionality and adding it as a comprehensive demo of advanced LangGraph capabilities.

## 📊 **Current State Analysis**

### **Existing Code Structure Issues**
- ❌ **Monolithic Design**: 414 lines in a single file
- ❌ **Mixed Concerns**: Business logic, orchestration, and infrastructure combined
- ❌ **Hard Dependencies**: Direct LangGraph, OpenAI, Tavily imports throughout
- ❌ **No Abstraction**: Services directly used in workflow nodes
- ❌ **Tightly Coupled**: Difficult to test or swap components

### **Functional Capabilities (To Preserve)**
- ✅ **Analyst Generation**: AI-driven researcher persona creation
- ✅ **Human-in-the-Loop**: Interactive analyst refinement
- ✅ **Multi-Agent Research**: Analyst-expert interview system
- ✅ **Multi-Source Search**: Web (Tavily) + Wikipedia integration
- ✅ **Report Generation**: Structured research document creation
- ✅ **Checkpointing**: Workflow state persistence and recovery

## 🏗️ **Clean Architecture Integration Strategy**

### **Phase 1: Domain Layer Extraction (Week 1)**

#### **1.1 Domain Entities**
```python
# src/app/domain/models/entities.py - Add these entities

class Analyst(BaseEntity):
    """Research analyst domain entity"""
    id: AnalystId
    name: str
    affiliation: str
    role: str
    description: str
    expertise_areas: List[str] = Field(default_factory=list)
    research_focus: Optional[str] = None
    
    def get_persona_description(self) -> str:
        """Business logic for persona generation"""
        return f"Name: {self.name}\\nRole: {self.role}\\nAffiliation: {self.affiliation}\\nDescription: {self.description}"
    
    def is_suitable_for_topic(self, topic: str) -> bool:
        """Domain logic to determine analyst-topic fit"""
        # Business rules for analyst-topic matching
        pass

class ResearchInterview(BaseEntity):
    """Research interview domain entity"""
    id: InterviewId
    analyst_id: AnalystId
    topic: str
    questions: List[Question] = Field(default_factory=list)
    answers: List[Answer] = Field(default_factory=list)
    context_sources: List[ContextSource] = Field(default_factory=list)
    transcript: Optional[str] = None
    status: InterviewStatus = InterviewStatus.PENDING
    max_turns: int = 3
    
    def add_question(self, question: Question) -> None:
        """Add question to interview"""
        self.questions.append(question)
        self.updated_at = datetime.utcnow()
    
    def add_answer(self, answer: Answer) -> None:
        """Add answer to interview"""
        self.answers.append(answer)
        self.updated_at = datetime.utcnow()
    
    def is_complete(self) -> bool:
        """Business rule: determine if interview is complete"""
        return (len(self.answers) >= self.max_turns or 
                any("Thank you so much for your help" in q.content for q in self.questions))

class ResearchReport(BaseEntity):
    """Research report domain entity"""
    id: ReportId
    title: str
    topic: str
    analyst_id: AnalystId
    interview_id: InterviewId
    sections: List[ReportSection] = Field(default_factory=list)
    sources: List[Source] = Field(default_factory=list)
    status: ReportStatus = ReportStatus.DRAFT
    
    def add_section(self, section: ReportSection) -> None:
        """Add section to report"""
        self.sections.append(section)
        self.updated_at = datetime.utcnow()
    
    def calculate_word_count(self) -> int:
        """Business logic for report metrics"""
        return sum(len(section.content.split()) for section in self.sections)
```

#### **1.2 Value Objects**
```python
# src/app/domain/models/value_objects.py - Add these value objects

@dataclass(frozen=True)
class AnalystId:
    value: str
    
    def __post_init__(self):
        if not self.value or len(self.value.strip()) == 0:
            raise ValueError("AnalystId cannot be empty")

@dataclass(frozen=True)
class SearchQuery:
    query: str
    max_results: int = 3
    sources: List[str] = field(default_factory=lambda: ["web", "wikipedia"])
    
    def __post_init__(self):
        if not self.query or len(self.query.strip()) < 3:
            raise ValueError("Search query must be at least 3 characters")

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

class ReportStatus(Enum):
    DRAFT = "draft"
    REVIEW = "review"
    PUBLISHED = "published"
```

#### **1.3 Domain Events**
```python
# src/app/domain/models/events.py - Add research events

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

class AnswerReceived(DomainEvent):
    interview_id: InterviewId
    answer: str
    sources: List[str]

class InterviewCompleted(DomainEvent):
    interview_id: InterviewId
    total_questions: int
    total_sources: int

class ReportGenerated(DomainEvent):
    report_id: ReportId
    interview_id: InterviewId
    word_count: int
```

#### **1.4 Domain Services**
```python
# src/app/domain/services/research_service.py

class ResearchService:
    """Domain service for research business logic"""
    
    def __init__(self, event_publisher: EventPublisher):
        self.event_publisher = event_publisher
    
    async def generate_analysts_for_topic(
        self,
        uow: UnitOfWork,
        topic: str,
        max_analysts: int = 3,
        human_feedback: Optional[str] = None
    ) -> List[Analyst]:
        """Business logic for analyst generation"""
        async with uow:
            # Business rules for analyst creation
            existing_analysts = await uow.analysts.find_by_topic(topic)
            
            if len(existing_analysts) >= max_analysts and not human_feedback:
                return existing_analysts[:max_analysts]
            
            # Create new analysts based on business rules
            analysts = []
            for i in range(max_analysts):
                analyst = Analyst(
                    id=AnalystId(f"analyst_{topic}_{i}"),
                    name=f"Analyst {i+1}",
                    # ... business logic for analyst creation
                )
                analysts.append(analyst)
                await uow.analysts.save(analyst)
            
            await uow.commit()
            
            # Publish events
            for analyst in analysts:
                event = AnalystCreated(
                    aggregate_id=analyst.id,
                    analyst_id=analyst.id,
                    topic=topic,
                    analyst_details={
                        "name": analyst.name,
                        "role": analyst.role,
                        "affiliation": analyst.affiliation
                    }
                )
                await self.event_publisher.publish(event)
            
            return analysts
    
    async def start_research_interview(
        self,
        uow: UnitOfWork,
        analyst: Analyst,
        topic: str,
        max_turns: int = 3
    ) -> ResearchInterview:
        """Business logic for starting interviews"""
        async with uow:
            interview = ResearchInterview(
                id=InterviewId(f"interview_{analyst.id}_{int(time.time())}"),
                analyst_id=analyst.id,
                topic=topic,
                max_turns=max_turns,
                status=InterviewStatus.IN_PROGRESS
            )
            
            await uow.research_interviews.save(interview)
            await uow.commit()
            
            # Publish event
            event = InterviewStarted(
                aggregate_id=interview.id,
                interview_id=interview.id,
                analyst_id=analyst.id,
                topic=topic
            )
            await self.event_publisher.publish(event)
            
            return interview
    
    async def evaluate_interview_completion(
        self,
        interview: ResearchInterview
    ) -> bool:
        """Business logic for interview completion"""
        return interview.is_complete()
    
    async def generate_research_report(
        self,
        uow: UnitOfWork,
        interview: ResearchInterview,
        analyst: Analyst
    ) -> ResearchReport:
        """Business logic for report generation"""
        async with uow:
            report = ResearchReport(
                id=ReportId(f"report_{interview.id}"),
                title=f"Research Report: {interview.topic}",
                topic=interview.topic,
                analyst_id=analyst.id,
                interview_id=interview.id,
                status=ReportStatus.DRAFT
            )
            
            await uow.research_reports.save(report)
            await uow.commit()
            
            return report

# src/app/domain/services/question_generation_service.py

class QuestionGenerationService:
    """Domain service for question generation logic"""
    
    def generate_interview_question(
        self,
        analyst: Analyst,
        conversation_history: List[Message],
        interview_context: InterviewContext
    ) -> str:
        """Business logic for question generation"""
        # Domain rules for question quality
        if len(conversation_history) == 0:
            return f"Hello, I'm {analyst.name}, {analyst.role}. " \\
                   f"I'd like to discuss {interview_context.topic} with you."
        
        # Business rules for follow-up questions
        if len(conversation_history) < interview_context.max_turns:
            return "Can you provide more specific examples about this topic?"
        
        return "Thank you so much for your help!"
    
    def should_end_interview(
        self,
        conversation_history: List[Message],
        max_turns: int
    ) -> bool:
        """Business logic for interview completion"""
        expert_responses = len([m for m in conversation_history 
                               if m.role == "expert"])
        
        if expert_responses >= max_turns:
            return True
        
        last_messages = conversation_history[-2:] if len(conversation_history) >= 2 else []
        return any("Thank you so much for your help" in msg.content 
                  for msg in last_messages)
```

### **Phase 2: Infrastructure Layer Implementation (Week 2)**

#### **2.1 Repository Interfaces**
```python
# src/app/domain/interfaces/repositories.py - Add research repositories

class AnalystRepository(ABC):
    @abstractmethod
    async def save(self, analyst: Analyst) -> None:
        pass
    
    @abstractmethod
    async def find_by_id(self, analyst_id: AnalystId) -> Optional[Analyst]:
        pass
    
    @abstractmethod
    async def find_by_topic(self, topic: str) -> List[Analyst]:
        pass
    
    @abstractmethod
    async def find_by_expertise(self, expertise: str) -> List[Analyst]:
        pass

class ResearchInterviewRepository(ABC):
    @abstractmethod
    async def save(self, interview: ResearchInterview) -> None:
        pass
    
    @abstractmethod
    async def find_by_id(self, interview_id: InterviewId) -> Optional[ResearchInterview]:
        pass
    
    @abstractmethod
    async def find_by_analyst(self, analyst_id: AnalystId) -> List[ResearchInterview]:
        pass

class ResearchReportRepository(ABC):
    @abstractmethod
    async def save(self, report: ResearchReport) -> None:
        pass
    
    @abstractmethod 
    async def find_by_id(self, report_id: ReportId) -> Optional[ResearchReport]:
        pass
```

#### **2.2 External Service Interfaces**
```python
# src/app/domain/interfaces/services.py - Add research service interfaces

class AnalystGenerationService(ABC):
    """Abstract interface for AI analyst generation"""
    
    @abstractmethod
    async def generate_analysts(
        self,
        topic: str,
        max_analysts: int,
        human_feedback: Optional[str] = None
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
    async def generate_question(
        self,
        analyst_persona: str,
        conversation_history: List[Dict[str, Any]]
    ) -> str:
        pass
    
    @abstractmethod
    async def generate_answer(
        self,
        question: str,
        context: List[str],
        analyst_focus: str
    ) -> str:
        pass

class ReportGenerationService(ABC):
    """Abstract interface for report generation"""
    
    @abstractmethod
    async def generate_report_section(
        self,
        interview_transcript: str,
        context_sources: List[str],
        analyst_focus: str
    ) -> str:
        pass
```

#### **2.3 Infrastructure Implementations**
```python
# src/app/infrastructure/services/openai_research_service.py

class OpenAIAnalystGenerationService(AnalystGenerationService):
    """OpenAI implementation for analyst generation"""
    
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
    
    async def generate_analysts(
        self,
        topic: str,
        max_analysts: int,
        human_feedback: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Use LLM service to generate analysts - infrastructure concern"""
        
        prompt = self._build_analyst_prompt(topic, max_analysts, human_feedback)
        
        result = await self.llm_service.generate_structured_response(
            messages=[{"role": "system", "content": prompt}],
            response_schema=PerspectivesSchema,
            model="gpt-4o",
            temperature=0
        )
        
        return [analyst.dict() for analyst in result.analysts]
    
    def _build_analyst_prompt(self, topic: str, max_analysts: int, feedback: Optional[str]) -> str:
        """Infrastructure-specific prompt building"""
        return f"""You are tasked with creating a set of AI analyst personas...
        Topic: {topic}
        Max analysts: {max_analysts}
        Feedback: {feedback or 'None'}"""

# src/app/infrastructure/services/tavily_search_service.py

class TavilySearchService(SearchService):
    """Tavily implementation for web search"""
    
    def __init__(self, api_key: str):
        self.search_tool = TavilySearchResults(max_results=10)
    
    async def search_web(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """Tavily-specific search implementation"""
        results = await self.search_tool.ainvoke(query)
        return results[:max_results]
    
    async def search_wikipedia(self, query: str, max_docs: int = 2) -> List[Dict[str, Any]]:
        """Wikipedia search via langchain"""
        loader = WikipediaLoader(query=query, load_max_docs=max_docs)
        docs = await loader.aload()
        
        return [
            {
                "content": doc.page_content,
                "source": doc.metadata.get("source", ""),
                "page": doc.metadata.get("page", "")
            }
            for doc in docs
        ]

# src/app/infrastructure/repositories/memory_research_repository.py

class MemoryAnalystRepository(AnalystRepository):
    """In-memory implementation for development/testing"""
    
    def __init__(self):
        self._analysts: Dict[str, Analyst] = {}
        self._by_topic: Dict[str, List[AnalystId]] = defaultdict(list)
    
    async def save(self, analyst: Analyst) -> None:
        self._analysts[analyst.id.value] = analyst
        # Index by topic (if we have topic context)
    
    async def find_by_id(self, analyst_id: AnalystId) -> Optional[Analyst]:
        return self._analysts.get(analyst_id.value)
    
    async def find_by_topic(self, topic: str) -> List[Analyst]:
        analyst_ids = self._by_topic.get(topic, [])
        return [self._analysts[aid.value] for aid in analyst_ids 
                if aid.value in self._analysts]
```

### **Phase 3: Orchestration Layer Integration (Week 3)**

#### **3.1 Research Workflow Orchestrator**
```python
# src/app/orchestration/workflows/research_workflow.py

class ResearchWorkflow(BaseWorkflow):
    """Framework-agnostic research workflow"""
    
    def __init__(
        self,
        research_service: ResearchService,
        question_service: QuestionGenerationService,
        analyst_generation_service: AnalystGenerationService,
        search_service: SearchService,
        qa_service: QuestionAnswerService,
        report_service: ReportGenerationService
    ):
        self.research_service = research_service
        self.question_service = question_service  
        self.analyst_generation_service = analyst_generation_service
        self.search_service = search_service
        self.qa_service = qa_service
        self.report_service = report_service
    
    async def generate_analysts_workflow(
        self,
        uow: UnitOfWork,
        topic: str,
        max_analysts: int = 3,
        human_feedback: Optional[str] = None
    ) -> List[Analyst]:
        """Pure business logic - framework agnostic"""
        
        # Use domain service for business logic
        analysts = await self.research_service.generate_analysts_for_topic(
            uow, topic, max_analysts, human_feedback
        )
        
        return analysts
    
    async def conduct_interview_workflow(
        self,
        uow: UnitOfWork,
        analyst: Analyst,
        topic: str,
        max_turns: int = 3
    ) -> ResearchReport:
        """Pure business logic for interview workflow"""
        
        # Start interview using domain service
        interview = await self.research_service.start_research_interview(
            uow, analyst, topic, max_turns
        )
        
        # Interview loop (business logic)
        conversation_history = []
        
        for turn in range(max_turns):
            # Generate question (domain logic)
            question = self.question_service.generate_interview_question(
                analyst, 
                conversation_history, 
                InterviewContext(topic=topic, analyst_persona=analyst.get_persona_description())
            )
            
            # Search for context (infrastructure via interface)
            search_results = await self.search_service.search_web(question)
            
            # Generate answer (infrastructure via interface)
            answer = await self.qa_service.generate_answer(
                question, search_results, analyst.description
            )
            
            # Update conversation (domain logic)
            conversation_history.extend([
                {"role": "analyst", "content": question},
                {"role": "expert", "content": answer}
            ])
            
            # Check completion (domain logic)
            if self.question_service.should_end_interview(conversation_history, max_turns):
                break
        
        # Generate report (domain logic + infrastructure)
        transcript = "\\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history])
        report = await self.research_service.generate_research_report(
            uow, interview, analyst
        )
        
        return report

# src/app/orchestration/langgraph/research_orchestrator.py

class LangGraphResearchOrchestrator(LangGraphOrchestrator):
    """LangGraph-specific implementation for research workflows"""
    
    def __init__(self, research_workflow: ResearchWorkflow, **kwargs):
        super().__init__(**kwargs)
        self.research_workflow = research_workflow
        self.analyst_graph = self._build_analyst_graph()
        self.interview_graph = self._build_interview_graph()
    
    def _build_analyst_graph(self) -> StateGraph:
        """Build LangGraph for analyst generation"""
        
        class AnalystGenerationState(TypedDict):
            topic: str
            max_analysts: int
            human_feedback: Optional[str]
            analysts: List[Dict[str, Any]]
            requires_human_input: bool
        
        # LangGraph nodes (thin wrappers around domain workflow)
        def generate_analysts_node(state: AnalystGenerationState) -> AnalystGenerationState:
            # Delegate to domain workflow
            analysts = await self.research_workflow.generate_analysts_workflow(
                self.uow,
                state["topic"],
                state["max_analysts"], 
                state.get("human_feedback")
            )
            
            return {
                "analysts": [analyst.dict() for analyst in analysts],
                "requires_human_input": state.get("human_feedback") is None
            }
        
        def human_feedback_node(state: AnalystGenerationState) -> AnalystGenerationState:
            # LangGraph-specific: pause for human input
            return state  # Pauses here due to interrupt_before
        
        def route_human_feedback(state: AnalystGenerationState) -> str:
            if state.get("human_feedback"):
                return "generate_analysts"
            return END
        
        # Build graph
        builder = StateGraph(AnalystGenerationState)
        builder.add_node("generate_analysts", generate_analysts_node)
        builder.add_node("human_feedback", human_feedback_node)
        
        builder.add_edge(START, "generate_analysts")
        builder.add_edge("generate_analysts", "human_feedback")
        builder.add_conditional_edges(
            "human_feedback", 
            route_human_feedback,
            ["generate_analysts", END]
        )
        
        return builder.compile(
            interrupt_before=["human_feedback"],
            checkpointer=self.checkpointer
        )
    
    def _build_interview_graph(self) -> StateGraph:
        """Build LangGraph for research interviews"""
        
        class InterviewState(MessagesState):
            analyst: Dict[str, Any]
            topic: str
            max_turns: int
            context_sources: List[str]
            current_turn: int
            interview_complete: bool
        
        # LangGraph nodes (thin wrappers)
        def ask_question_node(state: InterviewState) -> InterviewState:
            # Delegate to domain service
            question = await self.research_workflow.question_service.generate_interview_question(
                # Convert dict to analyst object for domain service
                Analyst(**state["analyst"]),
                state["messages"],
                InterviewContext(topic=state["topic"])
            )
            
            return {"messages": [AIMessage(content=question, name="analyst")]}
        
        def search_context_node(state: InterviewState) -> InterviewState:
            # Get last question for search
            last_question = state["messages"][-1].content
            
            # Use infrastructure service via domain workflow
            search_results = await self.research_workflow.search_service.search_web(last_question)
            
            formatted_context = self._format_search_results(search_results)
            return {"context_sources": [formatted_context]}
        
        def generate_answer_node(state: InterviewState) -> InterviewState:
            last_question = state["messages"][-1].content
            context = state["context_sources"]
            
            # Use infrastructure service via domain workflow
            answer = await self.research_workflow.qa_service.generate_answer(
                last_question, context, state["analyst"]["description"]
            )
            
            return {"messages": [AIMessage(content=answer, name="expert")]}
        
        def check_completion_node(state: InterviewState) -> InterviewState:
            # Use domain service for business logic
            is_complete = self.research_workflow.question_service.should_end_interview(
                state["messages"], state["max_turns"]
            )
            
            return {
                "interview_complete": is_complete,
                "current_turn": state.get("current_turn", 0) + 1
            }
        
        def route_interview(state: InterviewState) -> str:
            if state.get("interview_complete", False):
                return "generate_report"
            return "ask_question"
        
        # Build graph
        builder = StateGraph(InterviewState)
        builder.add_node("ask_question", ask_question_node)
        builder.add_node("search_context", search_context_node)
        builder.add_node("generate_answer", generate_answer_node)
        builder.add_node("check_completion", check_completion_node)
        builder.add_node("generate_report", self._generate_report_node)
        
        builder.add_edge(START, "ask_question")
        builder.add_edge("ask_question", "search_context")
        builder.add_edge("search_context", "generate_answer")
        builder.add_edge("generate_answer", "check_completion")
        builder.add_conditional_edges(
            "check_completion",
            route_interview,
            ["ask_question", "generate_report"]
        )
        builder.add_edge("generate_report", END)
        
        return builder.compile(checkpointer=self.checkpointer)
    
    async def execute_analyst_generation(
        self,
        topic: str,
        max_analysts: int = 3,
        thread_id: str = None
    ) -> ExecutionResult:
        """Execute analyst generation workflow"""
        
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
            
            return ExecutionResult.success_result(
                data={"analysts": final_state["analysts"]},
                execution_time=0.0  # Could track this
            )
        except Exception as e:
            return ExecutionResult.error_result(str(e))
    
    async def execute_research_interview(
        self,
        analyst: Dict[str, Any],
        topic: str,
        max_turns: int = 3,
        thread_id: str = None
    ) -> ExecutionResult:
        """Execute research interview workflow"""
        
        initial_state = {
            "analyst": analyst,
            "topic": topic,
            "max_turns": max_turns,
            "messages": [HumanMessage(content=f"Let's discuss {topic}")],
            "context_sources": [],
            "current_turn": 0,
            "interview_complete": False
        }
        
        config = {"configurable": {"thread_id": thread_id or f"interview_{int(time.time())}"}}
        
        try:
            final_state = await self.interview_graph.ainvoke(initial_state, config)
            
            return ExecutionResult.success_result(
                data={
                    "interview_transcript": self._format_transcript(final_state["messages"]),
                    "total_turns": final_state.get("current_turn", 0),
                    "sources": final_state.get("context_sources", [])
                }
            )
        except Exception as e:
            return ExecutionResult.error_result(str(e))
```

### **Phase 4: API Layer Integration (Week 4)**

#### **4.1 REST API Endpoints**
```python
# src/app/api/rest/research_endpoints.py

from fastapi import APIRouter, HTTPException, Depends
from ...orchestration.langgraph.research_orchestrator import LangGraphResearchOrchestrator

router = APIRouter(prefix="/api/v1/research", tags=["research"])

@router.post("/analysts/generate")
async def generate_analysts(
    request: GenerateAnalystsRequest,
    orchestrator: LangGraphResearchOrchestrator = Depends(get_research_orchestrator)
):
    """Generate AI analysts for a research topic"""
    
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
    """Conduct research interview with an analyst"""
    
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
        "sources": result.data["sources"]
    }

@router.post("/analysts/{analyst_id}/feedback")
async def provide_human_feedback(
    analyst_id: str,
    feedback: HumanFeedbackRequest,
    orchestrator: LangGraphResearchOrchestrator = Depends(get_research_orchestrator)
):
    """Provide human feedback for analyst refinement"""
    
    # Resume workflow with human feedback
    config = {"configurable": {"thread_id": feedback.session_id}}
    
    # Update state with human feedback
    orchestrator.analyst_graph.update_state(
        config, 
        {"human_feedback": feedback.feedback_text},
        as_node="human_feedback"
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

#### **4.2 CLI Interface**
```python
# src/app/api/cli/research_cli.py

import click
from ...orchestration.langgraph.research_orchestrator import LangGraphResearchOrchestrator

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
    
    # Generate initial analysts
    result = await orchestrator.execute_analyst_generation(
        topic=topic,
        max_analysts=max_analysts
    )
    
    if result.success:
        analysts = result.data["analysts"]
        click.echo(f"\\n🎯 Generated {len(analysts)} analysts for: {topic}")
        
        for i, analyst in enumerate(analysts, 1):
            click.echo(f"\\n{i}. {analyst['name']}")
            click.echo(f"   Role: {analyst['role']}")
            click.echo(f"   Affiliation: {analyst['affiliation']}")
            click.echo(f"   Description: {analyst['description']}")
        
        if interactive:
            feedback = click.prompt("\\n💬 Provide feedback to refine analysts (or press Enter to continue)")
            if feedback.strip():
                # Handle human feedback...
                pass
    else:
        click.echo(f"❌ Error: {result.error_message}")

@research.command()
@click.option("--topic", required=True, help="Research topic")
@click.option("--analyst-name", required=True, help="Analyst name")
@click.option("--max-turns", default=3, help="Maximum interview turns")
async def conduct_interview(topic: str, analyst_name: str, max_turns: int):
    """Conduct research interview"""
    
    orchestrator = get_research_orchestrator()
    
    # For CLI, we'd need to load or create an analyst
    # This would integrate with the domain services
    
    click.echo(f"🎤 Starting interview on: {topic}")
    click.echo(f"👤 Analyst: {analyst_name}")
    click.echo(f"🔄 Max turns: {max_turns}")
    
    # Execute interview...
    result = await orchestrator.execute_research_interview(
        analyst={"name": analyst_name},  # Simplified for CLI
        topic=topic,
        max_turns=max_turns
    )
    
    if result.success:
        click.echo("\\n📝 Interview completed!")
        click.echo(f"Transcript: {result.data['interview_transcript']}")
    else:
        click.echo(f"❌ Error: {result.error_message}")
```

### **Phase 5: Testing & Integration (Week 5)**

#### **5.1 Domain Service Tests**
```python
# tests/unit/domain/services/test_research_service.py

class TestResearchService:
    
    def test_generate_analysts_for_topic(self):
        # Test pure domain logic without LangGraph or OpenAI
        mock_event_publisher = Mock()
        service = ResearchService(mock_event_publisher)
        
        # Test business rules
        topic = "AI Ethics"
        max_analysts = 2
        
        # Mock UoW
        mock_uow = Mock()
        
        result = await service.generate_analysts_for_topic(
            mock_uow, topic, max_analysts
        )
        
        assert len(result) == max_analysts
        assert all(isinstance(analyst, Analyst) for analyst in result)
    
    def test_interview_completion_logic(self):
        # Test business rules for interview completion
        service = QuestionGenerationService()
        
        # Test max turns completion
        messages = [Mock(role="expert")] * 3
        assert service.should_end_interview(messages, max_turns=3) == True
        
        # Test thank you completion
        messages = [
            Mock(content="Some question"), 
            Mock(content="Thank you so much for your help!")
        ]
        assert service.should_end_interview(messages, max_turns=5) == True
```

#### **5.2 Integration Tests**
```python
# tests/integration/orchestration/test_research_orchestrator.py

class TestLangGraphResearchOrchestrator:
    
    async def test_analyst_generation_workflow(self):
        # Test complete LangGraph workflow with mock infrastructure
        mock_services = create_mock_research_services()
        orchestrator = LangGraphResearchOrchestrator(mock_services)
        
        result = await orchestrator.execute_analyst_generation(
            topic="Test Topic",
            max_analysts=2
        )
        
        assert result.success == True
        assert "analysts" in result.data
        assert len(result.data["analysts"]) == 2
    
    async def test_human_in_loop_functionality(self):
        # Test LangGraph human feedback interruption
        orchestrator = create_test_orchestrator()
        
        # Start workflow
        config = {"configurable": {"thread_id": "test_123"}}
        
        # Should pause at human_feedback node
        result = await orchestrator.analyst_graph.ainvoke(
            {"topic": "Test", "max_analysts": 2}, 
            config
        )
        
        state = orchestrator.analyst_graph.get_state(config)
        assert state.next == ("human_feedback",)
        
        # Provide feedback and continue
        orchestrator.analyst_graph.update_state(
            config, 
            {"human_feedback": "Add more technical expertise"}, 
            as_node="human_feedback"
        )
        
        # Continue and complete
        final_result = None
        async for event in orchestrator.analyst_graph.astream(None, config):
            final_result = event
            
        assert "analysts" in final_result
```

## 🎯 **Integration Benefits**

### **Clean Architecture Advantages**
1. **Testable Business Logic**: Domain services tested independently of LangGraph
2. **Framework Independence**: Research logic works with any orchestrator
3. **Swappable Infrastructure**: Easy to replace OpenAI, Tavily, etc.
4. **Clear Separation**: Orchestration vs. business logic vs. infrastructure

### **LangGraph Enhancement**
1. **Advanced Workflows**: Multi-agent coordination, human-in-the-loop
2. **State Management**: Checkpointing, interruption, resumption
3. **Streaming**: Real-time workflow progress
4. **Visualization**: Workflow graph visualization

### **Scalability Features**
1. **Multi-Agent Research**: Parallel analyst interviews
2. **Batch Processing**: Multiple topics simultaneously
3. **Persistent State**: Long-running research projects
4. **Quality Controls**: Validation and error recovery

## 📈 **Success Metrics**

### **Technical Quality**
- [ ] **Code Coverage**: >90% for domain services
- [ ] **Performance**: <5s for analyst generation, <30s for interviews
- [ ] **Reliability**: >99% success rate for valid inputs
- [ ] **Maintainability**: Framework changes require <15% code modification

### **Functional Completeness**  
- [ ] **Feature Parity**: All original functionality preserved
- [ ] **Enhanced Capabilities**: Human-in-the-loop, checkpointing, streaming
- [ ] **API Coverage**: REST and CLI interfaces complete
- [ ] **Documentation**: Comprehensive guides and examples

### **Architecture Compliance**
- [ ] **Domain Purity**: No framework dependencies in domain layer
- [ ] **Interface Adherence**: All external dependencies abstracted
- [ ] **Event-Driven**: Proper domain event publishing
- [ ] **SOLID Principles**: Single responsibility, dependency inversion

## 🚀 **Getting Started**

### **Quick Setup**
```bash
# Install research-specific dependencies
pip install -e ".[research,tavily,wikipedia]"

# Run analyst generation
python -m app.api.cli.research_cli generate-analysts --topic "AI Ethics" --interactive

# Conduct interview
python -m app.api.cli.research_cli conduct-interview --topic "AI Ethics" --analyst-name "Dr. Smith"

# Start REST API with research endpoints
python -m app.api.rest.main --enable-research
```

### **Development Workflow**
1. **Domain First**: Implement business logic in domain services
2. **Test Coverage**: Write comprehensive unit tests for domain layer
3. **Infrastructure**: Implement external service integrations
4. **Orchestration**: Create LangGraph workflows as thin wrappers
5. **API Integration**: Add REST/CLI interfaces
6. **End-to-End Testing**: Validate complete workflows

---

This integration plan transforms the monolithic research-assistant.py into a comprehensive demonstration of Clean Architecture principles while preserving all functionality and adding advanced LangGraph capabilities. The result will be a maintainable, testable, and scalable research system that showcases the power of proper architectural design.