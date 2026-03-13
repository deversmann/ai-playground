"""
Interactive chat interface using Rich.

This module provides a beautiful terminal UI for chatting with the AI.
It uses Rich for formatting and Prompt Toolkit for advanced input handling.

Features:
- Colored output
- Markdown rendering for AI responses
- Command history
- Special commands (/help, /quit, etc.)

Example:
    >>> interface = ChatInterface()
    >>> await interface.run()
"""

import asyncio
import uuid
from datetime import datetime

from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from .client import APIClient, APIClientError


class ChatInterface:
    """
    Interactive chat interface.

    Provides a REPL (Read-Eval-Print Loop) for chatting with the AI.
    Handles user input, displays responses, and manages the conversation.

    Attributes:
        console: Rich console for formatted output
        client: API client for backend communication
        session_id: Unique identifier for this chat session
        prompt_session: Prompt Toolkit session for input handling
    """

    def __init__(
        self,
        api_url: str = "http://localhost:8000",
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ):
        """
        Initialize the chat interface.

        Args:
            api_url: URL of the API server
            temperature: Default temperature for responses
            max_tokens: Default max tokens for responses

        Example:
            >>> interface = ChatInterface("http://localhost:8000")
        """
        self.console = Console()
        self.client = APIClient(base_url=api_url)
        self.session_id = str(uuid.uuid4())
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Create prompt session with history
        self.prompt_session: PromptSession = PromptSession(
            history=InMemoryHistory()
        )

        # Track conversation stats
        self.message_count = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    async def run(self):
        """
        Run the interactive chat interface.

        This is the main loop that:
        1. Displays welcome message
        2. Checks API health
        3. Accepts user input
        4. Sends messages to API
        5. Displays responses
        6. Repeats until user quits

        Example:
            >>> interface = ChatInterface()
            >>> await interface.run()
        """
        # Display welcome message
        self._display_welcome()

        # Check if API is available
        try:
            await self._check_api_health()
        except APIClientError as e:
            self.console.print(f"[red]Error: {e}[/red]")
            self.console.print(
                "\n[yellow]Make sure the API server is running:[/yellow]"
            )
            self.console.print("  poetry run uvicorn chatbot.main:app --reload\n")
            return

        # Main chat loop
        while True:
            try:
                # Get user input
                user_input = await self.prompt_session.prompt_async(
                    "\n[You] ",
                    multiline=False,
                )

                # Skip empty input
                if not user_input.strip():
                    continue

                # Check for commands
                if user_input.startswith("/"):
                    should_continue = await self._handle_command(user_input)
                    if not should_continue:
                        break
                    continue

                # Send message to API
                await self._send_and_display_message(user_input)

            except KeyboardInterrupt:
                # Ctrl+C pressed
                if await self._confirm_quit():
                    break
            except EOFError:
                # Ctrl+D pressed
                break
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")

        # Display goodbye message
        self._display_goodbye()

    def _display_welcome(self):
        """Display welcome message and instructions."""
        welcome_text = """
# AI Chatbot CLI

Welcome to the AI Chatbot! This is a learning project demonstrating
modern Python architecture with FastAPI, async/await, and provider abstraction.

**Phase 2: Now with conversation memory!** The AI remembers your conversation
and maintains context across multiple messages.

## Commands
- `/help` - Show help message
- `/stats` - Show conversation statistics
- `/new` - Start a new conversation
- `/clear` - Clear screen
- `/quit` or `/exit` - Exit the chat
- Press Ctrl+C or Ctrl+D to exit

## Tips
- Just type your message and press Enter
- Use Up/Down arrows for command history
- AI responses are rendered in Markdown
- The AI remembers previous messages in this session!

Let's chat!
        """
        panel = Panel(
            Markdown(welcome_text),
            title="[bold cyan]Welcome[/bold cyan]",
            border_style="cyan",
        )
        self.console.print(panel)

    async def _check_api_health(self):
        """Check if the API server is healthy and display info."""
        health = await self.client.health_check()
        info_table = Table(show_header=False, box=None, padding=(0, 2))
        info_table.add_row("Status:", f"[green]{health['status']}[/green]")
        info_table.add_row("Provider:", f"[cyan]{health['provider']}[/cyan]")
        info_table.add_row("Version:", f"{health['version']}")
        info_table.add_row("Session ID:", f"[dim]{self.session_id}[/dim]")

        self.console.print("\n[bold]API Status[/bold]")
        self.console.print(info_table)

    async def _send_and_display_message(self, message: str):
        """
        Send a message to the API and display the response.

        Args:
            message: User's message text
        """
        # Show "thinking" indicator
        with self.console.status("[cyan]Thinking...[/cyan]", spinner="dots"):
            try:
                response = await self.client.send_message(
                    message=message,
                    session_id=self.session_id,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
            except APIClientError as e:
                self.console.print(f"\n[red]Error: {e}[/red]")
                return

        # Update stats
        self.message_count += 1
        self.total_input_tokens += response["usage"]["input_tokens"]
        self.total_output_tokens += response["usage"]["output_tokens"]

        # Display AI response with Markdown rendering
        self.console.print("\n[bold green]AI:[/bold green]")
        self.console.print(Markdown(response["response"]))

        # Display token usage (dimmed)
        usage = response["usage"]
        self.console.print(
            f"\n[dim]Tokens: {usage['input_tokens']} in, "
            f"{usage['output_tokens']} out, "
            f"{usage['total_tokens']} total[/dim]"
        )

    async def _handle_command(self, command: str) -> bool:
        """
        Handle special commands.

        Args:
            command: Command string (starts with /)

        Returns:
            bool: True to continue chat loop, False to exit

        Commands:
            /help - Show help
            /stats - Show statistics
            /new - Start new conversation
            /clear - Clear screen
            /quit, /exit - Exit chat
        """
        cmd = command.lower().strip()

        if cmd in ("/quit", "/exit"):
            return False

        elif cmd == "/help":
            self._show_help()

        elif cmd == "/stats":
            self._show_stats()

        elif cmd == "/new":
            self._start_new_conversation()

        elif cmd == "/clear":
            self.console.clear()

        else:
            self.console.print(f"[yellow]Unknown command: {command}[/yellow]")
            self.console.print("Type [cyan]/help[/cyan] for available commands")

        return True

    def _show_help(self):
        """Display help message."""
        help_text = """
## Available Commands

- `/help` - Show this help message
- `/stats` - Show conversation statistics
- `/new` - Start a new conversation (clears context)
- `/clear` - Clear the screen
- `/quit` or `/exit` - Exit the chat
- `Ctrl+C` or `Ctrl+D` - Exit the chat

## Features

- **Conversation Memory**: AI remembers your conversation context!
- **Markdown Rendering**: AI responses are rendered with formatting
- **Command History**: Use Up/Down arrows to navigate history
- **Token Tracking**: See token usage for each message

## Phase 2: Short-Term Memory

The AI now maintains conversation context within your session. Ask follow-up
questions and the AI will remember what you talked about!

Example:
```
You: What's the capital of France?
AI: The capital of France is Paris.

You: What's the population?
AI: Paris has approximately 2.2 million people...
```

Use `/new` to start a fresh conversation with no context.

## Tips

- Keep messages clear and concise
- Adjust temperature (0.0-1.0) for more/less creative responses
- Check `/stats` to monitor token usage
        """
        panel = Panel(
            Markdown(help_text),
            title="[bold cyan]Help[/bold cyan]",
            border_style="cyan",
        )
        self.console.print(panel)

    def _show_stats(self):
        """Display conversation statistics."""
        stats_table = Table(title="Conversation Statistics", box=None)
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="green")

        stats_table.add_row("Messages Sent", str(self.message_count))
        stats_table.add_row("Total Input Tokens", str(self.total_input_tokens))
        stats_table.add_row("Total Output Tokens", str(self.total_output_tokens))
        stats_table.add_row(
            "Total Tokens", str(self.total_input_tokens + self.total_output_tokens)
        )
        stats_table.add_row("Session ID", self.session_id)
        stats_table.add_row("Temperature", str(self.temperature))
        stats_table.add_row("Max Tokens", str(self.max_tokens))

        self.console.print()
        self.console.print(stats_table)

    def _start_new_conversation(self):
        """
        Start a new conversation with a fresh session ID.

        This clears the conversation context on the server side by
        creating a new session. Local stats are also reset.
        """
        old_session = self.session_id
        self.session_id = str(uuid.uuid4())

        # Reset local stats
        old_message_count = self.message_count
        old_total_tokens = self.total_input_tokens + self.total_output_tokens

        self.message_count = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0

        # Show confirmation
        info_panel = Panel(
            f"[green]✓[/green] Started new conversation!\n\n"
            f"[dim]Previous session:[/dim]\n"
            f"  • Messages: {old_message_count}\n"
            f"  • Tokens: {old_total_tokens}\n\n"
            f"[dim]New session ID:[/dim]\n"
            f"  {self.session_id}",
            title="[bold cyan]New Conversation[/bold cyan]",
            border_style="cyan",
        )
        self.console.print("\n")
        self.console.print(info_panel)

    async def _confirm_quit(self) -> bool:
        """
        Ask user to confirm quit.

        Returns:
            bool: True if user confirms quit
        """
        self.console.print("\n[yellow]Are you sure you want to quit? (y/n)[/yellow]")
        try:
            confirm = await self.prompt_session.prompt_async("> ")
            return confirm.lower().strip() in ("y", "yes")
        except (KeyboardInterrupt, EOFError):
            return True

    def _display_goodbye(self):
        """Display goodbye message."""
        goodbye_text = f"""
# Thanks for chatting!

**Session Summary:**
- Messages: {self.message_count}
- Total Tokens: {self.total_input_tokens + self.total_output_tokens}
  - Input: {self.total_input_tokens}
  - Output: {self.total_output_tokens}

Have a great day! 👋
        """
        panel = Panel(
            Markdown(goodbye_text),
            title="[bold cyan]Goodbye[/bold cyan]",
            border_style="cyan",
        )
        self.console.print("\n")
        self.console.print(panel)
