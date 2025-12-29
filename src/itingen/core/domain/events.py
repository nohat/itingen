from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict

class Event(BaseModel):
    model_config = ConfigDict(extra="allow")

    event_heading: Optional[str] = None
    kind: Optional[str] = None
    location: Optional[str] = None
    who: List[str] = Field(default_factory=list)
    depends_on: List[str] = Field(default_factory=list)
    venue_id: Optional[str] = None
    timezone: Optional[str] = None
    time_utc: Optional[str] = None
    coordination_point: Optional[bool] = None
    hard_stop: Optional[bool] = None
    inferred: Optional[bool] = None
    description: Optional[str] = None
    travel_to: Optional[str] = None
    
    # Raw data from ingest might include other fields
    # we allow extra for now to capture all Markdown key-values
