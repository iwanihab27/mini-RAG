from sqlalchemy.testing.suite.test_reflection import metadata
from app.stores.LLMEnums import DocumentTypeEnums
from app.controllers.BaseController import BaseController
from app.models.db_schemas import Project, DataChunk
from typing import List
import json


class NLPController(BaseController):
    def __init__(self, vectordb_client, generation_client, embedding_client):
        super().__init__()

        self.vectordb_client = vectordb_client
        self.generation_client = generation_client
        self.embedding_client = embedding_client

    def create_collection_name(self, project_id: str):
        return f"projects/{project_id}".strip()

    def reset_vector_db_collection(self, project: Project):
        collection_name = self.create_collection_name(project_id=project.project_id)
        return self.vectordb_client.delete_collection(collection_name=collection_name)

    def get_vector_collection_info(self, project: Project):
        collection_name = self.create_collection_name(project_id=project.project_id)
        collection_info = self.vectordb_client.get_collection_info(collection_name=collection_name)

        return json.loads(
            json.dumps(collection_info, default=lambda x : x.__dict__())
        )

    def index_vector_db(self, project: Project, chunks: List[DataChunk],
                              chunks_ids: List[int],
                              do_reset: bool = False):

        # step 1 get collection name
        collection_name = self.create_collection_name(project_id=project.project_id)

        # step 2 manage items
        texts = [ c.chunk_text for c in chunks ]
        metadata = [ c.chunk_metadata for c in chunks ]
        vectors = [
            self.embedding_client.embed_text(text=text,
                                             document_type=DocumentTypeEnums.DOCUMENT.value)
            for text in texts
        ]

        # step 3 create collection if not exist
        _ = self.vectordb_client.create_collection(
            collection_name=collection_name,
            do_reset=do_reset,
            embedding_size=self.embedding_client.embedding_size,)

        # step 4 insert into db
        _ = self.vectordb_client.insert_many(
            collection_name=collection_name,
            texts=texts,
            metadata=metadata,
            vectors=vectors,
            chunks_ids=chunks_ids,
        )

        return True

    def search_vector_db_collection(self, project: Project, text: str, limit: int = 10):

        #step1 ger collection name
        collection_name = self.create_collection_name(project_id=project.project_id)

        #step2  get text embedding vector
        vector = self.embedding_client.embed_text(text=text, document_type=DocumentTypeEnums.QUERY.value)

        if not vector or len(vector) == 0:
            return False

        #step3 do semantic search
        result = self.vectordb_client.search_by_vector(
            collection_name=collection_name,
            vector=vector,
            limit=limit,
        )

        if not result:
            return False

        return json.loads(
            json.dumps(result, default=lambda x: x.__dict__())
        )
