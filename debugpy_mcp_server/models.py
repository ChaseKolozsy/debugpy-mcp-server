"""
Pydantic models for debugpy MCP server data structures.
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class DebugSession(BaseModel):
    """Model for a debug session."""
    session_id: str = Field(..., description="Unique identifier for the debug session")
    host: str = Field(..., description="Host address of the debugpy server")
    port: int = Field(..., description="Port number of the debugpy server")
    is_connected: bool = Field(default=False, description="Whether the session is connected")
    process_id: Optional[int] = Field(default=None, description="Process ID of the debugged program")
    status: str = Field(default="disconnected", description="Current status of the session")


class Breakpoint(BaseModel):
    """Model for a breakpoint."""
    breakpoint_id: int = Field(..., description="Unique identifier for the breakpoint")
    file_path: str = Field(..., description="Path to the file containing the breakpoint")
    line_number: int = Field(..., description="Line number of the breakpoint")
    is_enabled: bool = Field(default=True, description="Whether the breakpoint is enabled")
    condition: Optional[str] = Field(default=None, description="Optional condition for the breakpoint")
    hit_count: int = Field(default=0, description="Number of times the breakpoint has been hit")


class StackFrame(BaseModel):
    """Model for a stack frame."""
    frame_id: int = Field(..., description="Unique identifier for the frame")
    name: str = Field(..., description="Name of the function/method")
    file_path: str = Field(..., description="Path to the source file")
    line_number: int = Field(..., description="Current line number in the frame")
    column: Optional[int] = Field(default=None, description="Current column number")
    source: Optional[str] = Field(default=None, description="Source code snippet")


class Variable(BaseModel):
    """Model for a variable."""
    name: str = Field(..., description="Name of the variable")
    value: str = Field(..., description="String representation of the variable value")
    type: str = Field(..., description="Type of the variable")
    scope: str = Field(..., description="Scope of the variable (local, global, etc.)")
    is_expandable: bool = Field(default=False, description="Whether the variable has child properties")


class DebugEvent(BaseModel):
    """Model for debug events."""
    event_type: str = Field(..., description="Type of the debug event")
    session_id: str = Field(..., description="Session ID that generated the event")
    data: Dict[str, Any] = Field(default_factory=dict, description="Event-specific data")
    timestamp: float = Field(..., description="Timestamp when the event occurred")


class ProcessInfo(BaseModel):
    """Model for process information."""
    process_id: int = Field(..., description="Process ID")
    name: str = Field(..., description="Process name")
    command_line: Optional[str] = Field(default=None, description="Command line used to start the process")
    is_debuggable: bool = Field(default=False, description="Whether the process can be debugged")
    debugpy_port: Optional[int] = Field(default=None, description="Port if debugpy is already listening")


class ExpressionResult(BaseModel):
    """Model for expression evaluation results."""
    expression: str = Field(..., description="The evaluated expression")
    result: str = Field(..., description="String representation of the result")
    type: str = Field(..., description="Type of the result")
    is_error: bool = Field(default=False, description="Whether evaluation resulted in an error")
    error_message: Optional[str] = Field(default=None, description="Error message if evaluation failed")


class SourceLocation(BaseModel):
    """Model for source code location."""
    file_path: str = Field(..., description="Path to the source file")
    line_number: int = Field(..., description="Line number")
    column: Optional[int] = Field(default=None, description="Column number")
    content: Optional[str] = Field(default=None, description="Source code content around the location")


class DebugCommand(BaseModel):
    """Model for debug commands."""
    command: str = Field(..., description="Command type")
    session_id: str = Field(..., description="Target session ID")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Command parameters")


class DebugResponse(BaseModel):
    """Model for debug command responses."""
    success: bool = Field(..., description="Whether the command succeeded")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Response data")
    error: Optional[str] = Field(default=None, description="Error message if command failed") 