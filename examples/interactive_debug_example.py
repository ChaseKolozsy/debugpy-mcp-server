#!/usr/bin/env python3
"""
Interactive debugging example that keeps the debugpy connection alive.
Perfect for learning how to use the debugpy MCP server.
"""

import debugpy
import time
import signal
import sys

# Global flag to control the main loop
keep_running = True

def signal_handler(sig, frame):
    """Handle script termination and cleanup debugpy."""
    global keep_running
    print("\nReceived interrupt signal. Stopping main loop...")
    keep_running = False

def fibonacci_sequence(n):
    """Generate fibonacci sequence up to n terms."""
    sequence = []
    a, b = 0, 1
    
    for i in range(n):
        sequence.append(a)
        a, b = b, a + b
    
    return sequence

def factorial(n):
    """Calculate factorial of n."""
    if n <= 1:
        return 1
    else:
        return n * factorial(n - 1)

def process_numbers(numbers):
    """Process a list of numbers with various operations."""
    results = {
        'fibonacci_sequences': [],
        'factorials': [],
        'squares': [],
        'cubes': []
    }
    
    for num in numbers:
        print(f"\nProcessing number: {num}")
        
        # Calculate fibonacci sequence
        if num <= 10:  # Limit to reasonable size
            fib_seq = fibonacci_sequence(num)
            results['fibonacci_sequences'].append({
                'n': num,
                'sequence': fib_seq
            })
            print(f"  Fibonacci sequence ({num} terms): {fib_seq}")
        
        # Calculate factorial
        if num <= 10:  # Prevent huge numbers
            fact = factorial(num)
            results['factorials'].append({
                'n': num,
                'factorial': fact
            })
            print(f"  Factorial of {num}: {fact}")
        
        # Calculate square and cube
        square = num ** 2
        cube = num ** 3
        results['squares'].append({'n': num, 'square': square})
        results['cubes'].append({'n': num, 'cube': cube})
        print(f"  {num}² = {square}, {num}³ = {cube}")
        
        # Add delay for easier debugging
        time.sleep(0.5)
    
    return results

def interactive_menu():
    """Interactive menu for debugging demonstration."""
    while keep_running:
        print("\n" + "="*50)
        print("INTERACTIVE DEBUGGING DEMO")
        print("="*50)
        print("1. Process default numbers [1, 2, 3, 5, 8]")
        print("2. Process custom numbers")
        print("3. Generate fibonacci sequence")
        print("4. Calculate factorial")
        print("5. Wait (good for setting breakpoints)")
        print("6. Exit")
        print("-"*50)
        
        try:
            choice = input("Enter your choice (1-6): ").strip()
            
            if choice == '1':
                print("\nProcessing default numbers...")
                numbers = [1, 2, 3, 5, 8]
                results = process_numbers(numbers)
                print(f"\nProcessing completed! Results: {len(results['factorials'])} calculations done.")
                
            elif choice == '2':
                try:
                    user_input = input("Enter numbers separated by spaces: ")
                    numbers = [int(x.strip()) for x in user_input.split() if x.strip()]
                    if numbers:
                        results = process_numbers(numbers)
                        print(f"\nProcessing completed! Results: {len(results['factorials'])} calculations done.")
                    else:
                        print("No valid numbers entered.")
                except ValueError:
                    print("Invalid input. Please enter numbers only.")
                    
            elif choice == '3':
                try:
                    n = int(input("Enter number of terms: "))
                    if 1 <= n <= 20:
                        sequence = fibonacci_sequence(n)
                        print(f"Fibonacci sequence ({n} terms): {sequence}")
                    else:
                        print("Please enter a number between 1 and 20.")
                except ValueError:
                    print("Invalid input. Please enter a number.")
                    
            elif choice == '4':
                try:
                    n = int(input("Enter number for factorial: "))
                    if 0 <= n <= 15:
                        result = factorial(n)
                        print(f"Factorial of {n}: {result}")
                    else:
                        print("Please enter a number between 0 and 15.")
                except ValueError:
                    print("Invalid input. Please enter a number.")
                    
            elif choice == '5':
                print("Waiting for 10 seconds... (perfect time to set breakpoints!)")
                for i in range(10, 0, -1):
                    print(f"  Waiting: {i} seconds remaining...")
                    time.sleep(1)
                    if not keep_running:
                        break
                print("Wait completed!")
                
            elif choice == '6':
                print("Exiting interactive demo...")
                break
                
            else:
                print("Invalid choice. Please enter 1-6.")
                
        except KeyboardInterrupt:
            print("\nInterrupted by user.")
            break
        except EOFError:
            print("\nEnd of input detected.")
            break

def main():
    """Main function with debugpy setup."""
    global keep_running
    
    # Set up signal handlers for clean shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        print("🐛 DEBUGPY INTERACTIVE DEMO")
        print("="*40)
        
        # Start debugpy server
        print("Starting debugpy server on port 5678...")
        debugpy.listen(5678)
        
        print("Waiting for debugger to attach...")
        print("Use the MCP tools to connect:")
        print("  start_debug_session(host='localhost', port=5678)")
        
        debugpy.wait_for_client()
        
        print("✅ Debugger attached!")
        print("You can now set breakpoints and debug interactively.")
        print("Try setting a breakpoint in one of these functions:")
        print("  - process_numbers() - line 35")
        print("  - fibonacci_sequence() - line 18") 
        print("  - factorial() - line 28")
        
        # Start interactive menu
        interactive_menu()
        
    except KeyboardInterrupt:
        print("\nProgram interrupted by user.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up debugpy connection
        print("\nCleaning up debugpy connection...")
        try:
            debugpy.disconnect()
            print("✅ Debugpy connection closed cleanly.")
        except:
            print("⚠️  Debugpy connection cleanup failed (this is usually OK).")
        
        print("👋 Goodbye!")

if __name__ == "__main__":
    main() 