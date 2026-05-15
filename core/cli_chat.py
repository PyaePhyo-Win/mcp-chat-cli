from typing import List, Tuple, AsyncGenerator, Optional
from mcp.types import Prompt, PromptMessage
from core.chat import Chat
from core.gemini import Gemini
from mcp_client import MCPClient

SUPPORTED_MODELS = [
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite-preview",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
]

class CliChat(Chat):
    def __init__(
        self,
        doc_client: MCPClient,
        clients: dict[str, MCPClient],
        llm_service: Gemini,
    ):
        super().__init__(clients=clients, llm_service=llm_service)
        self.doc_client: MCPClient = doc_client

    async def list_prompts(self) -> list[Prompt]:
        return await self.doc_client.list_prompts()

    async def list_docs_ids(self) -> list[str]:
        return await self.doc_client.read_resource("docs://documents")

    async def get_doc_content(self, doc_id: str) -> str:
        return await self.doc_client.read_resource(f"docs://documents/{doc_id}")

    async def get_prompt(
        self, command: str, doc_id: str
    ) -> list[PromptMessage]:
        return await self.doc_client.get_prompt(command, {"doc_id": doc_id})

    async def _extract_resources(self, query: str) -> str:
        mentions = [word[1:] for word in query.split() if word.startswith("@")]
        doc_ids = await self.list_docs_ids()
        mentioned_docs: list[Tuple[str, str]] = []

        for doc_id in doc_ids:
            if doc_id in mentions:
                content = await self.get_doc_content(doc_id)
                mentioned_docs.append((doc_id, content))

        return "".join(
            f'\\n<document id="{doc_id}">\\n{content}\\n</document>\\n'
            for doc_id, content in mentioned_docs
        )

    async def _process_command(self, query: str) -> Optional[str]:
        if not query.startswith("/"):
            return None

        words = query.split()
        cmd = words[0].lower()

        # Built-in commands
        if cmd == "/model":
            if len(words) < 2:
                return f"**Current model:** {self.llm_service.model}\n\n**Available models:**\n" + "\n".join([f"- {m}" for m in SUPPORTED_MODELS])
            
            new_model = words[1]
            if new_model in SUPPORTED_MODELS:
                self.llm_service.model = new_model
                return f"Successfully switched to model: **{new_model}**"
            else:
                return f"Error: Model '**{new_model}**' is not supported."

        if cmd == "/clear":
            self.messages = []
            return "Chat history cleared."

        if cmd == "/help":
            help_text = "**Available Commands:**\n\n"
            help_text += "- `/model <name>`: Switch Gemini model\n"
            help_text += "- `/clear`: Clear chat history\n"
            help_text += "- `/help`: Show this help message\n\n"
            
            prompts = await self.list_prompts()
            if prompts:
                help_text += "**MCP Prompts:**\n"
                for p in prompts:
                    help_text += f"- `/{p.name}`: {p.description or ''}\n"
            
            return help_text

        # MCP Prompts
        command = cmd.replace("/", "")
        try:
            doc_id = words[1] if len(words) > 1 else ""
            messages = await self.doc_client.get_prompt(
                command, {"doc_id": doc_id}
            )
            
            # Convert prompt messages to Gemini parts
            for msg in messages:
                role = "user" if msg.role == "user" else "model"
                content = msg.content
                text = ""
                if isinstance(content, dict) and content.get("type") == "text":
                    text = content.get("text", "")
                elif hasattr(content, "type") and content.type == "text":
                    text = getattr(content, "text", "")
                    
                self.messages.append({"role": role, "parts": [{"text": text}]})
            return "Command processed."
        except Exception:
            # If not a known MCP prompt, return None so it's treated as a normal query
            return None

    async def run(self, query: str) -> AsyncGenerator[str, None]:
        cmd_result = await self._process_command(query)
        if cmd_result:
            yield cmd_result
            return

        # Rest of Chat.run logic is inherited
        async for chunk in super().run(query):
            yield chunk
