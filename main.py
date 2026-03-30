"""
Smart Location Intelligence Agent — CLI Runner.

Usage:
    python main.py
    python main.py --query "Tell me about animals near the Central Park Zoo"

Make sure the MCP Server is running first:
    cd mcp_server && python server.py
"""

import argparse
import sys

from agent.agent import SmartLocationAgent


def main():
    parser = argparse.ArgumentParser(description="Smart Location Intelligence Agent")
    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="Query to send to the agent (skips interactive mode)",
    )
    args = parser.parse_args()

    agent = SmartLocationAgent()

    if args.query:
        print("\n" + "=" * 60)
        response = agent.run(args.query)
        print("\n🗺️  Agent Response:\n")
        print(response)
        print("=" * 60)
        return

    # Interactive REPL mode
    print("\n🗺️  Smart Location Intelligence Agent")
    print("   Type your question, or 'quit' to exit.\n")
    print("   Example: Tell me about animals near the Central Park Zoo")
    print("-" * 60)

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            sys.exit(0)

        if not user_input:
            continue
        if user_input.lower() in {"quit", "exit", "q"}:
            print("Goodbye!")
            break

        print("\nAgent: Thinking...\n")
        try:
            response = agent.run(user_input)
            print(f"Agent:\n{response}")
        except Exception as e:
            print(f"[Error] {e}")


if __name__ == "__main__":
    main()
