"""Example script to demonstrate LLM trace logging functionality."""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.infrastructure.services.openai_service import OpenAIService
from app.infrastructure.services.research_llm_service import ResearchLLMService
from app.utils.llm_trace_logger import get_trace_logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def test_basic_logging():
    """Test basic LLM trace logging with OpenAI service."""
    print("=" * 80)
    print("TEST 1: Basic LLM Trace Logging")
    print("=" * 80)
    
    # Check if API key is available
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY not found. Skipping real LLM test.")
        print("Set OPENAI_API_KEY in .env to test with real LLM calls.\n")
        return
    
    try:
        # Initialize OpenAI service
        service = OpenAIService(default_model="gpt-4o-mini")
        
        # Test message
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is clean architecture? Respond in 2 sentences."}
        ]
        
        # Generate response (automatically logged)
        result = await service.generate_response(
            messages=messages,
            temperature=0.7,
            max_tokens=100
        )
        
        if result.success:
            print(f"\n✅ Test completed successfully!")
            print(f"Response preview: {result.data['response'][:100]}...")
        else:
            print(f"\n❌ Test failed: {result.error}")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")


async def test_research_logging():
    """Test research-specific LLM trace logging."""
    print("\n" + "=" * 80)
    print("TEST 2: Research LLM Trace Logging")
    print("=" * 80)
    
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY not found. Skipping research LLM test.\n")
        return
    
    try:
        # Initialize Research LLM service
        service = ResearchLLMService(default_model="gpt-4o-mini")
        
        # Test analyst creation
        topic = "The impact of AI on software development"
        analysts = await service.create_analysts(
            topic=topic,
            max_analysts=2,
            human_feedback="Focus on practical applications"
        )
        
        print(f"\n✅ Created {len(analysts)} analysts:")
        for analyst in analysts:
            print(f"   - {analyst.name} ({analyst.role})")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")


async def test_manual_logging():
    """Test manual trace logging without LLM calls."""
    print("\n" + "=" * 80)
    print("TEST 3: Manual Trace Logging (No API Key Needed)")
    print("=" * 80)
    
    trace_logger = get_trace_logger()
    
    # Simulate an LLM request
    trace_id = trace_logger.log_llm_request(
        operation="test_custom_operation",
        messages=[
            {"role": "system", "content": "You are a test assistant."},
            {"role": "user", "content": "This is a test message."}
        ],
        model="gpt-4o-mini",
        temperature=0.7,
        max_tokens=500,
        custom_param="test_value"
    )
    
    # Simulate processing time
    await asyncio.sleep(0.5)
    
    # Simulate an LLM response
    trace_logger.log_llm_response(
        trace_id=trace_id,
        response="This is a simulated response for testing purposes.",
        success=True,
        execution_time=0.5,
        usage={
            "prompt_tokens": 25,
            "completion_tokens": 15,
            "total_tokens": 40
        }
    )
    
    print("\n✅ Manual logging test completed!")
    print(f"Trace ID: {trace_id}")


async def test_operation_tracking():
    """Test high-level operation tracking."""
    print("\n" + "=" * 80)
    print("TEST 4: Operation Tracking (No API Key Needed)")
    print("=" * 80)
    
    trace_logger = get_trace_logger()
    
    # Start operation
    operation_id = trace_logger.log_operation_start(
        operation="complex_research_workflow",
        context={
            "topic": "AI in Education",
            "max_analysts": 3,
            "interview_turns": 2
        }
    )
    
    # Simulate work
    await asyncio.sleep(0.3)
    
    # End operation
    trace_logger.log_operation_end(
        operation_id=operation_id,
        operation="complex_research_workflow",
        success=True,
        result="Research completed successfully"
    )
    
    print("\n✅ Operation tracking test completed!")
    print(f"Operation ID: {operation_id}")


def check_log_files():
    """Check if log files were created."""
    print("\n" + "=" * 80)
    print("Log Files Check")
    print("=" * 80)
    
    log_dir = Path("./logs/llm_traces")
    
    if log_dir.exists():
        log_files = list(log_dir.glob("*.json"))
        print(f"\n✅ Log directory exists: {log_dir}")
        print(f"📁 Found {len(log_files)} log files")
        
        if log_files:
            print("\nRecent log files:")
            for file in sorted(log_files, key=lambda f: f.stat().st_mtime, reverse=True)[:5]:
                size = file.stat().st_size
                print(f"   - {file.name} ({size} bytes)")
        else:
            print("\n⚠️  No log files found (this is normal if file logging is disabled)")
    else:
        print(f"\n⚠️  Log directory does not exist: {log_dir}")
        print("This is normal if file logging is disabled in .env")


def print_configuration():
    """Print current logging configuration."""
    print("\n" + "=" * 80)
    print("Current Configuration")
    print("=" * 80)
    
    config = {
        "LLM_TRACE_FILE_LOGGING": os.getenv("LLM_TRACE_FILE_LOGGING", "true"),
        "LLM_TRACE_CONSOLE_LOGGING": os.getenv("LLM_TRACE_CONSOLE_LOGGING", "true"),
        "LLM_TRACE_LOG_DIR": os.getenv("LLM_TRACE_LOG_DIR", "./logs/llm_traces"),
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
        "OPENAI_API_KEY": "✅ Set" if os.getenv("OPENAI_API_KEY") else "❌ Not set"
    }
    
    for key, value in config.items():
        print(f"{key}: {value}")


async def main():
    """Run all tests."""
    print("\n" + "🧪" * 40)
    print("LLM Trace Logging Test Suite")
    print("🧪" * 40)
    
    print_configuration()
    
    # Run tests
    await test_manual_logging()
    await test_operation_tracking()
    await test_basic_logging()
    await test_research_logging()
    
    # Check log files
    check_log_files()
    
    print("\n" + "=" * 80)
    print("✅ All tests completed!")
    print("=" * 80)
    print("\nTo view detailed logs:")
    print("  - Console: Check output above")
    print("  - Files: Check ./logs/llm_traces/ directory")
    print("\nTo configure logging:")
    print("  - Edit .env file")
    print("  - Set LLM_TRACE_FILE_LOGGING, LLM_TRACE_CONSOLE_LOGGING")
    print("  - See docs/LLM_TRACE_LOGGING.md for details\n")


if __name__ == "__main__":
    asyncio.run(main())
