"""Service layer for interacting with Claude Agent SDK."""

from collections.abc import AsyncIterator

from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock

from ..config import settings

# Explicitly list all tools to disallow - no file, web, or system access
DISALLOWED_TOOLS = [
    "Read",
    "Write",
    "Edit",
    "Bash",
    "Glob",
    "Grep",
    "WebFetch",
    "WebSearch",
    "NotebookEdit",
    "TodoWrite",
    "Task",
]


class ClaudeService:
    """Service layer for interacting with Claude Agent SDK.

    This service is configured to disable all tools, preventing Claude from
    accessing files, executing commands, or making web requests. It only
    processes the input prompt and returns generated text.
    """

    def __init__(self):
        """Initialize the Claude service."""
        pass

    async def generate(
        self,
        prompt: str,
        model: str,
        system_prompt: str | None = None,
        max_turns: int | None = None,
    ) -> AsyncIterator[str]:
        """Generate text completion using Claude Agent SDK.

        Args:
            prompt: The input prompt.
            model: The Claude model to use.
            system_prompt: Optional system prompt.
            max_turns: Maximum conversation turns.

        Yields:
            Text chunks as they are generated.
        """
        if max_turns is None:
            max_turns = settings.default_max_turns

        options = ClaudeAgentOptions(
            model=model,
            system_prompt=system_prompt,
            max_turns=max_turns,
            # Explicitly disable all tools - no file/web/system access
            allowed_tools=[],
            disallowed_tools=DISALLOWED_TOOLS,
        )

        async for message in query(prompt=prompt, options=options):
            # Extract text content from AssistantMessage
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        yield block.text

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str,
        max_turns: int | None = None,
    ) -> AsyncIterator[str]:
        """Chat completion with message history.

        Args:
            messages: List of message dictionaries with 'role' and 'content'.
            model: The Claude model to use.
            max_turns: Maximum conversation turns.

        Yields:
            Text chunks as they are generated.
        """
        if max_turns is None:
            max_turns = settings.default_max_turns

        # Extract system prompt if present
        system_prompt = None
        conversation_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            else:
                conversation_messages.append(msg)

        # Build the prompt from conversation history
        prompt = self._format_conversation(conversation_messages)

        options = ClaudeAgentOptions(
            model=model,
            system_prompt=system_prompt,
            max_turns=max_turns,
            # Explicitly disable all tools - no file/web/system access
            allowed_tools=[],
            disallowed_tools=DISALLOWED_TOOLS,
        )

        async for message in query(prompt=prompt, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        yield block.text

    def _format_conversation(self, messages: list[dict[str, str]]) -> str:
        """Format conversation messages into a single prompt.

        Args:
            messages: List of message dictionaries with 'role' and 'content'.

        Returns:
            Formatted prompt string.
        """
        if not messages:
            return ""

        # If only one user message, return it directly
        if len(messages) == 1 and messages[0]["role"] == "user":
            return messages[0]["content"]

        # Format multi-turn conversation
        formatted_parts = []
        for msg in messages:
            role = msg["role"].capitalize()
            content = msg["content"]
            formatted_parts.append(f"{role}: {content}")

        # Add instruction for the assistant to continue
        formatted_parts.append("Assistant:")

        return "\n\n".join(formatted_parts)


# Singleton instance
claude_service = ClaudeService()
