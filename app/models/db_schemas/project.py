from pydantic import BaseModel, Field, validator
from typing import List, Optional
from bson.objectid import ObjectId



class Project(BaseModel):
    id: Optional[ObjectId] = Field(None, alias="_id")
    project_id: str = Field(..., min_length=1)

    @validator("project_id")
    def project_id_validator(cls, value):
        if not value.isalnum():
            raise ValueError("Project ID must be alphanumeric")

        else:
            return value


    class Config:
        arbitrary_types_allowed = True    # mtdy4 error law la2et 7aga 8areeba


    @classmethod
    def get_indexes(cls):
        return [
            {
                "key": [
                    ("project_id", 1)
                ],
                "name": "project_id_index_1",
                "unique": True
            }
        ]


