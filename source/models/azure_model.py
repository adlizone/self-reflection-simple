# deepseek_model.py
import os
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
import json
from models.model import Model
from models.response import Response
from dialogs.dialog import Dialog
import time


class AzureModel(Model):
    def __init__(self, name: str):
        super().__init__(name)
        self.api_key = key  # Fetch API key from environment variables
        self.api_url = endpoint  # DeepSeek API endpoint

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
            
            client = ChatCompletionsClient(
                endpoint=endpoint,
                credential=AzureKeyCredential(key),
            )
            
            api_response = client.complete(
                messages=messages,
                max_tokens=2048,
                temperature=0.8,
                top_p=0.1,
                presence_penalty=0.0,
                frequency_penalty=0.0,
                model=self.name
            )
            
            # Note: Set tokens first in case there is an error below
            response.input_tokens = api_response.usage.prompt_tokens
            response.output_tokens = api_response.usage.completion_tokens
            response.total_tokens = api_response.usage.total_tokens

            response.text = api_response.choices[0].message.content
            response.text = response.text.replace("\n\n", "\n")
            
        except Exception as e:
            # Handle errors
            response.has_error = True
            response.text = f"Error: {str(e)}"

        finally:
            time.sleep(1)
            return response