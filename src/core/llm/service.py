import os
import logging
from typing import Optional, Type, Any, Union
from pydantic import BaseModel
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

class LLMService:
    """
    Service for interacting with Google Gemini LLM.
    Supports structured output via Pydantic schemas.
    """
    def __init__(self) -> None:
        self.api_key: Optional[str] = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            logger.warning("GOOGLE_API_KEY not found. LLMService will fail if called.")
        
        self.client: genai.Client = genai.Client(api_key=self.api_key)
        # Standardize on Gemini 2.0 Flash (latest stable-ish)
        self.model_name: str = "gemini-2.0-flash-exp"

    async def generate(
        self, 
        prompt: str, 
        schema: Optional[Type[BaseModel]] = None
    ) -> Union[str, dict[str, Any], Any]:
        """
        Generates content from the LLM. 
        If a schema is provided, returns the parsed structured output.
        """
        try:
            config = types.GenerateContentConfig(
                temperature=0.7,
            )
            
            if schema:
                config.response_mime_type = "application/json"
                config.response_schema = schema

            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )
            
            if schema:
                # SDK handles parsing if response_schema is provided as Pydantic class
                return response.parsed
            
            return response.text
        except Exception as e:
            logger.error("LLM Generation failed: %s", e)
            raise
