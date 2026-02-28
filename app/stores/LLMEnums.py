from enum import Enum


class LLMEnums(Enum):
    OPENAI = "OPENAI"
    COHERE = "COHERE"

class OPENAIEnums(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

class CohereEnums(Enum):
    SYSTEM = "SYSTEM"
    USER = "USER"
    ASSISTANT = "CHATBOT"

    DOCUMENT = "search_document"
    QUERY = "search_query"               # what the user type

class DocumentTypeEnums(Enum):
    DOCUMENT = "document"
    QUERY = "query"               # what the user type


