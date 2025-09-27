"""Research Assistant domain entities."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from ..models.entities import BaseEntity


class Analyst(BaseEntity):
    """Domain entity representing an AI analyst persona for research."""

    name: str = Field(description="Name of the analyst")
    role: str = Field(description="Role of the analyst in the context of the topic")
    affiliation: str = Field(description="Primary affiliation of the analyst")
    description: str = Field(
        description="Description of the analyst focus, concerns, and motives"
    )

    @property
    def persona(self) -> str:
        """Generate a formatted persona string for the analyst."""
        return (
            f"Name: {self.name}\n"
            f"Role: {self.role}\n"
            f"Affiliation: {self.affiliation}\n"
            f"Description: {self.description}"
        )


class Perspectives(BaseModel):
    """Collection of analysts representing different perspectives on a topic."""

    analysts: List[Analyst] = Field(
        description="Comprehensive list of analysts with their roles and affiliations"
    )


class ResearchTopic(BaseEntity):
    """Domain entity representing a research topic."""

    topic: str = Field(description="The main research topic")
    max_analysts: int = Field(
        default=3, description="Maximum number of analysts to create"
    )
    human_feedback: Optional[str] = Field(
        default=None, description="Optional human feedback to guide analyst creation"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SearchQuery(BaseModel):
    """Domain model for search queries."""

    search_query: str = Field(description="Search query for retrieval")


class Interview(BaseEntity):
    """Domain entity representing an interview between analyst and expert."""

    analyst_id: str = Field(description="ID of the analyst conducting the interview")
    topic: str = Field(description="Topic being researched")
    transcript: str = Field(description="Interview transcript")
    context_documents: List[str] = Field(
        default_factory=list, description="Source documents used in the interview"
    )
    max_turns: int = Field(
        default=2, description="Maximum number of conversation turns"
    )
    completed_at: Optional[datetime] = Field(default=None)


class ResearchSection(BaseEntity):
    """Domain entity representing a written research section."""

    interview_id: str = Field(
        description="ID of the interview this section is based on"
    )
    analyst_id: str = Field(description="ID of the analyst")
    title: str = Field(description="Section title")
    content: str = Field(description="Markdown formatted content")
    sources: List[str] = Field(
        default_factory=list, description="List of sources cited in the section"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ResearchProject(BaseEntity):
    """Domain entity representing a complete research project."""

    topic: str = Field(description="Main research topic")
    analysts: List[Analyst] = Field(default_factory=list)
    interviews: List[Interview] = Field(default_factory=list)
    sections: List[ResearchSection] = Field(default_factory=list)
    status: str = Field(default="created", description="Project status")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)
