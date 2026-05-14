from core.gemini import Gemini
from mcp_client import MCPClient
from core.tools import ToolManager
from google.genai import types

class Chat:
    def __init__(self, llm_service: Gemini, clients: dict[str, MCPClient]):
        self.llm_service: Gemini = llm_service
        self.clients: dict[str, MCPClient] = clients
        self.messages = []

    async def _process_query(self, query: str):
        self.messages.append({"role": "user", "parts": [{"text": query}]})

    async def run(
        self,
        query: str,
    ) -> str:
        final_text_response = ""
        await self._process_query(query)

        while True:
            response = self.llm_service.chat(
                messages=self.messages,
                tools=await ToolManager.get_all_tools(self.clients),
            )
            
            # Add assistant's response to history
            self.messages.append(response.candidates[0].content)

            function_calls = [
                part.function_call for part in response.candidates[0].content.parts 
                if part.function_call
            ]

            if function_calls:
                print(f"Executing tools...")
                tool_results = await ToolManager.execute_tool_requests(
                    self.clients, function_calls
                )
                
                self.messages.append({
                    "role": "user",
                    "parts": tool_results
                })
            else:
                final_text_response = " ".join([p.text for p in response.candidates[0].content.parts if p.text])
                break

        return final_text_response
