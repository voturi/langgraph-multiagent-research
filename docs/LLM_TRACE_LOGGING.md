# LLM Trace Logging

Comprehensive logging system for tracing LLM inputs, outputs, and execution flow.

## Overview

The LLM Trace Logger provides detailed tracking of all LLM interactions in the research assistant, including:
- Input messages and parameters
- Response content and metadata
- Execution times and token usage
- Error tracking and debugging information
- Operation-level workflow tracking

## Features

### 1. **Automatic Request/Response Logging**
Every LLM call is automatically logged with:
- Full input messages (system, user, assistant)
- Model parameters (temperature, max_tokens, etc.)
- Response content
- Token usage statistics
- Execution time
- Success/failure status

### 2. **Dual Logging Modes**
- **Console Logging**: Human-readable output with emojis and formatting
- **File Logging**: Structured JSON files for programmatic analysis

### 3. **Operation Tracking**
Track high-level operations (e.g., "create_analysts", "conduct_interview") with start/end markers and correlation IDs.

### 4. **Configurable Output**
Control logging behavior via environment variables without code changes.

## Configuration

Add these variables to your `.env` file:

```bash
# LLM Trace Logging Configuration
LLM_TRACE_FILE_LOGGING=true          # Enable/disable file logging
LLM_TRACE_CONSOLE_LOGGING=true       # Enable/disable console logging
LLM_TRACE_LOG_DIR=./logs/llm_traces  # Directory for log files
LOG_LEVEL=INFO                        # Overall log level
```

### Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_TRACE_FILE_LOGGING` | `true` | Write detailed JSON logs to files |
| `LLM_TRACE_CONSOLE_LOGGING` | `true` | Print formatted logs to console |
| `LLM_TRACE_LOG_DIR` | `./logs/llm_traces` | Directory for log files |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

## Usage

### Automatic Logging (Already Integrated)

The trace logger is already integrated into all LLM services. No additional code needed!

Logged operations:
- `generate_response` - Base LLM response generation
- `create_analysts` - Analyst persona creation
- `generate_interview_question` - Interview question generation
- `generate_search_query` - Search query generation
- `generate_expert_answer` - Expert answer generation
- `write_research_section` - Research section writing

### Manual Logging (For Custom Operations)

```python
from app.utils.llm_trace_logger import get_trace_logger

trace_logger = get_trace_logger()

# Log an LLM request
trace_id = trace_logger.log_llm_request(
    operation="my_custom_operation",
    messages=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "What is clean architecture?"}
    ],
    model="gpt-4o-mini",
    temperature=0.7,
    max_tokens=1000,
)

# ... call your LLM ...

# Log the response
trace_logger.log_llm_response(
    trace_id=trace_id,
    response="Clean architecture is...",
    success=True,
    execution_time=2.5,
    usage={"prompt_tokens": 50, "completion_tokens": 100}
)
```

### Using the Decorator

```python
from app.utils.llm_trace_logger import trace_llm_call

@trace_llm_call("custom_llm_operation")
async def my_custom_function(topic: str):
    # Your LLM operation
    result = await some_llm_call(topic)
    return result
```

## Log File Structure

### Request Logs
Located at: `logs/llm_traces/trace_{trace_id}_request.json`

```json
{
  "trace_id": "20251130_012345_0001",
  "timestamp": "2025-11-30T01:23:45.123456",
  "operation": "create_analysts",
  "request": {
    "messages": [
      {"role": "system", "content": "..."},
      {"role": "user", "content": "..."}
    ],
    "model": "gpt-4o",
    "temperature": 0.1,
    "max_tokens": 1000,
    "message_count": 2,
    "additional_params": {
      "topic": "AI in healthcare",
      "max_analysts": 3
    }
  }
}
```

### Response Logs
Located at: `logs/llm_traces/trace_{trace_id}_response.json`

```json
{
  "trace_id": "20251130_012345_0001",
  "timestamp": "2025-11-30T01:23:47.456789",
  "success": true,
  "response": {
    "content": "Created 3 analysts: Dr. Smith (Medical AI Specialist), ..."
  },
  "error": null,
  "execution_time_seconds": 2.33,
  "usage": {
    "prompt_tokens": 150,
    "completion_tokens": 300,
    "total_tokens": 450
  },
  "metadata": {
    "analyst_count": 3
  }
}
```

### Operation Logs
Track high-level workflow operations:
- `operation_{operation_id}_start.json` - Operation start
- `operation_{operation_id}_end.json` - Operation completion

## Console Output Example

```
================================================================================
🚀 LLM REQUEST - Trace ID: 20251130_012345_0001
Operation: create_analysts
Model: gpt-4o
Temperature: 0.1, Max Tokens: 1000
Message Count: 2

📝 Messages:
[Message 1] Role: system
You are tasked with creating a set of AI analyst personas...

[Message 2] Role: user
Generate set of analysts.

✅ SUCCESS - Trace ID: 20251130_012345_0001
⏱️  Execution Time: 2.33s
📊 Token Usage: {'prompt_tokens': 150, 'completion_tokens': 300}

💬 Response:
Created 3 analysts: Dr. Sarah Smith (Medical AI Specialist), Prof. John Doe (Healthcare Policy Expert), Dr. Jane Williams (Clinical Data Scientist)
================================================================================
```

## Log Analysis

### View All Traces
```bash
ls -lh logs/llm_traces/
```

### Search for Specific Operation
```bash
grep -r "create_analysts" logs/llm_traces/
```

### Analyze Token Usage
```bash
jq '.usage.total_tokens' logs/llm_traces/trace_*_response.json | awk '{sum+=$1} END {print "Total tokens:", sum}'
```

### Find Failed Requests
```bash
jq 'select(.success == false)' logs/llm_traces/trace_*_response.json
```

### Calculate Average Execution Time
```bash
jq '.execution_time_seconds' logs/llm_traces/trace_*_response.json | awk '{sum+=$1; count++} END {print "Avg time:", sum/count, "seconds"}'
```

## Debugging Workflow

1. **Enable detailed logging**:
   ```bash
   export LOG_LEVEL=DEBUG
   export LLM_TRACE_CONSOLE_LOGGING=true
   ```

2. **Run your research assistant**:
   ```bash
   python interactive_research_assistant.py
   ```

3. **Review logs in real-time** (console) or after execution (files)

4. **Trace specific issues**:
   - Find the trace_id from console output
   - Open corresponding JSON files
   - Examine full request/response details

## Performance Considerations

### Minimize Performance Impact
```bash
# For production: disable console logging, keep file logging
export LLM_TRACE_CONSOLE_LOGGING=false
export LLM_TRACE_FILE_LOGGING=true
```

### Reduce Storage Usage
```bash
# Disable file logging for high-volume scenarios
export LLM_TRACE_FILE_LOGGING=false
```

### Log Rotation
Implement log rotation to manage disk space:

```bash
# Clean up logs older than 7 days
find logs/llm_traces/ -name "*.json" -mtime +7 -delete
```

## Privacy & Security

⚠️ **Important**: Trace logs contain full LLM inputs and outputs, which may include:
- Sensitive research topics
- Internal prompts and instructions
- User queries and data

**Best Practices**:
1. Store logs in secure locations with appropriate access controls
2. Implement log rotation and retention policies
3. Exclude logs directory from version control (`.gitignore`)
4. Sanitize logs before sharing or analyzing externally
5. Use environment variables to disable logging in sensitive environments

## Troubleshooting

### Logs Not Appearing
1. Check environment variables are set correctly
2. Verify log directory permissions
3. Ensure `LLM_TRACE_*` variables are `true` (lowercase)

### Large Log Files
1. Implement log rotation
2. Reduce `max_tokens` to limit response sizes
3. Consider disabling file logging for high-volume operations

### Missing Token Usage
Token usage depends on the LLM provider's response format. Some providers may not include usage metadata.

## Integration with LangSmith

The trace logger complements LangSmith tracing:
- **LangSmith**: Distributed tracing, UI, team collaboration
- **LLM Trace Logger**: Detailed local logs, custom analysis, offline debugging

Both can be used simultaneously for comprehensive observability.

## Examples

### Example 1: Debugging Failed Analyst Creation

```bash
# Find failed operations
jq 'select(.success == false and .operation == "create_analysts")' \
   logs/llm_traces/trace_*_response.json
```

### Example 2: Token Usage Report

```python
import json
from pathlib import Path

total_tokens = 0
for file in Path("logs/llm_traces").glob("trace_*_response.json"):
    with open(file) as f:
        data = json.load(f)
        if data.get("usage"):
            total_tokens += data["usage"].get("total_tokens", 0)

print(f"Total tokens used: {total_tokens}")
```

### Example 3: Performance Analysis

```python
import json
from pathlib import Path
from collections import defaultdict

operation_times = defaultdict(list)

for file in Path("logs/llm_traces").glob("trace_*_response.json"):
    with open(file) as f:
        data = json.load(f)
        # Read corresponding request file for operation name
        request_file = file.parent / file.name.replace("_response", "_request")
        if request_file.exists():
            with open(request_file) as rf:
                req_data = json.load(rf)
                operation = req_data.get("operation")
                exec_time = data.get("execution_time_seconds")
                if operation and exec_time:
                    operation_times[operation].append(exec_time)

# Print statistics
for operation, times in operation_times.items():
    avg_time = sum(times) / len(times)
    print(f"{operation}: {avg_time:.2f}s avg ({len(times)} calls)")
```

## Future Enhancements

Potential improvements:
- [ ] Structured log aggregation (e.g., to Elasticsearch)
- [ ] Real-time dashboard for monitoring
- [ ] Automatic anomaly detection
- [ ] Cost tracking (token usage → API costs)
- [ ] Integration with APM tools (DataDog, New Relic)
- [ ] Log compression for long-term storage
- [ ] Configurable PII redaction

## Support

For issues or questions:
1. Check this documentation
2. Review example logs in `logs/llm_traces/`
3. Open an issue in the project repository
