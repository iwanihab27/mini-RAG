from enum import Enum


class VectorDBEnums(Enum):
    QDRANT = "QDRANT"
    PGVECTOR = "PGVECTOR"

class DistanceMethodEnums(Enum):
    COSINE = "cosine"
    DOT = "dot"

class PgvectorTableSchemeEnums(Enum):
    ID = "id"
    TEXT = "text"
    VECTOR = "vector"
    CHUNK_ID = "chunk_id"
    METADATA = "metadata"
    _PREFIX = "pgvector"

class PgvectorDistanceMethodEnums(Enum):
    COSINE = "vector_cosine_ops"
    DOT = "vector_12_ops"

class PgvectorIndexTypesEnums(Enum):
    HNSW = "hnsw"
    IVFFLAT = "ivfflat"