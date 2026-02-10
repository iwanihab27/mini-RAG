from pydantic import BaseModel, Field, validator
from typing import List, Optional
from bson.objectid import ObjectId
from datetime import datetime


class Asset(BaseModel):
    id: Optional[ObjectId] = Field(None, alias="_id")
    asset_project_id: ObjectId
    asset_type: str = Field(..., min_length=1)
    asset_name: str = Field(..., min_length=1)
    asset_size: int = Field(ge=0, default=None)
    asset_confic: dict = Field(ge=0, default=None)
    asset_pushed_at: ObjectId = Field(default=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True

        @classmethod
        def get_indexes(cls):
            return [
                {
                    "key": [
                        ("asset_object_id", 1)
                    ],
                    "name": "asset_object_id_index_1",
                    "unique": False
                },
                {
                    "key": [
                        ("asset_object_id", 1),
                        ("asset_name", 1)
                    ],
                    "name": "asset_object_id_index_1",
                    "unique": True
                },
            ]

