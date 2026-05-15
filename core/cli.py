from typing import List, Optional
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggest, Suggestion
from prompt_toolkit.document import Document
from prompt_toolkit.buffer import Buffer
from core.cli_chat import CliChat
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.text import Text
from rich.live import Live


class CommandAutoSuggest(AutoSuggest):
    def __init__(self, prompts: List):
        self.prompts = prompts
        self.prompt_dict = {prompt.name: prompt for prompt in prompts}

    def get_suggestion(
        self, buffer: Buffer, document: Document
    ) -> Optional[Suggestion]:
        text = document.text

        if not text.startswith("/"):
            return None

        parts = text[1:].split()

        if len(parts) == 1:
            cmd = parts[0]

            if cmd in self.prompt_dict:
                prompt = self.prompt_dict[cmd]
                return Suggestion(f" {prompt.arguments[0].name}")

        return None


class UnifiedCompleter(Completer):
    def __init__(self):
        self.prompts = []
        self.prompt_dict = {}
        self.resources = []
        self.builtin_commands = {
            "model": "Switch Gemini model",
            "clear": "Clear chat history",
            "help": "Show help message",
        }
        from core.cli_chat import SUPPORTED_MODELS
        self.supported_models = SUPPORTED_MODELS

    def update_prompts(self, prompts: List):
        self.prompts = prompts
        self.prompt_dict = {prompt.name: prompt for prompt in prompts}

    def update_resources(self, resources: List):
        self.resources = resources

    def get_completions(self, document, complete_event):
        text = document.text
        text_before_cursor = document.text_before_cursor

        if "@" in text_before_cursor:
            last_at_pos = text_before_cursor.rfind("@")
            prefix = text_before_cursor[last_at_pos + 1 :]

            for resource_id in self.resources:
                if resource_id.lower().startswith(prefix.lower()):
                    yield Completion(
                        resource_id,
                        start_position=-len(prefix),
                        display=resource_id,
                        display_meta="Resource",
                    )
            return

        if text.startswith("/"):
            parts = text[1:].split()

            # Command name completion
            if len(parts) <= 1 and not text.endswith(" "):
                cmd_prefix = parts[0] if parts else ""

                # Suggest built-in commands
                for cmd, desc in self.builtin_commands.items():
                    if cmd.startswith(cmd_prefix):
                        yield Completion(
                            cmd,
                            start_position=-len(cmd_prefix),
                            display=f"/{cmd}",
                            display_meta=desc,
                        )

                # Suggest MCP prompts
                for prompt in self.prompts:
                    if prompt.name.startswith(cmd_prefix):
                        yield Completion(
                            prompt.name,
                            start_position=-len(cmd_prefix),
                            display=f"/{prompt.name}",
                            display_meta=prompt.description or "",
                        )
                return

            # Argument completion
            if len(parts) == 1 and text.endswith(" "):
                cmd = parts[0].lower()

                if cmd == "model":
                    for model in self.supported_models:
                        yield Completion(model, start_position=0, display=model)
                    return

                if cmd in self.prompt_dict:
                    for id in self.resources:
                        yield Completion(
                            id,
                            start_position=0,
                            display=id,
                        )
                return

            if len(parts) >= 2:
                cmd = parts[0].lower()
                doc_prefix = parts[-1]

                if cmd == "model":
                    for model in self.supported_models:
                        if model.lower().startswith(doc_prefix.lower()):
                            yield Completion(
                                model,
                                start_position=-len(doc_prefix),
                                display=model
                            )
                    return

                for resource in self.resources:
                    if resource.lower().startswith(doc_prefix.lower()):
                        yield Completion(
                            resource,
                            start_position=-len(doc_prefix),
                            display=resource,
                        )
                return


class CliApp:
    def __init__(self, agent: CliChat):
        self.agent = agent
        self.resources = []
        self.prompts = []
        self.console = Console()

        self.completer = UnifiedCompleter()

        self.command_autosuggester = CommandAutoSuggest([])

        self.kb = KeyBindings()

        @self.kb.add("/")
        def _(event):
            buffer = event.app.current_buffer
            if buffer.document.is_cursor_at_the_end and not buffer.text:
                buffer.insert_text("/")
                buffer.start_completion(select_first=False)
            else:
                buffer.insert_text("/")

        @self.kb.add("@")
        def _(event):
            buffer = event.app.current_buffer
            buffer.insert_text("@")
            if buffer.document.is_cursor_at_the_end:
                buffer.start_completion(select_first=False)

        @self.kb.add(" ")
        def _(event):
            buffer = event.app.current_buffer
            text = buffer.text

            buffer.insert_text(" ")

            if text.startswith("/"):
                parts = text[1:].split()

                if len(parts) == 1:
                    buffer.start_completion(select_first=False)
                elif len(parts) == 2:
                    arg = parts[1]
                    if (
                        "doc" in arg.lower()
                        or "file" in arg.lower()
                        or "id" in arg.lower()
                    ):
                        buffer.start_completion(select_first=False)

        self.history = InMemoryHistory()
        self.session = PromptSession(
            completer=self.completer,
            history=self.history,
            key_bindings=self.kb,
            bottom_toolbar=self._get_bottom_toolbar,
            style=Style.from_dict(
                {
                    "prompt": "bold #00ff00",
                    "completion-menu.completion": "bg:#222222 #ffffff",
                    "completion-menu.completion.current": "bg:#444444 #ffffff",
                    "bottom-toolbar": "bg:#000000 italic",
                }
            ),
            complete_while_typing=True,
            complete_in_thread=True,
            auto_suggest=self.command_autosuggester,
        )

    def _get_bottom_toolbar(self):
        return f" Active Model: {self.agent.llm_service.model} "

    async def initialize(self):
        await self.refresh_resources()
        await self.refresh_prompts()

    async def refresh_resources(self):
        try:
            self.resources = await self.agent.list_docs_ids()
            self.completer.update_resources(self.resources)
        except Exception as e:
            print(f"Error refreshing resources: {e}")

    async def refresh_prompts(self):
        try:
            self.prompts = await self.agent.list_prompts()
            self.completer.update_prompts(self.prompts)
            self.command_autosuggester = CommandAutoSuggest(self.prompts)
            self.session.auto_suggest = self.command_autosuggester
        except Exception as e:
            print(f"Error refreshing prompts: {e}")

    def _display_welcome(self):
        welcome_text = Text("Welcome to MCP Chat CLI!", style="bold cyan")
        welcome_text.append("\n\nConnect with your tools and documents using Gemini.", style="italic white")
        
        self.console.print(
            Panel(
                welcome_text,
                title="[bold magenta]MCP Chat CLI[/bold magenta]",
                border_style="blue",
                padding=(1, 2),
            )
        )
        self.console.print("\nType [bold green]/[/bold green] for commands, [bold green]@[/bold green] for resources.\n")

    async def run(self):
        self._display_welcome()
        while True:
            try:
                # Use a more styled prompt
                user_input = await self.session.prompt_async([("class:prompt", "User: ")])
                if not user_input.strip():
                    continue

                self.console.print("\n[bold magenta]Assistant:[/bold magenta]")
                
                full_response = ""
                # Use Live to render the streaming response
                with Live(Markdown(full_response), console=self.console, refresh_per_second=10) as live:
                    async for chunk in self.agent.run(user_input):
                        full_response += chunk
                        live.update(Markdown(full_response))
                
                self.console.print()

            except KeyboardInterrupt:
                break
            except Exception as e:
                self.console.print(f"[bold red]Error:[/bold red] {e}")
