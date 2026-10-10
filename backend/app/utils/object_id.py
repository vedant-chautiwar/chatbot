from datetime import datetime
from typing import Any, Dict, List, Union
from bson import ObjectId
from fastapi import HTTPException, status


def parse_object_id(id_str: str, resource_name: str = "Resource") -> ObjectId:
    """Validate and convert string to BSON ObjectId."""
    if not id_str or not ObjectId.is_valid(id_str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {resource_name} ID format",
        )
    return ObjectId(id_str)


def serialize_mongo_doc(doc: Union[Dict[str, Any], List[Any], Any]) -> Any:
    """
    Recursively serialize MongoDB document for JSON responses:
    - Converts `_id` to `id` (as str)
    - Converts any `ObjectId` to string
    - Converts any `datetime` to ISO 8601 formatted string
    """
    if doc is None:
        return None

    if isinstance(doc, list):
        return [serialize_mongo_doc(item) for item in doc]

    if isinstance(doc, dict):
        result = {}
        for key, value in doc.items():
            if key == "_id":
                result["id"] = str(value)
            elif isinstance(value, ObjectId):
                result[key] = str(value)
            elif isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, (dict, list)):
                result[key] = serialize_mongo_doc(value)
            else:
                result[key] = value
        return result

    if isinstance(doc, ObjectId):
        return str(doc)

    if isinstance(doc, datetime):
        return doc.isoformat()

    return doc
