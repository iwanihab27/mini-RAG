from bson import ObjectId
from app.models.BaseDataModel import BaseDataModel
from app.models.db_schemas.mini_rag.schemes import asset
from app.models.enums.DataBaseEnum import DataBaseEnum
from bson import ObjectId
from sqlalchemy import select, func, delete


class AssetModel(BaseDataModel):

    def __init__(self, db_client: object):
        super().__init__(db_client=db_client)
        self.db_client = db_client

    @classmethod  # revise
    async def create_instance(cls, db_client: object):
        instance = cls(db_client)  # keda nada el init
        return instance

    async def create_asset (self, asset:asset):
        async with  self.db_client() as session:
            async with session.begin():
                session.add(asset)
            await session.commit()
            await session.refresh(asset)

        return asset

    async def get_all_project_assets(self, asset_project_id: str, asset_type: str):
        async with  self.db_client() as session:
            stmt = select(asset).where(
                asset.asset_project_id == asset_project_id,
                asset.asset_type == asset_type,
            )
            results = await session.execute(stmt)
            records = results.scalars().all()
        return records

    async def get_asset_record(self, asset_project_id: str, asset_name: str):
        async with  self.db_client() as session:
            stmt = select(asset).where(
                asset.asset_project_id == asset_project_id,
                asset.asset_name == asset_name,
            )
            results = await session.execute(stmt)
            records = results.scalar_one_or_none()
        return records