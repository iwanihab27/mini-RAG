from sqlalchemy.testing.suite.test_reflection import metadata
from app.stores.LLMEnums import DocumentTypeEnums
from app.controllers.BaseController import BaseController
from app.models.db_schemas.mini_rag.schemes import project, datachunk, asset, RetrievedDocuments
from typing import List
import json
import time


class NLPController(BaseController):
    def __init__(self, vectordb_client, generation_client, embedding_client, TemplateParser):
        super().__init__()

        self.vectordb_client = vectordb_client
        self.generation_client = generation_client
        self.embedding_client = embedding_client
        self.TemplateParser = TemplateParser

    def create_collection_name(self, project_id: str):
        return f"collection_{self.vectordb_client.default_vector_size}_{project_id}".strip()

    async def reset_vector_db_collection(self, project: project):
        collection_name = self.create_collection_name(project_id=project.project_id)
        return await self.vectordb_client.delete_collection(collection_name=collection_name)

    async def get_vector_collection_info(self, project: project):
        collection_name = self.create_collection_name(project_id=project.project_id)
        collection_info = await self.vectordb_client.get_collection_info(collection_name=collection_name)

        return json.loads(
            json.dumps(collection_info, default=lambda x : x.__dict__)
        )

    async def index_vector_db(self, project: project, chunks: List[datachunk],
                              chunks_ids: List[int],
                              do_reset: bool = False):

        # step 1 get collection name
        collection_name = self.create_collection_name(project_id=project.project_id)

        # step 2 manage items
        texts = [ c.chunk_text for c in chunks ]
        metadata = [ c.chunk_metadata for c in chunks ]
        vectors = []
        for text in texts:
            vector = self.embedding_client.embed_text(text=texts, document_type=DocumentTypeEnums.DOCUMENT.value)
            vectors.append(vector)
            time.sleep(0.7)

        # step 3 create collection if not exist
        _ = await self.vectordb_client.create_collection(
            collection_name=collection_name,
            do_reset=do_reset,
            embedding_size=self.embedding_client.embedding_size,)

        # step 4 insert into db
        _ = await self.vectordb_client.insert_many(
            collection_name=collection_name,
            text=texts,
            metadata=metadata,
            vector=vectors,
            record_ids=chunks_ids,
        )

        return True

    async def search_vector_db_collection(self, project: project, text: str, limit: int = 10):

        #step1 ger collection name
        query_vector = None
        collection_name = self.create_collection_name(project_id=project.project_id)

        #step2  get text embedding vector
        vectors = self.embedding_client.embed_text(text=text, document_type=DocumentTypeEnums.QUERY.value)

        if not vectors or len(vectors) == 0:
            return False

        if isinstance(vectors, list) and len(vectors) > 0:
            query_vector = vectors[0]

        if not query_vector:
            return False

        #step3 do semantic search
        result = await self.vectorsdb_client.search_by_vectors(
            collection_name=collection_name,
            vectors=query_vector,
            limit=limit,
        )

        if not result:
            return False

        return result

    async def answer_rag_question(self, project: project, query: str, limit: int = 10):

        answer, full_prompt, chat_history = None, None, None

        #step1 retrieve related docs
        retrieved_documents = await self.search_vector_db_collection(
                project=project, text=query, limit=limit)

        if not retrieved_documents or len(retrieved_documents) == 0:
            return answer, full_prompt, chat_history

        #step2 construct LLM prompt
        system_prompt = self.TemplateParser.get("rag", "system_prompt")

        document_prompt = "\n".join([
            self.TemplateParser.get("rag", "document_prompt", {
                "doc_num": idx + 1,
                "chunk_text": self.generation_client.process_text(doc.text),
            })
            for idx, doc in enumerate(retrieved_documents)
        ])

        footer_prompt =self.TemplateParser.get("rag", "footer_prompt", {
            "query": query,
        })

        chat_history = [
            self.generation_client.construct_prompt(
                prompt=system_prompt,
                role=self.generation_client.enums.SYSTEM.value
            )
        ]

        full_prompt =  "\n\n".join([document_prompt, footer_prompt])

        answer =  self.generation_client.generate_text(
            prompt=full_prompt,
            chat_history=chat_history
        )

        return answer, full_prompt, chat_history

