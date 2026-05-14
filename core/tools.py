import json
from typing import Optional, Literal, List, Any
from mcp.types import CallToolResult, Tool, TextContent
from mcp_client import MCPClient

from google.genai import types

class ToolManager:
    @classmethod
    async def get_all_tools(cls, clients: dict[str, MCPClient]) -> list[types.Tool]:
        """Gets all tools from the provided clients and converts to Gemini schema."""
        function_declarations = []
        for client in clients.values():
            tool_models = await client.list_tools()
            for t in tool_models:
                
                properties = {}
                required = t.inputSchema.get("required", [])
                
                for prop_name, prop_info in t.inputSchema.get("properties", {}).items():
                    # Map JSON types to Gemini types
                    prop_type_str = prop_info.get("type", "string").upper()
                    prop_type = getattr(types.Type, prop_type_str, types.Type.STRING)
                    properties[prop_name] = types.Schema(
                        type=prop_type,
                        description=prop_info.get("description", "")
                    )
                
                parameters = types.Schema(
                    type=types.Type.OBJECT,
                    properties=properties,
                    required=required
                )
                
                decl = types.FunctionDeclaration(
                    name=t.name,
                    description=t.description,
                    parameters=parameters
                )
                function_declarations.append(decl)
                
        if not function_declarations:
            return []
            
        return [types.Tool(function_declarations=function_declarations)]

    @classmethod
    async def _find_client_with_tool(
        cls, clients: list[MCPClient], tool_name: str
    ) -> Optional[MCPClient]:
        for client in clients:
            tools = await client.list_tools()
            if any(t.name == tool_name for t in tools):
                return client
        return None

    @classmethod
    async def execute_tool_requests(
        cls, clients: dict[str, MCPClient], function_calls: list[Any]
    ) -> list[types.Part]:
        
        tool_results = []
        for fc in function_calls:
            tool_name = fc.name
            tool_input = dict(fc.args) if fc.args else {}
            
            print(f"Executing: {tool_name} with {tool_input}")
            client = await cls._find_client_with_tool(list(clients.values()), tool_name)
            
            if not client:
                res = types.Part.from_function_response(
                    name=tool_name,
                    response={"error": "Tool not found"}
                )
                tool_results.append(res)
                continue

            try:
                tool_output: CallToolResult | None = await client.call_tool(tool_name, tool_input)
                items = tool_output.content if tool_output else []
                content_list = [item.text for item in items if isinstance(item, TextContent)]
                res_content = {"result": json.dumps(content_list)} if content_list else {"result": "Success"}
                
                res = types.Part.from_function_response(
                    name=tool_name,
                    response=res_content
                )
            except Exception as e:
                res = types.Part.from_function_response(
                    name=tool_name,
                    response={"error": str(e)}
                )
                
            tool_results.append(res)
            
        return tool_results
