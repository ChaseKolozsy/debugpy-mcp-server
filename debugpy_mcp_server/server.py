#!/usr/bin/env python3
"""
Debugpy MCP Server

A Model Context Protocol server providing debugging capabilities using debugpy.
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

from .debugpy_client import DebugpyClient
from .models import (
    DebugSession, Breakpoint, StackFrame, Variable,
    ExpressionResult, SourceLocation, ProcessInfo
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the FastMCP server
mcp = FastMCP("Debugpy MCP Server")

# Global debugpy client instance
debugpy_client = DebugpyClient()

def format_response(data: Any) -> str:
    """Format response data for MCP tool output."""
    try:
        if hasattr(data, 'model_dump'):
            return json.dumps(data.model_dump(), indent=2, ensure_ascii=False)
        elif isinstance(data, (dict, list)):
            return json.dumps(data, indent=2, ensure_ascii=False)
        else:
            return str(data)
    except Exception as e:
        return f"Error formatting response: {e}"

# ============================================================================
# DEBUG SESSION MANAGEMENT
# ============================================================================

@mcp.tool()
def start_debug_session(host: str = "localhost", port: int = 5678, timeout: int = 30) -> str:
    """
    Start a new debug session by connecting to a debugpy-enabled program.
    
    Args:
        host: Host address where debugpy is listening (default: localhost)
        port: Port number where debugpy is listening (default: 5678)
        timeout: Connection timeout in seconds (default: 30)
    
    Returns:
        JSON string with session information and connection status
    """
    try:
        # Create session
        session_id = debugpy_client.create_session(host, port, timeout)
        
        # Connect to the session
        success = debugpy_client.connect_session(session_id)
        
        session = debugpy_client.get_session(session_id)
        
        result = {
            "success": success,
            "session_id": session_id,
            "session": session.model_dump() if session else None,
            "message": f"Connected to debug session at {host}:{port}" if success else "Failed to connect"
        }
        
        return format_response(result)
        
    except Exception as e:
        logger.error(f"Failed to start debug session: {e}")
        return format_response({"success": False, "error": str(e)})

@mcp.tool()
def stop_debug_session(session_id: str) -> str:
    """
    Stop and disconnect from a debug session.
    
    Args:
        session_id: ID of the debug session to stop
    
    Returns:
        JSON string with disconnection status
    """
    try:
        success = debugpy_client.disconnect_session(session_id)
        
        result = {
            "success": success,
            "session_id": session_id,
            "message": "Session disconnected successfully" if success else "Failed to disconnect session"
        }
        
        return format_response(result)
        
    except Exception as e:
        logger.error(f"Failed to stop debug session: {e}")
        return format_response({"success": False, "error": str(e)})

@mcp.tool()
def list_debug_sessions() -> str:
    """
    List all active debug sessions.
    
    Returns:
        JSON string with list of all debug sessions
    """
    try:
        sessions = debugpy_client.list_sessions()
        
        result = {
            "success": True,
            "sessions": [session.model_dump() for session in sessions],
            "count": len(sessions)
        }
        
        return format_response(result)
        
    except Exception as e:
        logger.error(f"Failed to list debug sessions: {e}")
        return format_response({"success": False, "error": str(e)})

@mcp.tool()
def get_session_status(session_id: str) -> str:
    """
    Get the status of a specific debug session.
    
    Args:
        session_id: ID of the debug session
    
    Returns:
        JSON string with session status information
    """
    try:
        session = debugpy_client.get_session(session_id)
        
        if session:
            result = {
                "success": True,
                "session": session.model_dump(),
                "breakpoints_count": len(debugpy_client.list_breakpoints(session_id))
            }
        else:
            result = {
                "success": False,
                "error": f"Session {session_id} not found"
            }
        
        return format_response(result)
        
    except Exception as e:
        logger.error(f"Failed to get session status: {e}")
        return format_response({"success": False, "error": str(e)})

# ============================================================================
# BREAKPOINT MANAGEMENT
# ============================================================================

@mcp.tool()
def set_breakpoint(session_id: str, file_path: str, line_number: int, condition: Optional[str] = None) -> str:
    """
    Set a breakpoint at the specified file and line.
    
    Args:
        session_id: ID of the debug session
        file_path: Path to the source file
        line_number: Line number for the breakpoint
        condition: Optional condition for conditional breakpoint
    
    Returns:
        JSON string with breakpoint information
    """
    try:
        breakpoint = debugpy_client.set_breakpoint(session_id, file_path, line_number, condition)
        
        if breakpoint:
            result = {
                "success": True,
                "breakpoint": breakpoint.model_dump(),
                "message": f"Breakpoint set at {file_path}:{line_number}"
            }
        else:
            result = {
                "success": False,
                "error": f"Failed to set breakpoint at {file_path}:{line_number}"
            }
        
        return format_response(result)
        
    except Exception as e:
        logger.error(f"Failed to set breakpoint: {e}")
        return format_response({"success": False, "error": str(e)})

@mcp.tool()
def clear_breakpoint(session_id: str, breakpoint_id: int) -> str:
    """
    Clear a specific breakpoint.
    
    Args:
        session_id: ID of the debug session
        breakpoint_id: ID of the breakpoint to clear
    
    Returns:
        JSON string with operation status
    """
    try:
        success = debugpy_client.clear_breakpoint(session_id, breakpoint_id)
        
        result = {
            "success": success,
            "message": f"Breakpoint {breakpoint_id} cleared" if success else f"Failed to clear breakpoint {breakpoint_id}"
        }
        
        return format_response(result)
        
    except Exception as e:
        logger.error(f"Failed to clear breakpoint: {e}")
        return format_response({"success": False, "error": str(e)})

@mcp.tool()
def list_breakpoints(session_id: str) -> str:
    """
    List all breakpoints for a debug session.
    
    Args:
        session_id: ID of the debug session
    
    Returns:
        JSON string with list of breakpoints
    """
    try:
        breakpoints = debugpy_client.list_breakpoints(session_id)
        
        result = {
            "success": True,
            "session_id": session_id,
            "breakpoints": [bp.model_dump() for bp in breakpoints],
            "count": len(breakpoints)
        }
        
        return format_response(result)
        
    except Exception as e:
        logger.error(f"Failed to list breakpoints: {e}")
        return format_response({"success": False, "error": str(e)})

# ============================================================================
# EXECUTION CONTROL
# ============================================================================

@mcp.tool()
def continue_execution(session_id: str) -> str:
    """
    Continue program execution until next breakpoint or completion.
    
    Args:
        session_id: ID of the debug session
    
    Returns:
        JSON string with execution status
    """
    try:
        success = debugpy_client.continue_execution(session_id)
        
        result = {
            "success": success,
            "session_id": session_id,
            "message": "Execution continued" if success else "Failed to continue execution"
        }
        
        return format_response(result)
        
    except Exception as e:
        logger.error(f"Failed to continue execution: {e}")
        return format_response({"success": False, "error": str(e)})

@mcp.tool()
def step_into(session_id: str) -> str:
    """
    Step into the next function call.
    
    Args:
        session_id: ID of the debug session
    
    Returns:
        JSON string with step status
    """
    try:
        success = debugpy_client.step_into(session_id)
        
        result = {
            "success": success,
            "session_id": session_id,
            "message": "Stepped into function" if success else "Failed to step into function"
        }
        
        return format_response(result)
        
    except Exception as e:
        logger.error(f"Failed to step into: {e}")
        return format_response({"success": False, "error": str(e)})

@mcp.tool()
def step_over(session_id: str) -> str:
    """
    Step over the current line.
    
    Args:
        session_id: ID of the debug session
    
    Returns:
        JSON string with step status
    """
    try:
        success = debugpy_client.step_over(session_id)
        
        result = {
            "success": success,
            "session_id": session_id,
            "message": "Stepped over line" if success else "Failed to step over line"
        }
        
        return format_response(result)
        
    except Exception as e:
        logger.error(f"Failed to step over: {e}")
        return format_response({"success": False, "error": str(e)})

@mcp.tool()
def step_out(session_id: str) -> str:
    """
    Step out of the current function.
    
    Args:
        session_id: ID of the debug session
    
    Returns:
        JSON string with step status
    """
    try:
        success = debugpy_client.step_out(session_id)
        
        result = {
            "success": success,
            "session_id": session_id,
            "message": "Stepped out of function" if success else "Failed to step out of function"
        }
        
        return format_response(result)
        
    except Exception as e:
        logger.error(f"Failed to step out: {e}")
        return format_response({"success": False, "error": str(e)})

# ============================================================================
# INSPECTION TOOLS
# ============================================================================

@mcp.tool()
def inspect_stack(session_id: str) -> str:
    """
    Get the current call stack for the debug session.
    
    Args:
        session_id: ID of the debug session
    
    Returns:
        JSON string with stack trace information
    """
    try:
        frames = debugpy_client.get_stack_trace(session_id)
        
        result = {
            "success": True,
            "session_id": session_id,
            "stack_frames": [frame.model_dump() for frame in frames],
            "frame_count": len(frames)
        }
        
        return format_response(result)
        
    except Exception as e:
        logger.error(f"Failed to inspect stack: {e}")
        return format_response({"success": False, "error": str(e)})

@mcp.tool()
def inspect_variables(session_id: str, frame_id: int = 0) -> str:
    """
    Inspect variables in the specified stack frame.
    
    Args:
        session_id: ID of the debug session
        frame_id: ID of the stack frame to inspect (default: 0 for top frame)
    
    Returns:
        JSON string with variable information
    """
    try:
        variables = debugpy_client.get_variables(session_id, frame_id)
        
        result = {
            "success": True,
            "session_id": session_id,
            "frame_id": frame_id,
            "variables": [var.model_dump() for var in variables],
            "variable_count": len(variables)
        }
        
        return format_response(result)
        
    except Exception as e:
        logger.error(f"Failed to inspect variables: {e}")
        return format_response({"success": False, "error": str(e)})

@mcp.tool()
def evaluate_expression(session_id: str, expression: str, frame_id: Optional[int] = None) -> str:
    """
    Evaluate a Python expression in the debugging context.
    
    Args:
        session_id: ID of the debug session
        expression: Python expression to evaluate
        frame_id: Optional frame ID for context (default: current frame)
    
    Returns:
        JSON string with evaluation result
    """
    try:
        result_obj = debugpy_client.evaluate_expression(session_id, expression, frame_id)
        
        result = {
            "success": not result_obj.is_error,
            "session_id": session_id,
            "evaluation": result_obj.model_dump()
        }
        
        return format_response(result)
        
    except Exception as e:
        logger.error(f"Failed to evaluate expression: {e}")
        return format_response({"success": False, "error": str(e)})

@mcp.tool()
def get_source_code(file_path: str, line_number: int, context_lines: int = 5) -> str:
    """
    Get source code around a specific location.
    
    Args:
        file_path: Path to the source file
        line_number: Target line number
        context_lines: Number of lines to show before and after (default: 5)
    
    Returns:
        JSON string with source code content
    """
    try:
        if not os.path.exists(file_path):
            return format_response({
                "success": False,
                "error": f"File not found: {file_path}"
            })
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        start_line = max(0, line_number - context_lines - 1)
        end_line = min(len(lines), line_number + context_lines)
        
        source_lines = []
        for i in range(start_line, end_line):
            source_lines.append({
                "line_number": i + 1,
                "content": lines[i].rstrip(),
                "is_target": i + 1 == line_number
            })
        
        result = {
            "success": True,
            "file_path": file_path,
            "target_line": line_number,
            "context_lines": context_lines,
            "source": source_lines,
            "total_lines": len(lines)
        }
        
        return format_response(result)
        
    except Exception as e:
        logger.error(f"Failed to get source code: {e}")
        return format_response({"success": False, "error": str(e)})

# ============================================================================
# PROCESS MANAGEMENT
# ============================================================================

@mcp.tool()
def list_debuggable_processes() -> str:
    """
    List running Python processes that might be debuggable.
    
    Returns:
        JSON string with list of potentially debuggable processes
    """
    try:
        import psutil
        
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                proc_info = proc.info
                if proc_info['name'] and 'python' in proc_info['name'].lower():
                    cmdline = proc_info.get('cmdline', [])
                    command_str = ' '.join(cmdline) if cmdline else ''
                    
                    # Check if debugpy is mentioned in command line
                    is_debuggable = 'debugpy' in command_str
                    debugpy_port = None
                    
                    # Try to extract debugpy port
                    if is_debuggable and '--listen' in command_str:
                        try:
                            listen_idx = cmdline.index('--listen')
                            if listen_idx + 1 < len(cmdline):
                                addr = cmdline[listen_idx + 1]
                                if ':' in addr:
                                    debugpy_port = int(addr.split(':')[1])
                        except (ValueError, IndexError):
                            pass
                    
                    process_info = ProcessInfo(
                        process_id=proc_info['pid'],
                        name=proc_info['name'],
                        command_line=command_str,
                        is_debuggable=is_debuggable,
                        debugpy_port=debugpy_port
                    )
                    
                    processes.append(process_info)
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        result = {
            "success": True,
            "processes": [proc.model_dump() for proc in processes],
            "total_count": len(processes),
            "debuggable_count": len([p for p in processes if p.is_debuggable])
        }
        
        return format_response(result)
        
    except Exception as e:
        logger.error(f"Failed to list debuggable processes: {e}")
        return format_response({"success": False, "error": str(e)})

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point for the debugpy MCP server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Debugpy MCP Server")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level.upper()))
    
    logger.info(f"Starting Debugpy MCP Server on {args.host}:{args.port}")
    
    # Run the server
    mcp.run(host=args.host, port=args.port)

if __name__ == "__main__":
    main() 