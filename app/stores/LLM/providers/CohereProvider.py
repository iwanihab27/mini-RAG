from pymupdf import message
from app.stores.LLM_interface import LLM_interface
from app.stores.LLMEnums import CohereEnums, DocumentTypeEnums
import cohere
import logging


class CohereProvider(LLM_interface):

    def __init__(self, api_key: str,
                 default_input_max_characters: int = 1000,
                 default_generation_max_output_tokens: int = 1000,
                 default_generation_temperature: float = 0.1, ):     # creativity

        self.api_key = api_key

        self.default_input_max_characters = default_input_max_characters
        self.default_generation_max_output_tokens = default_generation_max_output_tokens
        self.default_generation_temperature = default_generation_temperature

        self.generation_model_id = None

        self.embedding_model_id = None
        self.embedding_size = None

        self.client = cohere.Client(api_key= self.api_key)


        self.enums = CohereEnums
        self.logger = logging.getLogger(__name__)

    def set_generation_model(self, model_id: str):
        self.generation_model_id = model_id

    def set_embedding_model(self, model_id: str, embedding_size: int):
        self.embedding_model_id = model_id
        self.embedding_size = embedding_size

    def process_text(self, text: str, ):
        return text[:self.default_input_max_characters].strip()

    def generate_text(self, prompt: str, char_history: list = [], max_output_token: int = None,
                      temperature: float = None):

        if not self.client:
            self.logger.error("cohere client was not set")
            return None

        if not self.generation_model_id:
            self.logger.error("cohere generation model was not set")
            return None

        max_output_token = max_output_token if max_output_token else self.default_max_output_tokens
        temperature = temperature if temperature else self.default_generation_temperature

        response = self.client.chat(
            model = self.generation_model_id,
            char_history = char_history,
            message = self.process_text(prompt),
            temperature = temperature,
            max_tokens = max_output_token,
        )

        if not response or response.text:
            self.logger.error("error while generating text with cohere")
            return None

        return response.text

    def embed_text(self, text: str, document_type: str = None):
        if not self.client:
            self.logger.error("cohere client was not set")
            return None

        if not self.embedding_model_id:
            self.logger.error("eembedding model was not set")
            return None

        input_type = CohereEnums.DOCUMENT
        if document_type == DocumentTypeEnums.QUERY:
            input_type = CohereEnums.QUERY

        response = self.client.embed(
            model = self.embedding_model_id,
            texts = [self.process_text(text)],
            input_type = input_type,
            embedding_types=['float'],
        )

        if not response or not response.embeddings or not response.embeddings.float:
            self.logger.error("error while embedding text with cohere")
            return None

        return response.embeddings.float[0]

    def construct_prompt(self, prompt: str, role: str):
        return {
            "role": role,
            "text": prompt,
        }





