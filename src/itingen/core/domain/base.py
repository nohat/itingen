from typing import Any, Dict, List, Optional
import difflib
from pydantic import BaseModel, model_validator, ValidationError

class StrictBaseModel(BaseModel):
    """Base model that detects potential typos in extra fields."""
    
    @model_validator(mode="after")
    def check_for_typos(self) -> "StrictBaseModel":
        if not self.model_extra:
            return self
            
        known_fields = set(self.model_fields.keys())
        for extra_field in self.model_extra.keys():
            # Find close matches among known fields
            matches = difflib.get_close_matches(extra_field, known_fields, n=1, cutoff=0.85)
            if matches:
                # If the match is a very close typo (e.g. "addres" vs "address")
                # but allow fields that are reasonably distinct despite similarity
                # (e.g. "travel_from" vs "travel_to")
                raise ValueError(
                    f"Possible typo detected: field '{extra_field}' is very similar to "
                    f"existing field '{matches[0]}'. If this was intentional, "
                    f"ensure the field name is distinct enough."
                )
        return self
