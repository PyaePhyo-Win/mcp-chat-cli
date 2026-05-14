from google import genai
from google.genai import types

class Gemini:
    def __init__(self, model: str):
        self.client = genai.Client()
        self.model = model

    def chat(self, messages, tools=None):
        params = {
            "messages": messages,
        }
        if tools:
            params["tools"] = tools
            
        response = self.client.models.generate_content(
            model=self.model,
            contents=messages,
            config=types.GenerateContentConfig(
                tools=tools if tools else None,
                temperature=1.0,
            )
        )
        return response
