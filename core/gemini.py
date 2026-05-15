from google import genai
from google.genai import types

class Gemini:
    def __init__(self, model: str):
        self.client = genai.Client()
        self.model = model

    async def chat_stream(self, messages, tools=None):
        response = await self.client.aio.models.generate_content_stream(
            model=self.model,
            contents=messages,
            config=types.GenerateContentConfig(
                tools=tools if tools else None,
                temperature=1.0,
            )
        )
        return response
