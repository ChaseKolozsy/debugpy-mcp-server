#!/usr/bin/env python3
"""
Simple example script for debugging with the MCP server.
"""

import debugpy
import time
import signal
import sys

def signal_handler(sig, frame):
    """Handle script termination and cleanup debugpy."""
    print("\nReceived interrupt signal. Cleaning up debugpy connection...")
    try:
        debugpy.disconnect()
    except:
        pass
    print("Debugpy connection closed.")
    sys.exit(0)

def calculate_fibonacci(n):
    """Calculate fibonacci number."""
    if n <= 1:
        return n
    else:
        return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

def main():
    # Set up signal handler for proper cleanup
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start debugpy server on port 5678
        print("Starting debugpy server on port 5678...")
        debugpy.listen(5678)
        
        # Wait for debugger to attach (optional)
        print("Waiting for debugger to attach...")
        debugpy.wait_for_client()
        
        print("Debugger attached! Starting program execution...")
        
        # Your actual program logic
        numbers = [1, 2, 3, 5, 8]
        
        for num in numbers:
            print(f"Calculating fibonacci({num})")
            result = calculate_fibonacci(num)
            print(f"fibonacci({num}) = {result}")
            
            # Add a small delay to make debugging easier
            time.sleep(1)
        
        print("Program completed!")
        
        # Keep the connection alive for a bit to allow final debugging
        print("Keeping debugpy connection alive for 30 seconds...")
        print("Press Ctrl+C to exit early.")
        time.sleep(30)
        
    except KeyboardInterrupt:
        print("\nProgram interrupted by user.")
    finally:
        # Always clean up debugpy connection
        print("Cleaning up debugpy connection...")
        try:
            debugpy.disconnect()
        except:
            pass
        print("Debugpy connection closed. Exiting.")

if __name__ == "__main__":
    main() 