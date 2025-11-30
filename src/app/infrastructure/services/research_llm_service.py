"""Research-specific LLM service for analyst creation and interview management."""

import logging
import os
import time
from typing import Any, Dict, List, Optional

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    get_buffer_string,
)

from ...domain.entities.research import Analyst, Perspectives, SearchQuery
from ...utils.llm_trace_logger import get_trace_logger
from .openai_service import OpenAIService

logger = logging.getLogger(__name__)


class ResearchLLMService(OpenAIService):
    """Extended LLM service specifically for research assistant functionality."""

    # Analyst creation instructions
    ANALYST_INSTRUCTIONS = """You are tasked with creating a set of AI analyst personas. Follow these instructions carefully:
1. First, review the research topic: {topic}        
2. Examine any editorial feedback that has been optionally provided to guide creation of the analysts: 
{human_analyst_feedback}
3. Determine the most interesting themes based upon documents and / or feedback above.
4. Pick the top {max_analysts} themes.
5. Assign one analyst to each theme."""

    # Interview question generation instructions
    QUESTION_INSTRUCTIONS = """You are an analyst tasked with interviewing an expert to learn about a specific topic. 

Your goal is boil down to interesting and specific insights related to your topic.
1. Interesting: Insights that people will find surprising or non-obvious.       
2. Specific: Insights that avoid generalities and include specific examples from the expert.
Here is your topic of focus and set of goals: {goals} 
Begin by introducing yourself using a name that fits your persona, and then ask your question.
Continue to ask questions to drill down and refine your understanding of the topic.        
When you are satisfied with your understanding, complete the interview with: "Thank you so much for your help!"
Remember to stay in character throughout your response, reflecting the persona and goals provided to you."""

    # Search query generation instructions
    SEARCH_INSTRUCTIONS = """You will be given a conversation between an analyst and an expert. 

Your goal is to generate a well-structured query for use in retrieval and / or web-search related to the conversation.
        
First, analyze the full conversation.

Pay particular attention to the final question posed by the analyst.

Convert this final question into a well-structured web search query"""

    # Expert answer instructions
    ANSWER_INSTRUCTIONS = """You are an expert being interviewed by an analyst.

Here is analyst area of focus: {goals}. 
        
You goal is to answer a question posed by the interviewer.

To answer question, use this context:
        
{context}

When answering questions, follow these guidelines:
        
1. Use only the information provided in the context. 
        
2. Do not introduce external information or make assumptions beyond what is explicitly stated in the context.

3. The context contain sources at the topic of each individual document.

4. Include these sources your answer next to any relevant statements. For example, for source # 1 use [1]. 

5. List your sources in order at the bottom of your answer. [1] Source 1, [2] Source 2, etc
        
6. If the source is: <Document source="assistant/docs/llama3_1.pdf" page="7"/> then just list: 
        
[1] assistant/docs/llama3_1.pdf, page 7 
        
And skip the addition of the brackets as well as the Document source preamble in your citation."""

    # Section writing instructions
    SECTION_WRITER_INSTRUCTIONS = """You are an expert technical writer. 
            
Your task is to create a short, easily digestible section of a report based on a set of source documents.

1. Analyze the content of the source documents: 
- The name of each source document is at the start of the document, with the <Document tag.
        
2. Create a report structure using markdown formatting:
- Use ## for the section title
- Use ### for sub-section headers
        
3. Write the report following this structure:
a. Title (## header)
b. Summary (### header)
c. Sources (### header)

4. Make your title engaging based upon the focus area of the analyst: 
{focus}

5. For the summary section:
- Set up summary with general background / context related to the focus area of the analyst
- Emphasize what is novel, interesting, or surprising about insights gathered from the interview
- Create a numbered list of source documents, as you use them
- Do not mention the names of interviewers or experts
- Aim for approximately 400 words maximum
- Use numbered sources in your report (e.g., [1], [2]) based on information from source documents
        
6. In the Sources section:
- Include all sources used in your report
- Provide full links to relevant websites or specific document paths
- Separate each source by a newline. Use two spaces at the end of each line to create a newline in Markdown.
- It will look like:

### Sources
[1] Link or Document name
[2] Link or Document name

7. Be sure to combine sources. For example this is not correct:

[3] https://ai.meta.com/blog/meta-llama-3-1/
[4] https://ai.meta.com/blog/meta-llama-3-1/

There should be no redundant sources. It should simply be:

[3] https://ai.meta.com/blog/meta-llama-3-1/
        
8. Final review:
- Ensure the report follows the required structure
- Include no preamble before the title of the report
- Check that all guidelines have been followed"""

    def __init__(self, api_key: Optional[str] = None, default_model: str = "gpt-4o"):
        super().__init__(api_key, default_model)
        logger.info("Research LLM service initialized")

    async def create_analysts(
        self, topic: str, max_analysts: int = 3, human_feedback: Optional[str] = None
    ) -> List[Analyst]:
        """Create AI analyst personas using structured output."""
        trace_logger = get_trace_logger()
        start_time = time.time()
        
        # Create messages for tracing
        system_message_content = self.ANALYST_INSTRUCTIONS.format(
            topic=topic,
            human_analyst_feedback=human_feedback or "",
            max_analysts=max_analysts,
        )
        messages = [
            {"role": "system", "content": system_message_content},
            {"role": "user", "content": "Generate set of analysts."},
        ]
        
        # Log LLM request
        trace_id = trace_logger.log_llm_request(
            operation="create_analysts",
            messages=messages,
            model=self.default_model,
            topic=topic,
            max_analysts=max_analysts,
        )
        
        try:
            # Create structured output LLM
            structured_llm = self._chat_client.with_structured_output(Perspectives)

            # Generate analysts (use async invoke to avoid blocking calls)
            result = await structured_llm.ainvoke(
                [
                    SystemMessage(content=system_message_content),
                    HumanMessage(content="Generate set of analysts."),
                ]
            )
            execution_time = time.time() - start_time

            logger.info(f"Created {len(result.analysts)} analysts for topic: {topic}")
            
            # Log LLM response
            response_summary = f"Created {len(result.analysts)} analysts: " + ", ".join(
                [f"{a.name} ({a.role})" for a in result.analysts]
            )
            trace_logger.log_llm_response(
                trace_id=trace_id,
                response=response_summary,
                success=True,
                execution_time=execution_time,
                analyst_count=len(result.analysts),
            )
            
            return result.analysts

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Failed to create analysts: {e}")
            
            # Log failed LLM response
            trace_logger.log_llm_response(
                trace_id=trace_id,
                response="",
                success=False,
                error=str(e),
                execution_time=execution_time,
            )
            
            return self._get_mock_analysts(topic, max_analysts)

    async def generate_interview_question(
        self, analyst: Analyst, messages: List[Dict[str, Any]]
    ) -> str:
        """Generate an interview question from an analyst."""
        trace_logger = get_trace_logger()
        start_time = time.time()
        
        system_message_content = self.QUESTION_INSTRUCTIONS.format(goals=analyst.persona)
        trace_messages = [{"role": "system", "content": system_message_content}] + messages
        
        # Log LLM request
        trace_id = trace_logger.log_llm_request(
            operation="generate_interview_question",
            messages=trace_messages,
            model=self.default_model,
            analyst_name=analyst.name,
            analyst_role=analyst.role,
        )
        
        try:
            # Convert message dicts to LangChain messages
            lc_messages = self._convert_messages_to_langchain(messages)

            system_message = SystemMessage(content=system_message_content)

            response = await self._chat_client.ainvoke([system_message] + lc_messages)
            execution_time = time.time() - start_time
            
            # Log LLM response
            trace_logger.log_llm_response(
                trace_id=trace_id,
                response=response.content,
                success=True,
                execution_time=execution_time,
            )
            
            return response.content

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Failed to generate question: {e}")
            
            fallback_message = f"Hello, I'm {analyst.name}, {analyst.role}. I'm researching this topic and would love to learn more from your expertise. Could you share some insights?"
            
            # Log failed LLM response
            trace_logger.log_llm_response(
                trace_id=trace_id,
                response=fallback_message,
                success=False,
                error=str(e),
                execution_time=execution_time,
            )
            
            return fallback_message

    async def generate_search_query(self, messages: List[Dict[str, Any]]) -> str:
        """Generate a search query from conversation context."""
        try:
            structured_llm = self._chat_client.with_structured_output(SearchQuery)
            lc_messages = self._convert_messages_to_langchain(messages)

            result = await structured_llm.ainvoke(
                [SystemMessage(content=self.SEARCH_INSTRUCTIONS)] + lc_messages
            )

            return result.search_query

        except Exception as e:
            logger.error(f"Failed to generate search query: {e}")
            # Fallback: use last message content
            if messages:
                return messages[-1].get("content", "research topic")
            return "research topic"

    async def generate_expert_answer(
        self, analyst: Analyst, messages: List[Dict[str, Any]], context: str
    ) -> str:
        """Generate an expert answer using provided context."""
        trace_logger = get_trace_logger()
        start_time = time.time()
        
        system_message_content = self.ANSWER_INSTRUCTIONS.format(
            goals=analyst.persona, context=context
        )
        trace_messages = [{"role": "system", "content": system_message_content}] + messages
        
        # Log LLM request
        trace_id = trace_logger.log_llm_request(
            operation="generate_expert_answer",
            messages=trace_messages,
            model=self.default_model,
            analyst_name=analyst.name,
            context_length=len(context),
        )
        
        try:
            lc_messages = self._convert_messages_to_langchain(messages)

            system_message = SystemMessage(content=system_message_content)

            response = await self._chat_client.ainvoke([system_message] + lc_messages)
            execution_time = time.time() - start_time
            
            # Log LLM response
            trace_logger.log_llm_response(
                trace_id=trace_id,
                response=response.content,
                success=True,
                execution_time=execution_time,
            )
            
            return response.content

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Failed to generate expert answer: {e}")
            
            fallback_message = "I apologize, but I'm having trouble accessing the relevant information right now. Could you rephrase your question?"
            
            # Log failed LLM response
            trace_logger.log_llm_response(
                trace_id=trace_id,
                response=fallback_message,
                success=False,
                error=str(e),
                execution_time=execution_time,
            )
            
            return fallback_message

    async def write_research_section(self, analyst: Analyst, context: str) -> str:
        """Write a research section based on interview context."""
        trace_logger = get_trace_logger()
        start_time = time.time()
        
        system_message_content = self.SECTION_WRITER_INSTRUCTIONS.format(
            focus=analyst.description
        )
        human_message_content = f"Use this source to write your section: {context}"
        
        trace_messages = [
            {"role": "system", "content": system_message_content},
            {"role": "user", "content": human_message_content},
        ]
        
        # Log LLM request
        trace_id = trace_logger.log_llm_request(
            operation="write_research_section",
            messages=trace_messages,
            model=self.default_model,
            analyst_name=analyst.name,
            context_length=len(context),
        )
        
        try:
            system_message = SystemMessage(content=system_message_content)
            human_message = HumanMessage(content=human_message_content)

            response = await self._chat_client.ainvoke([system_message, human_message])
            execution_time = time.time() - start_time
            
            # Log LLM response
            trace_logger.log_llm_response(
                trace_id=trace_id,
                response=response.content,
                success=True,
                execution_time=execution_time,
            )
            
            return response.content

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Failed to write research section: {e}")
            
            fallback_message = f"## Research Section: {analyst.role}\n\nUnable to generate section content."
            
            # Log failed LLM response
            trace_logger.log_llm_response(
                trace_id=trace_id,
                response=fallback_message,
                success=False,
                error=str(e),
                execution_time=execution_time,
            )
            
            return fallback_message

    def _convert_messages_to_langchain(self, messages: List[Dict[str, Any]]) -> List:
        """Convert message dictionaries to LangChain message objects."""
        lc_messages = []

        for msg in messages:
            content = msg.get("content", "")
            msg_type = msg.get("type", "human")
            name = msg.get("name")

            if msg_type == "ai" or name == "expert":
                message = AIMessage(content=content)
                if name:
                    message.name = name
            else:
                message = HumanMessage(content=content)
                if name:
                    message.name = name

            lc_messages.append(message)

        return lc_messages

    def _get_mock_analysts(self, topic: str, max_analysts: int) -> List[Analyst]:
        """Generate mock analysts when LLM is unavailable."""
        mock_analysts = []

        for i in range(min(max_analysts, 3)):
            analyst = Analyst(
                name=f"Mock Analyst {i+1}",
                role=f"Researcher",
                affiliation=f"Mock Research Institute {i+1}",
                description=f"Mock analyst focused on {topic} with expertise in analysis {i+1}",
            )
            mock_analysts.append(analyst)

        return mock_analysts
