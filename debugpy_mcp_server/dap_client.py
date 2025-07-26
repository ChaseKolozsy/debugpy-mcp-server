"""
Debug Adapter Protocol (DAP) client implementation for debugpy.
"""

import json
import socket
import threading
import time
import uuid
from typing import Any, Dict, List, Optional, Callable
import logging

logger = logging.getLogger(__name__)


class DAPClient:
    """Debug Adapter Protocol client for communicating with debugpy."""
    
    def __init__(self):
        self.socket: Optional[socket.socket] = None
        self.sequence_number = 1
        self.pending_requests: Dict[int, threading.Event] = {}
        self.responses: Dict[int, Dict[str, Any]] = {}
        self.event_callbacks: Dict[str, Callable] = {}
        self.is_connected = False
        self.receive_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        
    def connect(self, host: str, port: int, timeout: int = 30) -> bool:
        """Connect to the debug adapter."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(timeout)
            self.socket.connect((host, port))
            
            self.is_connected = True
            
            # Start receiving thread
            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread.start()
            
            # Send initialize request
            response = self._send_request("initialize", {
                "clientID": "debugpy-mcp-server",
                "clientName": "Debugpy MCP Server",
                "adapterID": "python",
                "pathFormat": "path",
                "linesStartAt1": True,
                "columnsStartAt1": True,
                "supportsVariableType": True,
                "supportsVariablePaging": True,
                "supportsRunInTerminalRequest": False,
                "supportsMemoryReferences": False,
                "supportsProgressReporting": False,
                "supportsInvalidatedEvent": False
            })
            
            if response and response.get("success"):
                # Send configuration done - debugpy handles attach automatically when initialized
                config_response = self._send_request("configurationDone", {})
                return config_response and config_response.get("success", True)
                    
            return False
            
        except Exception as e:
            logger.error(f"Failed to connect to DAP server: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """Disconnect from the debug adapter."""
        self.is_connected = False
        
        try:
            if self.socket:
                # Send disconnect request
                self._send_request("disconnect", {"restart": False})
                self.socket.close()
                self.socket = None
        except:
            pass
            
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=1)
    
    def set_breakpoints(self, file_path: str, lines: List[int], 
                       conditions: Optional[List[Optional[str]]] = None) -> Dict[str, Any]:
        """Set breakpoints in a file."""
        breakpoints = []
        for i, line in enumerate(lines):
            bp = {"line": line}
            if conditions and i < len(conditions) and conditions[i]:
                bp["condition"] = conditions[i]
            breakpoints.append(bp)
            
        return self._send_request("setBreakpoints", {
            "source": {"path": file_path},
            "breakpoints": breakpoints
        })
    
    def continue_execution(self, thread_id: int = 1) -> Dict[str, Any]:
        """Continue execution."""
        return self._send_request("continue", {"threadId": thread_id})
    
    def step_over(self, thread_id: int = 1) -> Dict[str, Any]:
        """Step over the current line."""
        return self._send_request("next", {"threadId": thread_id})
    
    def step_into(self, thread_id: int = 1) -> Dict[str, Any]:
        """Step into the current function call."""
        return self._send_request("stepIn", {"threadId": thread_id})
    
    def step_out(self, thread_id: int = 1) -> Dict[str, Any]:
        """Step out of the current function."""
        return self._send_request("stepOut", {"threadId": thread_id})
    
    def get_stack_trace(self, thread_id: int = 1) -> Dict[str, Any]:
        """Get the stack trace."""
        return self._send_request("stackTrace", {"threadId": thread_id})
    
    def get_scopes(self, frame_id: int) -> Dict[str, Any]:
        """Get scopes for a frame."""
        return self._send_request("scopes", {"frameId": frame_id})
    
    def get_variables(self, variables_reference: int) -> Dict[str, Any]:
        """Get variables for a scope."""
        return self._send_request("variables", {"variablesReference": variables_reference})
    
    def evaluate(self, expression: str, frame_id: Optional[int] = None, 
                context: str = "repl") -> Dict[str, Any]:
        """Evaluate an expression."""
        request_data = {
            "expression": expression,
            "context": context
        }
        if frame_id is not None:
            request_data["frameId"] = frame_id
        return self._send_request("evaluate", request_data)
    
    def get_threads(self) -> Dict[str, Any]:
        """Get available threads."""
        return self._send_request("threads", {})
    
    def _send_request(self, command: str, arguments: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send a DAP request and wait for response."""
        if not self.is_connected or not self.socket:
            return None
            
        with self.lock:
            seq = self.sequence_number
            self.sequence_number += 1
        
        request = {
            "seq": seq,
            "type": "request",
            "command": command,
            "arguments": arguments
        }
        
        # Prepare to wait for response
        event = threading.Event()
        self.pending_requests[seq] = event
        
        try:
            # Send request
            message = json.dumps(request)
            content = f"Content-Length: {len(message)}\r\n\r\n{message}"
            self.socket.send(content.encode('utf-8'))
            
            # Wait for response
            if event.wait(timeout=10):
                response = self.responses.pop(seq, None)
                return response
            else:
                logger.error(f"Timeout waiting for response to {command}")
                return None
                
        except Exception as e:
            logger.error(f"Error sending request {command}: {e}")
            return None
        finally:
            self.pending_requests.pop(seq, None)
    
    def _receive_loop(self):
        """Receive and process DAP messages."""
        buffer = b""
        
        while self.is_connected and self.socket:
            try:
                data = self.socket.recv(4096)
                if not data:
                    break
                    
                buffer += data
                
                # Process complete messages
                while b'\r\n\r\n' in buffer:
                    header_end = buffer.find(b'\r\n\r\n')
                    header = buffer[:header_end].decode('utf-8')
                    
                    # Parse Content-Length
                    content_length = 0
                    for line in header.split('\r\n'):
                        if line.startswith('Content-Length:'):
                            content_length = int(line.split(':')[1].strip())
                            break
                    
                    if len(buffer) >= header_end + 4 + content_length:
                        # We have a complete message
                        content_start = header_end + 4
                        content_end = content_start + content_length
                        content = buffer[content_start:content_end].decode('utf-8')
                        buffer = buffer[content_end:]
                        
                        # Process the message
                        try:
                            message = json.loads(content)
                            self._handle_message(message)
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse DAP message: {e}")
                    else:
                        # Wait for more data
                        break
                        
            except Exception as e:
                if self.is_connected:
                    logger.error(f"Error in receive loop: {e}")
                break
    
    def _handle_message(self, message: Dict[str, Any]):
        """Handle a DAP message."""
        msg_type = message.get("type")
        
        if msg_type == "response":
            # Handle response
            seq = message.get("request_seq")
            if seq in self.pending_requests:
                self.responses[seq] = message
                self.pending_requests[seq].set()
                
        elif msg_type == "event":
            # Handle event
            event = message.get("event")
            if event in self.event_callbacks:
                self.event_callbacks[event](message.get("body", {}))
            
            # Log important events
            if event in ["stopped", "continued", "terminated", "exited"]:
                logger.info(f"DAP Event: {event} - {message.get('body', {})}")
    
    def on_event(self, event_name: str, callback: Callable):
        """Register an event callback."""
        self.event_callbacks[event_name] = callback 