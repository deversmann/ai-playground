"""
CLI entry point for the AI Chatbot.

This is the main script for running the interactive chat CLI.

Usage:
    poetry run python -m cli.main

    Or with custom settings:
    poetry run python -m cli.main --api-url http://localhost:8000 --temperature 0.5

Example:
    $ poetry run python -m cli.main
    # Starts interactive chat session
"""

import argparse
import asyncio
import sys

from .interface import ChatInterface


def parse_args():
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="AI Chatbot CLI - Interactive chat with AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start with default settings
  poetry run python -m cli.main

  # Custom API URL
  poetry run python -m cli.main --api-url http://localhost:8080

  # Adjust temperature and max tokens
  poetry run python -m cli.main --temperature 0.5 --max-tokens 500

Commands within chat:
  /help      - Show help
  /stats     - Show conversation statistics
  /clear     - Clear screen
  /quit      - Exit chat
  Ctrl+C/D   - Exit chat
        """,
    )

    parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8000",
        help="API server URL (default: http://localhost:8000)",
    )

    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Response temperature 0.0-1.0 (default: 0.7)",
    )

    parser.add_argument(
        "--max-tokens",
        type=int,
        default=1000,
        help="Maximum tokens in response (default: 1000)",
    )

    return parser.parse_args()


async def main():
    """
    Main entry point for the CLI.

    Parses arguments and starts the interactive chat interface.
    """
    # Parse command-line arguments
    args = parse_args()

    # Validate arguments
    if not (0.0 <= args.temperature <= 1.0):
        print(f"Error: temperature must be between 0.0 and 1.0, got {args.temperature}")
        sys.exit(1)

    if args.max_tokens < 1:
        print(f"Error: max-tokens must be at least 1, got {args.max_tokens}")
        sys.exit(1)

    # Create and run interface
    interface = ChatInterface(
        api_url=args.api_url,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
    )

    try:
        await interface.run()
    except KeyboardInterrupt:
        print("\n\nInterrupted. Goodbye!")
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Run the async main function
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        print("\nGoodbye!")
        sys.exit(0)
