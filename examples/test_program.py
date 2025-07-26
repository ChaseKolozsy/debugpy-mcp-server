#!/usr/bin/env python3
"""
Example program for testing the debugpy MCP server.

This program demonstrates various debugging scenarios including:
- Function calls and returns
- Variable manipulation
- Loops and conditionals
- Exception handling
"""

import debugpy
import time


def fibonacci(n):
    """Calculate fibonacci number using recursion."""
    if n <= 1:
        return n
    else:
        return fibonacci(n-1) + fibonacci(n-2)


def process_numbers(numbers):
    """Process a list of numbers with various operations."""
    results = []
    
    for i, num in enumerate(numbers):
        print(f"Processing number {i}: {num}")
        
        # Multiply by 2
        doubled = num * 2
        
        # Calculate fibonacci if small enough
        if num < 10:
            fib_result = fibonacci(num)
            results.append({
                'original': num,
                'doubled': doubled,
                'fibonacci': fib_result
            })
        else:
            results.append({
                'original': num,
                'doubled': doubled,
                'fibonacci': None
            })
        
        # Add a small delay to make debugging easier
        time.sleep(0.1)
    
    return results


def handle_user_input():
    """Handle user input with error handling."""
    try:
        user_input = input("Enter numbers separated by spaces: ")
        numbers = [int(x.strip()) for x in user_input.split()]
        
        if not numbers:
            raise ValueError("No numbers provided")
        
        return numbers
        
    except ValueError as e:
        print(f"Error parsing input: {e}")
        return [1, 2, 3, 5, 8]  # Default numbers


def main():
    """Main function to demonstrate debugging."""
    print("Debugpy MCP Server Test Program")
    print("=" * 40)
    
    # Start debugpy server
    print("Starting debugpy server on port 5678...")
    debugpy.listen(5678)
    print("Waiting for debugger to attach...")
    debugpy.wait_for_client()
    
    print("Debugger attached! Starting program execution...")
    
    # Get numbers from user
    numbers = handle_user_input()
    print(f"Processing numbers: {numbers}")
    
    # Process the numbers
    results = process_numbers(numbers)
    
    # Display results
    print("\nResults:")
    print("-" * 20)
    for result in results:
        print(f"Number: {result['original']}")
        print(f"  Doubled: {result['doubled']}")
        print(f"  Fibonacci: {result['fibonacci']}")
        print()
    
    # Calculate sum of doubled values
    total_doubled = sum(r['doubled'] for r in results)
    print(f"Total of doubled values: {total_doubled}")
    
    # Calculate average
    if results:
        avg_original = sum(r['original'] for r in results) / len(results)
        print(f"Average of original values: {avg_original:.2f}")
    
    print("Program completed!")


if __name__ == "__main__":
    main() 