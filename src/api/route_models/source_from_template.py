from .base import BaseRouteModel
from typing import Dict


class SourceFromTemplate(BaseRouteModel):
    source_template_name_hash: str
    feed_hash: str
    source_name: str
    parameters: Dict[str, str]

    model_config = {
        "json_schema_extra": {
            "example": {
                "source_template_name_hash": "example_hash_123",
                "feed_hash": "feed_hash_456",
                "source_name": "Example Source Name",
                "parameters": {"parameter_name": "value"},
            }
        }
    }
