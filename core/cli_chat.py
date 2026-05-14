from typing import List, Tuple
from mcp.types import Prompt, PromptMessage
from core.chat import Chat
from core.gemini import Gemini
from mcp_client import MCPClient

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

    async def _process_command(self, query: str) -> bool:
        if not query.startswith("/"):
            return False

        words = query.split()
        command = words[0].replace("/", "")
        messages = await self.doc_client.get_prompt(
            command, {"doc_id": words[1]}
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
            
        return True

    async def _process_query(self, query: str):
        if await self._process_command(query):
            return

        added_resources = await self._extract_resources(query)

        prompt = f"""
        The user has a question:
        <query>
        {query}
        </query>

        The following context may be useful in answering their question:
        <context>
        {added_resources}
        </context>

        Note the user's query might contain references to documents like "@report.docx".
        Answer the user's question directly and concisely. Start with the exact information they need. 
        """

        self.messages.append({"role": "user", "parts": [{"text": prompt}]})
