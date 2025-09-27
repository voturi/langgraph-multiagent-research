#!/usr/bin/env python3
"""Interactive terminal test for the research assistant with real APIs."""

import asyncio
import sys
import os
import json
from typing import Dict, Any, Optional

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app.orchestration.langgraph.research_orchestrator import ResearchOrchestrator
from app.orchestration.langgraph.research_entry import create_research_dependencies


class InteractiveResearchTester:
    """Interactive terminal tester for research assistant."""
    
    def __init__(self):
        self.orchestrator = None
        self.current_thread_config = None
    
    def print_header(self, text: str):
        """Print a formatted header."""
        print("\n" + "="*60)
        print(f"  {text}")
        print("="*60)
    
    def print_section(self, text: str):
        """Print a formatted section."""
        print(f"\n--- {text} ---")
    
    def print_analyst(self, analyst, index: int):
        """Print analyst information."""
        print(f"\n{index + 1}. {analyst.name}")
        print(f"   Role: {analyst.role}")
        print(f"   Affiliation: {analyst.affiliation}")
        print(f"   Description: {analyst.description}")
    
    def print_section_preview(self, section: Dict[str, Any], index: int):
        """Print research section preview."""
        title = section.get('title', 'Untitled')
        analyst_name = section.get('analyst_name', 'Unknown')
        # Use content_preview if available, otherwise create preview from content
        content_preview = section.get('content_preview')
        if content_preview:
            preview_text = content_preview
        else:
            content = section.get('content', '')
            preview_text = content[:150] + "..." if len(content) > 150 else content
        
        print(f"\n{index + 1}. {title}")
        print(f"   By: {analyst_name}")
        print(f"   Preview: {preview_text}")
        
        sources = section.get('sources', [])
        if sources:
            print(f"   Sources: {len(sources)} citations")
    
    async def setup_research_assistant(self):
        """Set up the research assistant."""
        self.print_header("SETTING UP RESEARCH ASSISTANT")
        
        try:
            # Create research workflow
            print("🔧 Initializing research workflow...")
            research_workflow = create_research_dependencies()
            
            # Create orchestrator
            print("🎛️ Setting up orchestrator...")
            self.orchestrator = ResearchOrchestrator(research_workflow)
            
            # Check if using real APIs
            if research_workflow.use_mock:
                print("⚠️  Using MOCK services (API keys not configured)")
                return False
            else:
                print("✅ Using REAL APIs:")
                print("   - OpenAI API ✅")
                print("   - Tavily Search API ✅") 
                print("   - Wikipedia API ✅")
                return True
                
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return False
    
    def get_research_topic(self) -> Optional[str]:
        """Get research topic from user."""
        self.print_section("Research Topic")
        
        print("Enter a research topic you'd like to investigate.")
        print("Examples:")
        print("  - 'Machine learning best practices for production systems'")
        print("  - 'Sustainable energy solutions for urban environments'") 
        print("  - 'Modern software architecture patterns'")
        
        while True:
            topic = input("\n🔍 Research topic: ").strip()
            if topic:
                return topic
            print("Please enter a valid topic.")
    
    def get_research_config(self) -> Dict[str, Any]:
        """Get research configuration from user."""
        self.print_section("Research Configuration")
        
        # Number of analysts
        while True:
            try:
                max_analysts = input("📊 Number of analyst perspectives (2-5) [default: 3]: ").strip()
                if not max_analysts:
                    max_analysts = 3
                else:
                    max_analysts = int(max_analysts)
                
                if 2 <= max_analysts <= 5:
                    break
                else:
                    print("Please enter a number between 2 and 5.")
            except ValueError:
                print("Please enter a valid number.")
        
        # Interview turns
        while True:
            try:
                max_turns = input("🎤 Interview depth (1-3 turns per analyst) [default: 2]: ").strip()
                if not max_turns:
                    max_turns = 2
                else:
                    max_turns = int(max_turns)
                
                if 1 <= max_turns <= 3:
                    break
                else:
                    print("Please enter a number between 1 and 3.")
            except ValueError:
                print("Please enter a valid number.")
        
        return {
            "max_analysts": max_analysts,
            "max_interview_turns": max_turns
        }
    
    async def start_research_with_interruption(self, topic: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Start research workflow with human feedback interruption."""
        self.print_header("STARTING RESEARCH WORKFLOW")
        
        print(f"🚀 Initiating research on: '{topic}'")
        print(f"📊 Configuration: {config['max_analysts']} analysts, {config['max_interview_turns']} interview turns")
        
        # Start workflow with interruption
        result = await self.orchestrator.run_research_with_interruption(
            topic=topic,
            max_analysts=config["max_analysts"],
            max_interview_turns=config["max_interview_turns"]
        )
        
        if result.get("status") == "paused_for_feedback":
            # Store thread config for continuation
            self.current_thread_config = result["thread_config"]
            current_state = result["current_state"]
            
            # Show generated analysts
            analysts = current_state.get("analysts", [])
            if analysts:
                self.print_section(f"Generated Analysts ({len(analysts)})")
                for i, analyst in enumerate(analysts):
                    self.print_analyst(analyst, i)
                
                return {"paused": True, "analysts": analysts}
        
        return result
    
    def get_human_feedback(self, analysts) -> Optional[str]:
        """Get human feedback about the analysts."""
        self.print_section("Human Feedback")
        
        print("The AI has generated analyst personas for your research topic.")
        print("You can provide feedback to refine the analysts, or proceed as-is.")
        print("\nOptions:")
        print("1. Proceed with these analysts (press Enter)")
        print("2. Provide feedback to modify analysts")
        print("3. Cancel research")
        
        choice = input("\nYour choice [1]: ").strip()
        
        if choice == "3":
            return None  # Cancel
        elif choice == "2":
            print("\nProvide feedback to improve the analyst selection:")
            print("Examples:")
            print("  - 'Add a practitioner with startup experience'")
            print("  - 'Include an academic researcher perspective'")
            print("  - 'Focus more on practical implementation'")
            
            feedback = input("\n💬 Your feedback: ").strip()
            return feedback if feedback else ""
        else:
            return ""  # Proceed as-is
    
    async def continue_research(self, feedback: str) -> Dict[str, Any]:
        """Continue research with human feedback."""
        self.print_header("CONTINUING RESEARCH")
        
        if feedback:
            print(f"💬 Applying your feedback: '{feedback}'")
        else:
            print("📋 Proceeding with current analysts")
        
        print("🔄 Resuming workflow...")
        print("   This will:")
        print("   - Conduct interviews with each analyst")
        print("   - Search for relevant information")
        print("   - Generate research sections")
        print("   - Compile final report")
        
        # Continue the workflow
        result = await self.orchestrator.continue_research_with_feedback(
            human_feedback=feedback,
            thread_config=self.current_thread_config
        )
        
        return result
    
    def display_results(self, result: Dict[str, Any]):
        """Display final research results."""
        self.print_header("RESEARCH RESULTS")
        
        if result.get("success"):
            output_data = result.get("output_data", {})
            
            print("✅ Research completed successfully!")
            print(f"📊 Topic: {output_data.get('topic', 'Unknown')}")
            print(f"👥 Analysts: {output_data.get('total_analysts', 0)}")
            print(f"🎤 Interviews: {output_data.get('total_interviews', 0)}")
            print(f"📄 Sections: {output_data.get('total_sections', 0)}")
            
            # Display sections
            sections = output_data.get("sections", [])
            if sections:
                self.print_section(f"Research Sections ({len(sections)})")
                for i, section in enumerate(sections):
                    self.print_section_preview(section, i)
                    
                # Ask if user wants to see full content
                if input("\n📖 View full section content? (y/n) [n]: ").strip().lower() == 'y':
                    for i, section in enumerate(sections):
                        self.print_header(f"SECTION {i+1}: {section.get('title', 'Untitled')}")
                        print(f"By: {section.get('analyst_name', 'Unknown')}")
                        print(f"\n{section.get('content', 'No content')}")
                        
                        if i < len(sections) - 1:
                            input("\nPress Enter for next section...")
        
        else:
            print("❌ Research failed")
            error = result.get("error", "Unknown error")
            print(f"Error: {error}")
    
    async def run_interactive_test(self):
        """Run the complete interactive test."""
        self.print_header("INTERACTIVE RESEARCH ASSISTANT TEST")
        
        print("Welcome to the Research Assistant!")
        print("This tool will create AI analyst personas, conduct interviews,")
        print("and generate comprehensive research reports on your topic.")
        
        # Setup
        if not await self.setup_research_assistant():
            print("\n❌ Setup failed. Please check your API keys and try again.")
            return
        
        # Get research parameters
        topic = self.get_research_topic()
        if not topic:
            print("❌ No topic provided. Exiting.")
            return
            
        config = self.get_research_config()
        
        try:
            # Start research with interruption
            result = await self.start_research_with_interruption(topic, config)
            
            if result.get("paused"):
                analysts = result["analysts"]
                
                # Get human feedback
                feedback = self.get_human_feedback(analysts)
                if feedback is None:
                    print("\n🚫 Research cancelled by user.")
                    return
                
                # Continue with feedback
                final_result = await self.continue_research(feedback)
                
                # Display results
                self.display_results(final_result)
            
            else:
                # Handle error case
                print("❌ Unexpected workflow state")
                print(f"Result: {result}")
        
        except KeyboardInterrupt:
            print("\n\n🚫 Research interrupted by user.")
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """Main function."""
    tester = InteractiveResearchTester()
    await tester.run_interactive_test()


if __name__ == "__main__":
    asyncio.run(main())