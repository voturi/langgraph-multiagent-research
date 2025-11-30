"""LLM Trace Logger - Comprehensive logging for LLM inputs and outputs."""

import json
import logging
import os
import time
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class LLMTraceLogger:
    """Logger for tracing LLM inputs, outputs, and execution flow."""

    def __init__(
        self,
        log_dir: Optional[str] = None,
        enable_file_logging: bool = True,
        enable_console_logging: bool = True,
        log_level: str = "INFO",
    ):
        """
        Initialize LLM trace logger.

        Args:
            log_dir: Directory for trace log files. Defaults to ./logs/llm_traces
            enable_file_logging: Whether to write traces to files
            enable_console_logging: Whether to log to console
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        self.enable_file_logging = enable_file_logging
        self.enable_console_logging = enable_console_logging

        # Setup log directory
        if log_dir:
            self.log_dir = Path(log_dir)
        else:
            self.log_dir = Path("./logs/llm_traces")

        if self.enable_file_logging:
            self.log_dir.mkdir(parents=True, exist_ok=True)

        # Setup logger
        self.logger = logging.getLogger("llm_trace")
        self.logger.setLevel(getattr(logging, log_level.upper()))

        # Prevent duplicate handlers
        if not self.logger.handlers:
            if enable_console_logging:
                console_handler = logging.StreamHandler()
                console_handler.setLevel(logging.INFO)
                console_formatter = logging.Formatter(
                    "%(asctime)s - [LLM_TRACE] - %(levelname)s - %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
                console_handler.setFormatter(console_formatter)
                self.logger.addHandler(console_handler)

        # Trace counter for unique IDs
        self._trace_counter = 0

    def _get_trace_id(self) -> str:
        """Generate unique trace ID."""
        self._trace_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{timestamp}_{self._trace_counter:04d}"

    def _truncate_text(self, text: str, max_length: int = 500) -> str:
        """Truncate text for console display."""
        if len(text) <= max_length:
            return text
        return text[:max_length] + f"... [{len(text) - max_length} more chars]"

    def _format_messages(self, messages: List[Dict[str, Any]]) -> str:
        """Format messages for readable display."""
        formatted = []
        for i, msg in enumerate(messages):
            role = msg.get("role", msg.get("type", "unknown"))
            content = msg.get("content", "")
            name = msg.get("name", "")
            
            header = f"[Message {i+1}] Role: {role}"
            if name:
                header += f" | Name: {name}"
            
            formatted.append(f"{header}\n{content}\n")
        
        return "\n".join(formatted)

    def log_llm_request(
        self,
        operation: str,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        trace_id: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        Log an LLM request with all parameters.

        Args:
            operation: Name of the operation (e.g., "generate_response", "create_analysts")
            messages: Input messages to the LLM
            model: Model name
            temperature: Temperature parameter
            max_tokens: Max tokens parameter
            trace_id: Optional trace ID for correlation
            **kwargs: Additional parameters

        Returns:
            trace_id for correlating with response
        """
        if trace_id is None:
            trace_id = self._get_trace_id()

        # Build trace data
        trace_data = {
            "trace_id": trace_id,
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "request": {
                "messages": messages,
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "message_count": len(messages),
                "additional_params": kwargs,
            },
        }

        # Console logging (truncated)
        if self.enable_console_logging:
            self.logger.info(f"{'='*80}")
            self.logger.info(f"🚀 LLM REQUEST - Trace ID: {trace_id}")
            self.logger.info(f"Operation: {operation}")
            self.logger.info(f"Model: {model or 'default'}")
            self.logger.info(f"Temperature: {temperature}, Max Tokens: {max_tokens}")
            self.logger.info(f"Message Count: {len(messages)}")
            self.logger.info(f"\n📝 Messages:\n{self._format_messages(messages)}")
            if kwargs:
                self.logger.info(f"Additional Params: {kwargs}")

        # File logging (full data)
        if self.enable_file_logging:
            trace_file = self.log_dir / f"trace_{trace_id}_request.json"
            with open(trace_file, "w") as f:
                json.dump(trace_data, f, indent=2, default=str)

        return trace_id

    def log_llm_response(
        self,
        trace_id: str,
        response: Union[str, Dict[str, Any]],
        success: bool = True,
        error: Optional[str] = None,
        execution_time: Optional[float] = None,
        usage: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        """
        Log an LLM response with execution details.

        Args:
            trace_id: Trace ID from the request
            response: Response content from LLM
            success: Whether the request succeeded
            error: Error message if failed
            execution_time: Execution time in seconds
            usage: Token usage information
            **kwargs: Additional metadata
        """
        # Extract response content
        if isinstance(response, dict):
            response_content = response.get("response") or response.get("content") or str(response)
            response_data = response
        else:
            response_content = str(response)
            response_data = {"content": response_content}

        # Build trace data
        trace_data = {
            "trace_id": trace_id,
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "response": response_data,
            "error": error,
            "execution_time_seconds": execution_time,
            "usage": usage,
            "metadata": kwargs,
        }

        # Console logging (truncated)
        if self.enable_console_logging:
            status = "✅ SUCCESS" if success else "❌ FAILED"
            self.logger.info(f"\n{status} - Trace ID: {trace_id}")
            
            if execution_time:
                self.logger.info(f"⏱️  Execution Time: {execution_time:.2f}s")
            
            if usage:
                self.logger.info(f"📊 Token Usage: {usage}")
            
            if success:
                truncated_response = self._truncate_text(response_content, max_length=800)
                self.logger.info(f"\n💬 Response:\n{truncated_response}")
            else:
                self.logger.error(f"\n⚠️  Error: {error}")
            
            self.logger.info(f"{'='*80}\n")

        # File logging (full data)
        if self.enable_file_logging:
            trace_file = self.log_dir / f"trace_{trace_id}_response.json"
            with open(trace_file, "w") as f:
                json.dump(trace_data, f, indent=2, default=str)

    def log_operation_start(
        self, operation: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log the start of a high-level operation.

        Args:
            operation: Name of the operation
            context: Additional context data

        Returns:
            operation_id for tracking
        """
        operation_id = self._get_trace_id()
        
        if self.enable_console_logging:
            self.logger.info(f"\n{'🔵'*40}")
            self.logger.info(f"🎬 OPERATION START - {operation}")
            self.logger.info(f"Operation ID: {operation_id}")
            if context:
                self.logger.info(f"Context: {json.dumps(context, indent=2, default=str)}")
            self.logger.info(f"{'🔵'*40}\n")

        if self.enable_file_logging:
            op_file = self.log_dir / f"operation_{operation_id}_start.json"
            op_data = {
                "operation_id": operation_id,
                "operation": operation,
                "timestamp": datetime.now().isoformat(),
                "context": context,
            }
            with open(op_file, "w") as f:
                json.dump(op_data, f, indent=2, default=str)

        return operation_id

    def log_operation_end(
        self,
        operation_id: str,
        operation: str,
        success: bool = True,
        result: Optional[Any] = None,
        error: Optional[str] = None,
    ):
        """
        Log the end of a high-level operation.

        Args:
            operation_id: Operation ID from start
            operation: Name of the operation
            success: Whether operation succeeded
            result: Operation result
            error: Error message if failed
        """
        if self.enable_console_logging:
            status = "✅ COMPLETED" if success else "❌ FAILED"
            self.logger.info(f"\n{'🟢' if success else '🔴'*40}")
            self.logger.info(f"🏁 OPERATION END - {operation} - {status}")
            self.logger.info(f"Operation ID: {operation_id}")
            if error:
                self.logger.error(f"Error: {error}")
            self.logger.info(f"{'🟢' if success else '🔴'*40}\n")

        if self.enable_file_logging:
            op_file = self.log_dir / f"operation_{operation_id}_end.json"
            op_data = {
                "operation_id": operation_id,
                "operation": operation,
                "timestamp": datetime.now().isoformat(),
                "success": success,
                "result": str(result) if result else None,
                "error": error,
            }
            with open(op_file, "w") as f:
                json.dump(op_data, f, indent=2, default=str)


# Global trace logger instance
_trace_logger: Optional[LLMTraceLogger] = None


def get_trace_logger() -> LLMTraceLogger:
    """Get or create the global trace logger instance."""
    global _trace_logger
    if _trace_logger is None:
        log_level = os.getenv("LOG_LEVEL", "INFO")
        enable_file_logging = os.getenv("LLM_TRACE_FILE_LOGGING", "true").lower() == "true"
        enable_console_logging = os.getenv("LLM_TRACE_CONSOLE_LOGGING", "true").lower() == "true"
        log_dir = os.getenv("LLM_TRACE_LOG_DIR", "./logs/llm_traces")
        
        _trace_logger = LLMTraceLogger(
            log_dir=log_dir,
            enable_file_logging=enable_file_logging,
            enable_console_logging=enable_console_logging,
            log_level=log_level,
        )
    return _trace_logger


def trace_llm_call(operation_name: Optional[str] = None):
    """
    Decorator to automatically trace LLM calls.

    Usage:
        @trace_llm_call("create_analysts")
        async def create_analysts(self, topic: str, ...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        op_name = operation_name or func.__name__

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            trace_logger = get_trace_logger()
            start_time = time.time()
            
            # Extract self if it's a method
            if args and hasattr(args[0], '__class__'):
                context = {"class": args[0].__class__.__name__, "method": func.__name__}
            else:
                context = {"function": func.__name__}
            
            trace_id = trace_logger.log_operation_start(op_name, context)
            
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                trace_logger.log_operation_end(
                    trace_id, op_name, success=True, result=type(result).__name__
                )
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                trace_logger.log_operation_end(
                    trace_id, op_name, success=False, error=str(e)
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            trace_logger = get_trace_logger()
            start_time = time.time()
            
            if args and hasattr(args[0], '__class__'):
                context = {"class": args[0].__class__.__name__, "method": func.__name__}
            else:
                context = {"function": func.__name__}
            
            trace_id = trace_logger.log_operation_start(op_name, context)
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                trace_logger.log_operation_end(
                    trace_id, op_name, success=True, result=type(result).__name__
                )
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                trace_logger.log_operation_end(
                    trace_id, op_name, success=False, error=str(e)
                )
                raise

        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
