from typing import AsyncGenerator
from core.gemini import Gemini
from mcp_client import MCPClient
from core.tools import ToolManager
from google.genai import types, errors
from rich.console import Console

class Chat:
    def __init__(self, llm_service: Gemini, clients: dict[str, MCPClient]):
        self.llm_service: Gemini = llm_service
        self.clients: dict[str, MCPClient] = clients
        self.messages = []
        self.console = Console()

    async def _process_query(self, query: str):
        self.messages.append({"role": "user", "parts": [{"text": query}]})

    async def run(
        self,
        query: str,
    ) -> AsyncGenerator[str, None]:
        await self._process_query(query)

        while True:
            try:
                stream = await self.llm_service.chat_stream(
                    messages=self.messages,
                    tools=await ToolManager.get_all_tools(self.clients),
                )
                
                full_text = ""
                full_parts = []
                
                async for chunk in stream:
                    # Handle text chunks
                    if chunk.text:
                        full_text += chunk.text
                        yield chunk.text
                    
                    # Handle other parts (like function calls)
                    if chunk.candidates and chunk.candidates[0].content and chunk.candidates[0].content.parts:
                        for part in chunk.candidates[0].content.parts:
                            if part.function_call:
                                full_parts.append(part)
                            elif part.text and not chunk.text: # Backup if chunk.text is empty
                                full_text += part.text
                                yield part.text

                if full_text:
                    # Put the accumulated text into a part
                    full_parts.insert(0, types.Part(text=full_text))
                
                if not full_parts:
                    break

                # Create the assistant message and add to history
                assistant_message = types.Content(role="model", parts=full_parts)
                self.messages.append(assistant_message)

                function_calls = [
                    part.function_call for part in full_parts 
                    if part.function_call
                ]

                if function_calls:
                    self.console.print("[italic yellow]Executing tools...[/italic yellow]")
                    tool_results = await ToolManager.execute_tool_requests(
                        self.clients, function_calls
                    )
                    
                    self.messages.append({
                        "role": "user",
                        "parts": tool_results
                    })
                    # Loop again to send tool results back to the model
                else:
                    break

            except errors.APIError as e:
                yield f"\n\n**API Error:** {e.message}"
                break
            except Exception as e:
                yield f"\n\n**Error during streaming:** {e}"
                break
