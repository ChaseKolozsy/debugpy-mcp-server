#!/usr/bin/env python3
"""
Test script for the debugpy MCP server.

This script tests basic functionality without requiring a full MCP client.
"""

import sys
import os
import json

# Add the debugpy_mcp_server package to the path
sys.path.insert(0, os.path.dirname(__file__))

try:
    from debugpy_mcp_server.models import DebugSession, Breakpoint, Variable
    from debugpy_mcp_server.debugpy_client import DebugpyClient
    print("✓ Successfully imported debugpy MCP server modules")
except ImportError as e:
    print(f"✗ Failed to import modules: {e}")
    sys.exit(1)

def test_models():
    """Test that Pydantic models work correctly."""
    print("\nTesting Pydantic models...")
    
    # Test DebugSession
    session = DebugSession(
        session_id="test-session",
        host="localhost",
        port=5678
    )
    print(f"✓ Created DebugSession: {session.session_id}")
    
    # Test Breakpoint
    breakpoint = Breakpoint(
        breakpoint_id=1,
        file_path="/test/file.py",
        line_number=10
    )
    print(f"✓ Created Breakpoint: {breakpoint.file_path}:{breakpoint.line_number}")
    
    # Test Variable
    variable = Variable(
        name="test_var",
        value="42",
        type="int",
        scope="local"
    )
    print(f"✓ Created Variable: {variable.name} = {variable.value}")

def test_debugpy_client():
    """Test DebugpyClient creation and basic methods."""
    print("\nTesting DebugpyClient...")
    
    client = DebugpyClient()
    print("✓ Created DebugpyClient instance")
    
    # Test session creation (without connecting)
    session_id = client.create_session("localhost", 5678)
    print(f"✓ Created session: {session_id}")
    
    # Test listing sessions
    sessions = client.list_sessions()
    print(f"✓ Listed sessions: {len(sessions)} session(s)")
    
    # Test getting session
    session = client.get_session(session_id)
    if session:
        print(f"✓ Retrieved session: {session.session_id}")
    else:
        print("✗ Failed to retrieve session")

def test_server_imports():
    """Test that the server module can be imported."""
    print("\nTesting server module imports...")
    
    try:
        # This will test if all dependencies are available
        from debugpy_mcp_server import server
        print("✓ Successfully imported server module")
        
        # Test that MCP tools are defined
        if hasattr(server, 'mcp'):
            print("✓ MCP server instance found")
        else:
            print("✗ MCP server instance not found")
            
    except ImportError as e:
        print(f"✗ Failed to import server module: {e}")

def main():
    """Run all tests."""
    print("Debugpy MCP Server Tests")
    print("=" * 40)
    
    test_models()
    test_debugpy_client()
    test_server_imports()
    
    print("\n" + "=" * 40)
    print("All tests completed!")
    print("\nTo start the MCP server, run:")
    print("  python -m debugpy_mcp_server.server")
    print("\nTo test with a debug target, run:")
    print("  python examples/test_program.py")

if __name__ == "__main__":
    main() 