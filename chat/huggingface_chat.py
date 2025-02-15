from transformers import pipeline
import torch
from utility.mlogging import logger

class HuggingFaceChat:
    """Hugging Face Chat Model (Replacing OpenAI API)"""

    def __init__(self, config: dict):
        """
        Initializes the chatbot using a local Hugging Face model.
        
        Args:
            config (dict): Configuration settings for the chatbot.
        """
        self.config = config

        # Retrieve model parameters from configuration with defaults
        # Optionally, you can allow the model name to be specified in the config.
        self.model_name = config.get("model", "./models/phi-2")
        self.temperature = config["common"].get("temperature", 0.7)
        self.max_length = config["common"]["response_segment"].get("max", 100)

        logger.info(f"🔄 Loading Hugging Face Model: {self.model_name}...")
        
        # Load the text generation pipeline
        self.chatbot = pipeline(
            "text-generation",
            model=self.model_name,
            device=0 if torch.cuda.is_available() else -1
        )

        logger.info("✅ Hugging Face Chat Model Loaded Successfully!")

    def get_response(self, text: str):
        """
        Generates a chatbot response using the Hugging Face model.
        
        Args:
            text (str): User input text.
        
        Returns:
            dict: A dictionary with the keys:
                  "seq": -1 (indicating a complete response),
                  "text": the generated response text.
        """
        try:
            logger.info(f"🗣 Generating response for: {text}")

            response = self.chatbot(
                text,
                max_length=self.max_length,
                truncation=True,
                temperature=self.temperature
            )

            response_text = response[0]["generated_text"]
            logger.info(f"💬 Response: {response_text}")

            return {"seq": -1, "text": response_text}

        except Exception as e:
            logger.error(f"❌ ERROR in Chatbot Processing: {e}")
            return {"seq": -1, "text": "⚠️ Sorry, I encountered an error!"}

    def get_response_stream(self, text: str):
        """
        Simulates a streaming response by yielding the full response once.
        In a production system, you might split the response into multiple chunks.
        
        Args:
            text (str): User input text.
        
        Yields:
            dict: A dictionary with a chunk of the response.
        """
        # For simplicity, we call get_response and yield its result.
        response = self.get_response(text)
        yield response

    def decode_chunk(self, chunk: dict):
        """
        Decodes a chunk of a streaming response.
        Since get_response_stream() yields a full response, this function just
        returns the chunk if it contains valid text.
        
        Args:
            chunk (dict): A chunk from get_response_stream.
        
        Returns:
            dict or None: The chunk (if valid) or None if no text is present.
        """
        if chunk and "text" in chunk and chunk["text"]:
            return chunk
        return None
