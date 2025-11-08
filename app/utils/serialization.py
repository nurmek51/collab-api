"""
Utility functions for data serialization and JSONB handling
"""
import json
import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Dict, List, Union
from pydantic import BaseModel
from enum import Enum


def serialize_for_jsonb(data: Any) -> Any:
    """
    Convert Python objects to JSON-serializable format for PostgreSQL JSONB storage.
    Handles Pydantic models, enums, datetime objects, UUIDs, etc.
    """
    if data is None:
        return None
    
    if isinstance(data, BaseModel):
        # Convert Pydantic model to dict with proper serialization
        return serialize_for_jsonb(data.model_dump())
    
    elif isinstance(data, dict):
        return {key: serialize_for_jsonb(value) for key, value in data.items()}
    
    elif isinstance(data, (list, tuple)):
        return [serialize_for_jsonb(item) for item in data]
    
    elif isinstance(data, Enum):
        return data.value
    
    elif isinstance(data, (datetime, date)):
        return data.isoformat()
    
    elif isinstance(data, uuid.UUID):
        return str(data)
    
    elif isinstance(data, Decimal):
        return float(data)
    
    elif isinstance(data, (str, int, float, bool)):
        return data
    
    else:
        # For any other type, try to convert to string
        return str(data)


def prepare_model_data_for_db(model_data: BaseModel, exclude_fields: set = None) -> Dict[str, Any]:
    """
    Prepare Pydantic model data for database insertion with proper JSONB serialization.
    
    Args:
        model_data: Pydantic model instance
        exclude_fields: Set of field names to exclude from the output
        
    Returns:
        Dictionary ready for database insertion
    """
    if exclude_fields is None:
        exclude_fields = set()
    
    # Get the raw model dump
    data_dict = model_data.model_dump(exclude=exclude_fields)
    
    # Process each field for JSONB compatibility
    processed_dict = {}
    for key, value in data_dict.items():
        processed_dict[key] = serialize_for_jsonb(value)
    
    return processed_dict


def safe_model_dump(model_data: BaseModel, exclude_unset: bool = False, exclude_fields: set = None) -> Dict[str, Any]:
    """
    Safely dump a Pydantic model with proper JSONB serialization for database operations.
    
    Args:
        model_data: Pydantic model instance
        exclude_unset: Whether to exclude unset fields
        exclude_fields: Set of field names to exclude
        
    Returns:
        Dictionary ready for database operations
    """
    if exclude_fields is None:
        exclude_fields = set()
        
    data_dict = model_data.model_dump(exclude_unset=exclude_unset, exclude=exclude_fields)
    
    # Process for JSONB compatibility
    return {key: serialize_for_jsonb(value) for key, value in data_dict.items()}
