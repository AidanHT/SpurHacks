"""
Shared type definitions for Promptly models
"""

from typing import Annotated, Any
from bson import ObjectId
from pydantic import BeforeValidator


def validate_object_id(v: Any) -> ObjectId:
    """Validate and convert to ObjectId"""
    if isinstance(v, ObjectId):
        return v
    if isinstance(v, str) and ObjectId.is_valid(v):
        return ObjectId(v)
    raise ValueError("Invalid ObjectId")


PyObjectId = Annotated[ObjectId, BeforeValidator(validate_object_id)] 