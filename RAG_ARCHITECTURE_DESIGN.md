# RAG Architecture Design - Enterprise Knowledge Base Integration

## 🎯 **Overview**

This design document outlines the RAG (Retrieval-Augmented Generation) architecture for integrating PDF-based enterprise knowledge bases into the existing LangGraph Research Agent, while maintaining clean architecture principles.

## 🏗️ **Architecture Overview**

```
┌─────────────────────────────────────────────────┐
│               RAG Research Graph                │
│            (New Implementation)                 │
├─────────────────────────────────────────────────┤
│    PDF Ingestion │ Vector Search │ Context      │
│      Pipeline    │    Service    │  Assembly    │
├─────────────────────────────────────────────────┤
│              Domain Services                    │
│     (Enhanced with RAG capabilities)           │
├─────────────────────────────────────────────────┤
│             Infrastructure Layer                │
│  OpenAI │ ChromaDB │ PDF Parser │ Embeddings   │
└─────────────────────────────────────────────────┘
```

## 📚 **Domain Layer Extensions**

### **New Domain Entities**

```python
# Enhanced domain entities for RAG support
class DocumentSource(BaseEntity):
    id: DocumentSourceId
    file_path: str
    file_name: str
    content_type: str  # PDF, TXT, DOCX
    upload_date: datetime
    processing_status: ProcessingStatus
    total_chunks: int
    metadata: Dict[str, Any]

class DocumentChunk(BaseEntity):
    id: ChunkId
    source_id: DocumentSourceId
    chunk_index: int
    content: str
    embedding: Optional[List[float]]
    page_number: Optional[int]
    section_header: Optional[str]
    metadata: Dict[str, Any]

class RAGSearchResult(ValueObject):
    chunk_id: ChunkId
    content: str
    similarity_score: float
    source_document: str
    page_number: Optional[int]
    section_header: Optional[str]
```

### **New Domain Services**

```python
class DocumentProcessingService:
    """Domain service for document processing business logic"""
    
    async def process_document(self, file_path: str) -> DocumentSource:
        """Process document and create chunks with business rules"""
        
    def should_process_chunk(self, chunk_content: str) -> bool:
        """Business rules for chunk inclusion"""
        
    def calculate_optimal_chunk_size(self, document_type: str) -> int:
        """Business logic for chunking strategy"""

class RAGSearchService:
    """Domain service for RAG search business logic"""
    
    async def search_knowledge_base(
        self, 
        query: str, 
        max_results: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[RAGSearchResult]:
        """Search RAG knowledge base with business rules"""
        
    def rank_search_results(self, results: List[RAGSearchResult]) -> List[RAGSearchResult]:
        """Apply business rules for result ranking"""
```

## 🔧 **Infrastructure Layer Implementation**

### **PDF Processing Service**

```python
class PDFProcessingService:
    """Infrastructure service for PDF text extraction"""
    
    async def extract_text_from_pdf(self, file_path: str) -> Dict[str, Any]:
        """Extract text with page numbers and structure"""
        
    async def chunk_document(
        self, 
        content: str, 
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> List[str]:
        """Split document into overlapping chunks"""
```

### **Vector Storage Service**

```python
class ChromaDBVectorService:
    """ChromaDB implementation for vector storage"""
    
    async def store_document_chunks(
        self, 
        chunks: List[DocumentChunk]
    ) -> List[str]:
        """Store chunks with embeddings in ChromaDB"""
        
    async def similarity_search(
        self, 
        query_embedding: List[float],
        k: int = 5
    ) -> List[Tuple[str, float]]:
        """Perform similarity search in vector database"""
```

### **Embedding Service**

```python
class OpenAIEmbeddingService:
    """OpenAI embeddings for semantic search"""
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI text-embedding-3-small"""
        
    async def generate_batch_embeddings(
        self, 
        texts: List[str]
    ) -> List[List[float]]:
        """Batch embedding generation for efficiency"""
```

## 📊 **New RAG-Powered Workflow**

### **Enhanced Research Workflow**

```python
class RAGResearchWorkflow(ResearchWorkflow):
    """Extended workflow with RAG capabilities"""
    
    def __init__(
        self,
        # ... existing parameters
        rag_search_service: RAGSearchService,
        document_processing_service: DocumentProcessingService,
        pdf_processing_service: PDFProcessingService,
        vector_service: ChromaDBVectorService,
        embedding_service: OpenAIEmbeddingService,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.rag_search_service = rag_search_service
        self.document_processing_service = document_processing_service
        # ... other RAG services
    
    async def _search_for_context(self, messages: List[Dict[str, Any]]) -> str:
        """Override to use RAG instead of web search"""
        try:
            # Generate search query using existing LLM service
            search_query = await self._generate_search_query(messages)
            
            # Search RAG knowledge base instead of web/Wikipedia
            rag_results = await self.rag_search_service.search_knowledge_base(
                query=search_query,
                max_results=5,
                similarity_threshold=0.7
            )
            
            # Format results for context (similar to existing format)
            return self._format_rag_results_for_context(rag_results)
            
        except Exception as e:
            logger.error(f"RAG search failed: {e}")
            return "RAG search context unavailable"
    
    async def ingest_pdf_document(self, file_path: str) -> DocumentSource:
        """New method to ingest PDF into knowledge base"""
        return await self.document_processing_service.process_document(file_path)
```

## 🚀 **New LangGraph Implementation**

### **RAG Research Orchestrator**

```python
class RAGResearchOrchestrator:
    """New orchestrator specifically for RAG-powered research"""
    
    def __init__(self, rag_research_workflow: RAGResearchWorkflow):
        self.workflow = rag_research_workflow
        self.checkpointer = MemorySaver()
    
    def build_graph(self) -> CompiledGraph:
        """Build RAG-powered research graph"""
        
        # Same nodes as existing graph, but with RAG search
        workflow = StateGraph(ResearchState)
        
        # Standard research nodes (reuse existing)
        research_nodes = ResearchNodes(self.workflow)
        
        # Add document ingestion node (NEW)
        workflow.add_node("ingest_documents", self._ingest_documents_node)
        
        # Standard flow
        workflow.add_node("create_project", research_nodes.create_project_node)
        workflow.add_node("generate_analysts", research_nodes.generate_analysts_node)
        workflow.add_node("conduct_interview", research_nodes.conduct_interview_node)
        # ... etc
        
        # Enhanced flow with document ingestion option
        workflow.add_edge(START, "check_documents")
        workflow.add_conditional_edges(
            "check_documents",
            self._route_document_processing,
            {
                "ingest_documents": "ingest_documents",
                "start_research": "create_project"
            }
        )
        workflow.add_edge("ingest_documents", "create_project")
        # ... rest of graph
        
        return workflow.compile(checkpointer=self.checkpointer)
```

## 📁 **Directory Structure**

```
src/app/
├── domain/
│   ├── entities/
│   │   ├── research.py           # Existing entities
│   │   └── rag.py               # NEW: RAG domain entities
│   ├── services/
│   │   ├── research_service.py   # Existing service
│   │   ├── rag_search_service.py # NEW: RAG domain service
│   │   └── document_service.py   # NEW: Document processing service
│   └── interfaces/
│       ├── repositories.py       # Existing interfaces
│       └── rag_services.py      # NEW: RAG service interfaces
├── infrastructure/
│   └── services/
│       ├── tavily_service.py     # Existing web search
│       ├── wikipedia_service.py  # Existing Wikipedia
│       ├── pdf_service.py       # NEW: PDF processing
│       ├── chromadb_service.py  # NEW: Vector storage
│       └── embedding_service.py  # NEW: OpenAI embeddings
├── orchestration/
│   └── langgraph/
│       ├── research_orchestrator.py    # Existing orchestrator
│       └── rag_research_orchestrator.py # NEW: RAG orchestrator
└── application/
    └── workflows/
        ├── research_workflow.py         # Existing workflow
        └── rag_research_workflow.py     # NEW: RAG workflow
```

## 🔄 **Integration Points**

### **Existing System Compatibility**

1. **Same State Schema**: Use existing `ResearchState` for compatibility
2. **Same Domain Services**: Reuse `ResearchService`, `AnalystService`, etc.
3. **Same Entry Point Pattern**: Create `rag_research_entry.py` similar to existing
4. **Same CLI Interface**: Extend existing CLI with RAG commands

### **New Capabilities**

1. **Document Ingestion**: `python -m app.cli ingest-pdf --file document.pdf`
2. **RAG Research**: `python -m app.cli research-rag --topic "strategy pattern"`
3. **Knowledge Base Status**: `python -m app.cli kb-status`

## 🛠️ **Implementation Dependencies**

### **New Dependencies** (add to pyproject.toml)

```toml
# RAG-specific dependencies
dependencies = [
    # ... existing dependencies
    "chromadb>=0.5.0",              # Vector database
    "pypdf2>=3.0.1",                # PDF text extraction
    "sentence-transformers>=2.2.2",  # Alternative embeddings
    "python-multipart>=0.0.6",      # File upload support
]
```

### **Configuration Extensions**

```bash
# New environment variables
CHROMA_DB_PATH=./data/chroma_db
RAG_CHUNK_SIZE=1000
RAG_CHUNK_OVERLAP=200
RAG_SIMILARITY_THRESHOLD=0.7
RAG_MAX_RESULTS=5
```

## 🧪 **Testing Strategy**

### **Unit Tests**
- Domain service tests with mock infrastructure
- RAG search business logic validation
- Document processing rule testing

### **Integration Tests**
- End-to-end PDF ingestion workflow
- RAG search with real ChromaDB
- Compatibility with existing graph

### **Performance Tests**
- Document ingestion speed
- Search response times
- Memory usage with large knowledge bases

## 🎯 **Success Metrics**

- **Processing Speed**: <30s for PDF ingestion
- **Search Accuracy**: >80% relevant results
- **Response Time**: <2s for RAG search queries
- **Storage Efficiency**: <50MB per 100-page document
- **Architecture Compliance**: 100% clean architecture adherence

## 🚀 **Rollout Plan**

### **Phase 1**: Core Infrastructure (Week 1)
- PDF processing service
- Vector storage with ChromaDB
- Embedding service integration

### **Phase 2**: Domain Integration (Week 2)
- RAG domain entities and services
- Enhanced workflow implementation
- Unit test coverage

### **Phase 3**: LangGraph Integration (Week 3)
- New RAG orchestrator
- Graph node implementations
- Integration testing

### **Phase 4**: User Interface (Week 4)
- CLI commands for document ingestion
- RAG research workflow
- Documentation and examples

This design maintains your existing clean architecture while adding powerful RAG capabilities that can search your enterprise PDF knowledge base instead of the web!