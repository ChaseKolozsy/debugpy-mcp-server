#!/usr/bin/env python3
"""
Stdio wrapper for the Debugpy MCP Server.

This module provides stdio communication for the MCP server instead of HTTP.
"""

import asyncio
import sys
import logging
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool

from .debugpy_client import DebugpyClient
from .models import (
    DebugSession, Breakpoint, StackFrame, Variable,
    ExpressionResult, SourceLocation, ProcessInfo
)

# Configure logging to stderr so it doesn't interfere with stdio
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Create server instance
server = Server("debugpy-mcp-server")

# Global debugpy client instance
debugpy_client = DebugpyClient()

def format_response(data):
    """Format response data for MCP tool output."""
    try:
        import json
        if hasattr(data, 'model_dump'):
            return json.dumps(data.model_dump(), indent=2, ensure_ascii=False)
        elif isinstance(data, (dict, list)):
            return json.dumps(data, indent=2, ensure_ascii=False)
        else:
            return str(data)
    except Exception as e:
        return f"Error formatting response: {e}"

# ============================================================================
# TOOLS
# ============================================================================

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available debugging tools."""
    return [
        Tool(
            name="start_debug_session",
            description="Start a new debug session by connecting to a debugpy-enabled program",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {"type": "string", "default": "localhost"},
                    "port": {"type": "integer", "default": 5678},
                    "timeout": {"type": "integer", "default": 30}
                }
            }
        ),
        Tool(
            name="stop_debug_session",
            description="Stop and disconnect from a debug session",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string"}
                },
                "required": ["session_id"]
            }
        ),
        Tool(
            name="list_debug_sessions",
            description="List all active debug sessions",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="get_session_status",
            description="Get the status of a specific debug session",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string"}
                },
                "required": ["session_id"]
            }
        ),
        Tool(
            name="set_breakpoint",
            description="Set a breakpoint at the specified file and line",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string"},
                    "file_path": {"type": "string"},
                    "line_number": {"type": "integer"},
                    "condition": {"type": "string"}
                },
                "required": ["session_id", "file_path", "line_number"]
            }
        ),
        Tool(
            name="clear_breakpoint",
            description="Clear a specific breakpoint",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string"},
                    "breakpoint_id": {"type": "integer"}
                },
                "required": ["session_id", "breakpoint_id"]
            }
        ),
        Tool(
            name="list_breakpoints",
            description="List all breakpoints for a debug session",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string"}
                },
                "required": ["session_id"]
            }
        ),
        Tool(
            name="continue_execution",
            description="Continue program execution until next breakpoint or completion",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string"}
                },
                "required": ["session_id"]
            }
        ),
        Tool(
            name="step_into",
            description="Step into the next function call",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string"}
                },
                "required": ["session_id"]
            }
        ),
        Tool(
            name="step_over",
            description="Step over the current line",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string"}
                },
                "required": ["session_id"]
            }
        ),
        Tool(
            name="step_out",
            description="Step out of the current function",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string"}
                },
                "required": ["session_id"]
            }
        ),
        Tool(
            name="inspect_stack",
            description="Get the current call stack for the debug session",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string"}
                },
                "required": ["session_id"]
            }
        ),
        Tool(
            name="inspect_variables",
            description="Inspect variables in the specified stack frame",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string"},
                    "frame_id": {"type": "integer", "default": 0}
                },
                "required": ["session_id"]
            }
        ),
        Tool(
            name="evaluate_expression",
            description="Evaluate a Python expression in the debugging context",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string"},
                    "expression": {"type": "string"},
                    "frame_id": {"type": "integer"}
                },
                "required": ["session_id", "expression"]
            }
        ),
        Tool(
            name="get_source_code",
            description="Get source code around a specific location",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"},
                    "line_number": {"type": "integer"},
                    "context_lines": {"type": "integer", "default": 5}
                },
                "required": ["file_path", "line_number"]
            }
        ),
        Tool(
            name="list_debuggable_processes",
            description="List running Python processes that might be debuggable",
            inputSchema={"type": "object", "properties": {}}
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list:
    """Handle tool calls."""
    try:
        if name == "start_debug_session":
            host = arguments.get("host", "localhost")
            port = arguments.get("port", 5678)
            timeout = arguments.get("timeout", 30)
            
            session_id = debugpy_client.create_session(host, port, timeout)
            success = debugpy_client.connect_session(session_id)
            session = debugpy_client.get_session(session_id)
            
            result = {
                "success": success,
                "session_id": session_id,
                "session": session.model_dump() if session else None,
                "message": f"Connected to debug session at {host}:{port}" if success else "Failed to connect"
            }
            
        elif name == "stop_debug_session":
            session_id = arguments["session_id"]
            success = debugpy_client.disconnect_session(session_id)
            result = {
                "success": success,
                "session_id": session_id,
                "message": "Session disconnected successfully" if success else "Failed to disconnect session"
            }
            
        elif name == "list_debug_sessions":
            sessions = debugpy_client.list_sessions()
            result = {
                "success": True,
                "sessions": [session.model_dump() for session in sessions],
                "count": len(sessions)
            }
            
        elif name == "get_session_status":
            session_id = arguments["session_id"]
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
                
        elif name == "set_breakpoint":
            session_id = arguments["session_id"]
            file_path = arguments["file_path"]
            line_number = arguments["line_number"]
            condition = arguments.get("condition")
            
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
                
        elif name == "clear_breakpoint":
            session_id = arguments["session_id"]
            breakpoint_id = arguments["breakpoint_id"]
            success = debugpy_client.clear_breakpoint(session_id, breakpoint_id)
            result = {
                "success": success,
                "message": f"Breakpoint {breakpoint_id} cleared" if success else f"Failed to clear breakpoint {breakpoint_id}"
            }
            
        elif name == "list_breakpoints":
            session_id = arguments["session_id"]
            breakpoints = debugpy_client.list_breakpoints(session_id)
            result = {
                "success": True,
                "session_id": session_id,
                "breakpoints": [bp.model_dump() for bp in breakpoints],
                "count": len(breakpoints)
            }
            
        elif name == "continue_execution":
            session_id = arguments["session_id"]
            success = debugpy_client.continue_execution(session_id)
            result = {
                "success": success,
                "session_id": session_id,
                "message": "Execution continued" if success else "Failed to continue execution"
            }
            
        elif name == "step_into":
            session_id = arguments["session_id"]
            success = debugpy_client.step_into(session_id)
            result = {
                "success": success,
                "session_id": session_id,
                "message": "Stepped into function" if success else "Failed to step into function"
            }
            
        elif name == "step_over":
            session_id = arguments["session_id"]
            success = debugpy_client.step_over(session_id)
            result = {
                "success": success,
                "session_id": session_id,
                "message": "Stepped over line" if success else "Failed to step over line"
            }
            
        elif name == "step_out":
            session_id = arguments["session_id"]
            success = debugpy_client.step_out(session_id)
            result = {
                "success": success,
                "session_id": session_id,
                "message": "Stepped out of function" if success else "Failed to step out of function"
            }
            
        elif name == "inspect_stack":
            session_id = arguments["session_id"]
            frames = debugpy_client.get_stack_trace(session_id)
            result = {
                "success": True,
                "session_id": session_id,
                "stack_frames": [frame.model_dump() for frame in frames],
                "frame_count": len(frames)
            }
            
        elif name == "inspect_variables":
            session_id = arguments["session_id"]
            frame_id = arguments.get("frame_id", 0)
            variables = debugpy_client.get_variables(session_id, frame_id)
            result = {
                "success": True,
                "session_id": session_id,
                "frame_id": frame_id,
                "variables": [var.model_dump() for var in variables],
                "variable_count": len(variables)
            }
            
        elif name == "evaluate_expression":
            session_id = arguments["session_id"]
            expression = arguments["expression"]
            frame_id = arguments.get("frame_id")
            result_obj = debugpy_client.evaluate_expression(session_id, expression, frame_id)
            result = {
                "success": not result_obj.is_error,
                "session_id": session_id,
                "evaluation": result_obj.model_dump()
            }
            
        elif name == "get_source_code":
            file_path = arguments["file_path"]
            line_number = arguments["line_number"]
            context_lines = arguments.get("context_lines", 5)
            
            import os
            if not os.path.exists(file_path):
                result = {
                    "success": False,
                    "error": f"File not found: {file_path}"
                }
            else:
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
                
        elif name == "list_debuggable_processes":
            import psutil
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    proc_info = proc.info
                    if proc_info['name'] and 'python' in proc_info['name'].lower():
                        cmdline = proc_info.get('cmdline', [])
                        command_str = ' '.join(cmdline) if cmdline else ''
                        
                        is_debuggable = 'debugpy' in command_str
                        debugpy_port = None
                        
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
            
        else:
            result = {"success": False, "error": f"Unknown tool: {name}"}
            
        return [format_response(result)]
        
    except Exception as e:
        logger.error(f"Error handling tool {name}: {e}")
        return [format_response({"success": False, "error": str(e)})]

async def main():
    """Main entry point for stdio server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main()) 