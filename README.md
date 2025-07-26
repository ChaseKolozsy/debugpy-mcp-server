# Debugpy MCP Server

A Model Context Protocol (MCP) server that provides debugging capabilities using Python's debugpy library. This server allows LLMs and agents to step through Python programs, set breakpoints, inspect variables, and control debugging sessions.

## Features

- **Debugger Control**: Start, stop, and manage debugpy debugging sessions
- **Breakpoint Management**: Set, clear, and list breakpoints in target programs
- **Step Debugging**: Step into, over, and out of code execution
- **Variable Inspection**: Inspect local and global variables at breakpoints
- **Stack Inspection**: View call stack and navigate stack frames
- **Expression Evaluation**: Evaluate Python expressions in debugging context
- **Process Management**: Monitor and control target debugging processes

## Installation

### Prerequisites

- Python 3.10 or later
- Target Python program that can be run with debugpy

### Setup

1. Install the package:
   ```bash
   pip install -r requirements.txt
   ```

2. Make the server executable:
   ```bash
   chmod +x debugpy_mcp_server/server.py
   ```

## Usage

### Starting the MCP Server

Run the debugpy MCP server:
```bash
python -m debugpy_mcp_server.server
```

The server will start and listen for MCP connections.

### Connecting Target Programs

To make a Python program debuggable, start it with debugpy:
```bash
python -m debugpy --listen 5678 --wait-for-client your_program.py
```

Or integrate debugpy into your program:
```python
import debugpy
debugpy.listen(5678)
debugpy.wait_for_client()  # Optional: wait for debugger to attach
```

## Available MCP Tools

### Debugger Management

- `start_debug_session`: Connect to a debugpy-enabled program
- `stop_debug_session`: Disconnect from debugging session
- `list_debug_sessions`: Show active debugging sessions
- `get_session_status`: Get status of a debugging session

### Breakpoint Management

- `set_breakpoint`: Set a breakpoint at specified file and line
- `clear_breakpoint`: Remove a breakpoint
- `list_breakpoints`: Show all active breakpoints
- `enable_breakpoint`: Enable a disabled breakpoint
- `disable_breakpoint`: Disable a breakpoint without removing it

### Execution Control

- `continue_execution`: Continue program execution
- `step_into`: Step into function calls
- `step_over`: Step over function calls
- `step_out`: Step out of current function
- `pause_execution`: Pause program execution

### Inspection Tools

- `inspect_variables`: Get local and global variables at current position
- `inspect_stack`: Get call stack information
- `evaluate_expression`: Evaluate Python expression in debugging context
- `get_source_code`: Get source code around current execution point

### Process Management

- `list_debuggable_processes`: Find processes that can be debugged
- `attach_to_process`: Attach debugger to a running process
- `detach_from_process`: Detach from a debugging process

## Example Usage with LLM/Agent

1. **Start your target program with debugpy**:
   ```bash
   python -m debugpy --listen 5678 --wait-for-client my_script.py
   ```

2. **Connect the MCP server to the debugging session**:
   ```
   start_debug_session(host="localhost", port=5678)
   ```

3. **Set breakpoints and control execution**:
   ```
   set_breakpoint(file_path="my_script.py", line_number=10)
   continue_execution()
   ```

4. **Inspect program state when breakpoint is hit**:
   ```
   inspect_variables()
   inspect_stack()
   evaluate_expression(expression="my_variable * 2")
   ```

5. **Step through code**:
   ```
   step_over()
   step_into()
   step_out()
   ```

## Configuration

The server can be configured using environment variables:

- `DEBUGPY_MCP_HOST`: Default host for debugpy connections (default: "localhost")
- `DEBUGPY_MCP_PORT`: Default port for debugpy connections (default: 5678)
- `DEBUGPY_MCP_TIMEOUT`: Connection timeout in seconds (default: 30)

## Error Handling

The server provides detailed error messages for common debugging scenarios:
- Connection failures to target programs
- Invalid breakpoint locations
- Expression evaluation errors
- Process attachment issues

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 