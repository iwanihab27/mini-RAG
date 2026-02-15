from app.stores.vectordb.providers.QdrantDBProvider import QdrantDBProvider
from app.stores.vectordb.VectorDBEnums import VectorDBEnums
from app.controllers.BaseController import BaseController


class VectorDBProvider:

    def __init__(self, config ):
        self.config = config
        self.base_controller = BaseController()

    def create(self, provider: str):
        if provider == VectorDBEnums.QDRANT.value:
            db_path = self.base_controller.get_db_path(db_name=self.config.VECTOR_DB_PATH,)
            return QdrantDBProvider(
                db_path=db_path,
                distance_method=self.config.VECTOR_DB_DISTANCE_METHOD,
            )

        return None




