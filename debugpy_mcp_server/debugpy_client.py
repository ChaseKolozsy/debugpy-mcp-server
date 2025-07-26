"""
Debugpy client wrapper for managing debugging sessions.
"""

import json
import socket
import time
import threading
import uuid
from typing import Any, Dict, List, Optional, Tuple
import logging

from .models import (
    DebugSession, Breakpoint, StackFrame, Variable, 
    ExpressionResult, SourceLocation, ProcessInfo
)

logger = logging.getLogger(__name__)


class DebugpyClient:
    """Client for communicating with debugpy debug adapters."""
    
    def __init__(self):
        self.sessions: Dict[str, DebugSession] = {}
        self.connections: Dict[str, socket.socket] = {}
        self.breakpoints: Dict[str, List[Breakpoint]] = {}
        self.sequence_number = 1
        self.event_handlers = []
        
    def create_session(self, host: str = "localhost", port: int = 5678, timeout: int = 30) -> str:
        """Create a new debug session."""
        session_id = str(uuid.uuid4())
        session = DebugSession(
            session_id=session_id,
            host=host,
            port=port,
            status="created"
        )
        
        self.sessions[session_id] = session
        self.breakpoints[session_id] = []
        
        logger.info(f"Created debug session {session_id} for {host}:{port}")
        return session_id
    
    def connect_session(self, session_id: str) -> bool:
        """Connect to a debugpy session."""
        if session_id not in self.sessions:
            logger.error(f"Session {session_id} not found")
            return False
            
        session = self.sessions[session_id]
        
        try:
            # Create socket connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(30)
            sock.connect((session.host, session.port))
            
            self.connections[session_id] = sock
            
            # Initialize debug adapter protocol
            self._send_request(session_id, "initialize", {
                "clientID": "debugpy-mcp-server",
                "clientName": "Debugpy MCP Server",
                "adapterID": "python",
                "pathFormat": "path",
                "linesStartAt1": True,
                "columnsStartAt1": True,
                "supportsVariableType": True,
                "supportsVariablePaging": True,
                "supportsRunInTerminalRequest": False
            })
            
            # Update session status
            session.is_connected = True
            session.status = "connected"
            
            logger.info(f"Connected to debug session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to session {session_id}: {e}")
            session.status = f"connection_failed: {e}"
            return False
    
    def disconnect_session(self, session_id: str) -> bool:
        """Disconnect from a debug session."""
        if session_id not in self.sessions:
            return False
            
        try:
            if session_id in self.connections:
                self.connections[session_id].close()
                del self.connections[session_id]
            
            session = self.sessions[session_id]
            session.is_connected = False
            session.status = "disconnected"
            
            logger.info(f"Disconnected from debug session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error disconnecting session {session_id}: {e}")
            return False
    
    def set_breakpoint(self, session_id: str, file_path: str, line_number: int, 
                      condition: Optional[str] = None) -> Optional[Breakpoint]:
        """Set a breakpoint in the target program."""
        if session_id not in self.sessions or not self.sessions[session_id].is_connected:
            logger.error(f"Session {session_id} not connected")
            return None
            
        try:
            breakpoint_id = len(self.breakpoints[session_id]) + 1
            
            # Send setBreakpoints request
            response = self._send_request(session_id, "setBreakpoints", {
                "source": {"path": file_path},
                "breakpoints": [{
                    "line": line_number,
                    "condition": condition
                }]
            })
            
            if response and response.get("success"):
                breakpoint = Breakpoint(
                    breakpoint_id=breakpoint_id,
                    file_path=file_path,
                    line_number=line_number,
                    condition=condition
                )
                
                self.breakpoints[session_id].append(breakpoint)
                logger.info(f"Set breakpoint {breakpoint_id} at {file_path}:{line_number}")
                return breakpoint
                
        except Exception as e:
            logger.error(f"Failed to set breakpoint: {e}")
            
        return None
    
    def clear_breakpoint(self, session_id: str, breakpoint_id: int) -> bool:
        """Clear a breakpoint."""
        if session_id not in self.breakpoints:
            return False
            
        breakpoints = self.breakpoints[session_id]
        for i, bp in enumerate(breakpoints):
            if bp.breakpoint_id == breakpoint_id:
                # Send clearBreakpoints request
                try:
                    self._send_request(session_id, "setBreakpoints", {
                        "source": {"path": bp.file_path},
                        "breakpoints": []
                    })
                    
                    breakpoints.pop(i)
                    logger.info(f"Cleared breakpoint {breakpoint_id}")
                    return True
                    
                except Exception as e:
                    logger.error(f"Failed to clear breakpoint: {e}")
                    
        return False
    
    def continue_execution(self, session_id: str) -> bool:
        """Continue program execution."""
        try:
            response = self._send_request(session_id, "continue", {
                "threadId": 1  # Assume main thread
            })
            return response and response.get("success", False)
            
        except Exception as e:
            logger.error(f"Failed to continue execution: {e}")
            return False
    
    def step_over(self, session_id: str) -> bool:
        """Step over the current line."""
        try:
            response = self._send_request(session_id, "next", {
                "threadId": 1
            })
            return response and response.get("success", False)
            
        except Exception as e:
            logger.error(f"Failed to step over: {e}")
            return False
    
    def step_into(self, session_id: str) -> bool:
        """Step into the current function call."""
        try:
            response = self._send_request(session_id, "stepIn", {
                "threadId": 1
            })
            return response and response.get("success", False)
            
        except Exception as e:
            logger.error(f"Failed to step into: {e}")
            return False
    
    def step_out(self, session_id: str) -> bool:
        """Step out of the current function."""
        try:
            response = self._send_request(session_id, "stepOut", {
                "threadId": 1
            })
            return response and response.get("success", False)
            
        except Exception as e:
            logger.error(f"Failed to step out: {e}")
            return False
    
    def get_stack_trace(self, session_id: str) -> List[StackFrame]:
        """Get the current stack trace."""
        try:
            response = self._send_request(session_id, "stackTrace", {
                "threadId": 1
            })
            
            if response and response.get("success"):
                frames = []
                for frame_data in response.get("body", {}).get("stackFrames", []):
                    frame = StackFrame(
                        frame_id=frame_data.get("id"),
                        name=frame_data.get("name"),
                        file_path=frame_data.get("source", {}).get("path", ""),
                        line_number=frame_data.get("line"),
                        column=frame_data.get("column")
                    )
                    frames.append(frame)
                
                return frames
                
        except Exception as e:
            logger.error(f"Failed to get stack trace: {e}")
            
        return []
    
    def get_variables(self, session_id: str, frame_id: int) -> List[Variable]:
        """Get variables for a specific stack frame."""
        try:
            # Get scopes first
            scopes_response = self._send_request(session_id, "scopes", {
                "frameId": frame_id
            })
            
            if not scopes_response or not scopes_response.get("success"):
                return []
            
            variables = []
            for scope in scopes_response.get("body", {}).get("scopes", []):
                scope_name = scope.get("name", "unknown")
                variables_ref = scope.get("variablesReference")
                
                if variables_ref:
                    vars_response = self._send_request(session_id, "variables", {
                        "variablesReference": variables_ref
                    })
                    
                    if vars_response and vars_response.get("success"):
                        for var_data in vars_response.get("body", {}).get("variables", []):
                            variable = Variable(
                                name=var_data.get("name"),
                                value=var_data.get("value"),
                                type=var_data.get("type", "unknown"),
                                scope=scope_name,
                                is_expandable=var_data.get("variablesReference", 0) > 0
                            )
                            variables.append(variable)
            
            return variables
            
        except Exception as e:
            logger.error(f"Failed to get variables: {e}")
            return []
    
    def evaluate_expression(self, session_id: str, expression: str, 
                          frame_id: Optional[int] = None) -> ExpressionResult:
        """Evaluate an expression in the debugging context."""
        try:
            request_data = {
                "expression": expression,
                "context": "repl"
            }
            
            if frame_id is not None:
                request_data["frameId"] = frame_id
            
            response = self._send_request(session_id, "evaluate", request_data)
            
            if response and response.get("success"):
                body = response.get("body", {})
                return ExpressionResult(
                    expression=expression,
                    result=body.get("result", ""),
                    type=body.get("type", "unknown"),
                    is_error=False
                )
            else:
                error_msg = response.get("message", "Unknown error") if response else "No response"
                return ExpressionResult(
                    expression=expression,
                    result="",
                    type="error",
                    is_error=True,
                    error_message=error_msg
                )
                
        except Exception as e:
            logger.error(f"Failed to evaluate expression: {e}")
            return ExpressionResult(
                expression=expression,
                result="",
                type="error",
                is_error=True,
                error_message=str(e)
            )
    
    def _send_request(self, session_id: str, command: str, arguments: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send a DAP request to the debug session."""
        if session_id not in self.connections:
            logger.error(f"No connection for session {session_id}")
            return None
            
        try:
            seq = self.sequence_number
            self.sequence_number += 1
            
            request = {
                "seq": seq,
                "type": "request",
                "command": command,
                "arguments": arguments
            }
            
            # Send request
            message = json.dumps(request)
            content_length = len(message.encode('utf-8'))
            
            sock = self.connections[session_id]
            sock.send(f"Content-Length: {content_length}\r\n\r\n{message}".encode('utf-8'))
            
            # Read response
            response = self._read_response(sock)
            return response
            
        except Exception as e:
            logger.error(f"Failed to send request {command}: {e}")
            return None
    
    def _read_response(self, sock: socket.socket) -> Optional[Dict[str, Any]]:
        """Read a DAP response from the socket."""
        try:
            # Read headers
            headers = {}
            while True:
                line = self._read_line(sock)
                if line == "":
                    break
                    
                if ":" in line:
                    key, value = line.split(":", 1)
                    headers[key.strip()] = value.strip()
            
            # Read content
            content_length = int(headers.get("Content-Length", 0))
            if content_length > 0:
                content = sock.recv(content_length).decode('utf-8')
                return json.loads(content)
                
        except Exception as e:
            logger.error(f"Failed to read response: {e}")
            
        return None
    
    def _read_line(self, sock: socket.socket) -> str:
        """Read a line from the socket."""
        line = ""
        while True:
            char = sock.recv(1).decode('utf-8')
            if char == '\n':
                break
            elif char != '\r':
                line += char
        return line
    
    def get_session(self, session_id: str) -> Optional[DebugSession]:
        """Get a debug session by ID."""
        return self.sessions.get(session_id)
    
    def list_sessions(self) -> List[DebugSession]:
        """List all debug sessions."""
        return list(self.sessions.values())
    
    def list_breakpoints(self, session_id: str) -> List[Breakpoint]:
        """List breakpoints for a session."""
        return self.breakpoints.get(session_id, []) 