from app.stores.vectordb.providers.PGVectorProvider import PGVectorProvider
from app.stores.vectordb.providers.QdrantDBProvider import QdrantDBProvider
from app.stores.vectordb.VectorDBEnums import VectorDBEnums
from app.controllers.BaseController import BaseController
from sqlalchemy.orm import sessionmaker


class VectorDBProvider:

    def __init__(self, config, db_client: sessionmaker = None):
        self.config = config
        self.base_controller = BaseController()
        self.db_client =db_client

    def create(self, provider: str):
        if provider == VectorDBEnums.QDRANT.value:
            qdrant_db_client = self.base_controller.get_db_path(db_name=self.config.VECTOR_DB_PATH,)

            return QdrantDBProvider(
                db_path=qdrant_db_client,
                distance_method=self.config.VECTOR_DB_DISTANCE_METHOD,
                default_vector_size=self.config.EMBEDDING_MODEL_SIZE,
                index_threshold=self.config.VECTOR_DB_PGVEC_INDEX_THRESHOLD,
            )

        if provider == VectorDBEnums.PGVECTOR.value:
            return PGVectorProvider(
                db_client = self.db_client,
                distance_method = self.config.VECTOR_DB_DISTANCE_METHOD,
                default_vector_size = self.config.EMBEDDING_MODEL_SIZE,
                index_threshold = self.config.VECTOR_DB_PGVEC_INDEX_THRESHOLD,
            )

        return None