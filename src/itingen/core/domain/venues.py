from datetime import datetime
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict

class VenueMetadata(BaseModel):
    created_at: str
    updated_at: str

class VenueContact(BaseModel):
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None

class VenueAddress(BaseModel):
    street: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    postcode: Optional[str] = None

class VenueBooking(BaseModel):
    reference: Optional[str] = None
    requirements: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None

class Venue(BaseModel):
    model_config = ConfigDict(extra="allow")

    venue_id: str = Field(..., pattern=r"^[a-z0-9\-]+$")
    canonical_name: str
    aliases: List[str] = Field(default_factory=list)
    metadata: VenueMetadata
    contact: Optional[VenueContact] = None
    address: Optional[Union[str, VenueAddress]] = None
    booking: Optional[VenueBooking] = None
    
    primary_cues: List[str] = Field(default_factory=list)
    secondary_cues: List[str] = Field(default_factory=list)
    camera_suggestions: List[str] = Field(default_factory=list)
    negative_cues: List[str] = Field(default_factory=list)
    reference_image_urls: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
