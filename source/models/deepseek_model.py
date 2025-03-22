# deepseek_model.py
from dotenv import load_dotenv
import os
import requests
import json
from models.model import Model
from models.response import Response
from dialogs.dialog import Dialog

class DeepSeekModel(Model):
    def __init__(self, name: str):
        super().__init__(name)
        self.api_key = os.getenv("DEEPSEEK_API_KEY")  # Fetch API key from environment variables
        self.api_url = os.getenv("DEEPSEEK_BASE_URL")  # DeepSeek API endpoint

    def get_response(self, dialog: Dialog) -> Response:
        # Create the response object
        response = Response()

        # Prepare messages for the API request
        messages = []
        for message in dialog.get_all():
            messages.append({
                "role": message.role,
                "content": message.content
            })

        try:
            # Set up the API request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            body = {
                "model": "deepseek-chat",  # Specify the DeepSeek model
                "messages": messages,
                "temperature": 0.0  # Adjust as needed
            }

            # Make the API request
            api_response = requests.post(self.api_url, headers=headers, json=body)
            api_response.raise_for_status()  # Raise an error for bad status codes

            # Parse the API response
            api_response_body = api_response.json()
            response.text = api_response_body["choices"][0]["message"]["content"]

            # Extract token usage (if available)
            if "usage" in api_response_body:
                response.input_tokens = api_response_body["usage"]["prompt_tokens"]
                response.output_tokens = api_response_body["usage"]["completion_tokens"]
                response.total_tokens = response.input_tokens + response.output_tokens

        except Exception as e:
            # Handle errors
            response.has_error = True
            response.text = f"Error: {str(e)}"

        finally:
            return response