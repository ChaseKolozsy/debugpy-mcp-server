# Debugpy MCP Server Usage Guide

This guide shows you how to connect scripts to the debugpy MCP server for interactive debugging.

## Method 1: Run Script with Debugpy Command Line

**No code changes needed!** Run any existing Python script with debugpy:

```bash
# Basic usage - waits for debugger to attach
python -m debugpy --listen 5678 --wait-for-client your_script.py

# Alternative - starts immediately, debugger can attach later
python -m debugpy --listen 5678 your_script.py

# Custom port
python -m debugpy --listen 0.0.0.0:9000 --wait-for-client your_script.py
```

## Method 2: Add Debugpy to Your Script

Modify your script to include debugpy:

```python
import debugpy

def main():
    # Start debugpy server
    debugpy.listen(5678)
    
    # Optional: wait for debugger to attach
    debugpy.wait_for_client()
    
    # Your code here
    print("Hello, debugger!")

if __name__ == "__main__":
    main()
```

## Using the MCP Server to Debug

### Step 1: Start Your Script

Choose one of the methods above to start your script with debugpy.

### Step 2: Connect via MCP Tools

Now use the MCP tools in Cursor to connect and debug:

#### Connect to the Debug Session
```
start_debug_session(host="localhost", port=5678)
```
This returns a `session_id` you'll use for all other operations.

#### Set Breakpoints
```
set_breakpoint(session_id="your-session-id", file_path="/path/to/your_script.py", line_number=10)
```

#### Control Execution
```
# Continue execution until breakpoint
continue_execution(session_id="your-session-id")

# Step through code
step_over(session_id="your-session-id")
step_into(session_id="your-session-id")
step_out(session_id="your-session-id")
```

#### Inspect Program State
```
# View call stack
inspect_stack(session_id="your-session-id")

# Examine variables
inspect_variables(session_id="your-session-id", frame_id=0)

# Evaluate expressions
evaluate_expression(session_id="your-session-id", expression="my_variable * 2")
```

#### View Source Code
```
get_source_code(file_path="/path/to/your_script.py", line_number=15, context_lines=5)
```

### Step 3: Find Running Processes

If you forget which processes are debuggable:

```
list_debuggable_processes()
```

This shows all Python processes and highlights which ones have debugpy enabled.

## Example Debugging Session

### 1. Start the example script:
```bash
cd submodules/debugpy-mcp-server
python examples/simple_debug_example.py
```

### 2. In Cursor, connect to the session:
```
start_debug_session()
```

### 3. Set a breakpoint in the fibonacci function:
```
set_breakpoint(session_id="<session-id>", file_path="examples/simple_debug_example.py", line_number=9)
```

### 4. Continue execution to hit the breakpoint:
```
continue_execution(session_id="<session-id>")
```

### 5. Inspect the current state:
```
inspect_variables(session_id="<session-id>")
inspect_stack(session_id="<session-id>")
```

### 6. Step through the code:
```
step_over(session_id="<session-id>")
```

### 7. Evaluate expressions:
```
evaluate_expression(session_id="<session-id>", expression="n + 1")
```

## Tips

- **Multiple Sessions**: You can debug multiple scripts simultaneously by using different ports
- **Conditional Breakpoints**: Use the `condition` parameter in `set_breakpoint` for conditional breaks
- **Remote Debugging**: Change the host to debug scripts on other machines
- **Background Scripts**: Remove `debugpy.wait_for_client()` to let scripts start immediately

## Common Ports

- `5678` - Default debugpy port
- `5679` - Alternative for multiple sessions  
- `9000-9010` - Good range for multiple debugging sessions

## Troubleshooting

If connection fails:
1. Check the script is running and waiting for debugger
2. Verify the port number matches
3. Ensure no firewall blocking the port
4. Use `list_debuggable_processes()` to find active debugpy processes 