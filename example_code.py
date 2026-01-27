"""
Example Python file for demonstrating ContextViewer MCP.

This file contains various code patterns that you can select
and interact with using the ContextViewer.
"""


def fibonacci(n):
    """
    Calculate the nth Fibonacci number using recursion.

    This is an inefficient implementation that can be improved.
    Try selecting this function and asking Claude to refactor it!
    """
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


class DataProcessor:
    """A simple data processor class."""

    def __init__(self, data):
        self.data = data
        self.processed = False

    def process(self):
        """
        Process the data.

        Select this method and ask Claude what it does!
        """
        if not self.data:
            raise ValueError("No data to process")

        # Simulate processing
        result = []
        for item in self.data:
            if isinstance(item, str):
                result.append(item.upper())
            elif isinstance(item, int):
                result.append(item * 2)
            else:
                result.append(item)

        self.processed = True
        return result

    def reset(self):
        """Reset the processor state."""
        self.processed = False


def main():
    """
    Main function demonstrating the usage.

    Try selecting different parts:
    - Single lines
    - Functions
    - Class methods
    - The entire file

    Then ask Claude to:
    - Explain what the code does
    - Suggest improvements
    - Refactor for better performance
    - Add error handling
    - Write unit tests
    """
    # Example 1: Fibonacci
    print("Fibonacci numbers:")
    for i in range(10):
        print(f"F({i}) = {fibonacci(i)}")

    # Example 2: Data processor
    processor = DataProcessor(["hello", "world", 42, 3.14])
    result = processor.process()
    print(f"Processed data: {result}")


if __name__ == "__main__":
    main()
