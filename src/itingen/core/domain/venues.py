"""Venue domain model for trip locations.

AIDEV-NOTE: Venues represent physical locations with rich metadata
to support AI generation and trip planning features.
"""

from typing import List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict

class VenueMetadata(BaseModel):
    """Metadata for venue creation and updates."""
    created_at: str = Field(..., description="ISO 8601 timestamp when venue was created")
    updated_at: str = Field(..., description="ISO 8601 timestamp when venue was last updated")

class VenueContact(BaseModel):
    """Contact information for a venue."""
    phone: Optional[str] = Field(None, description="Phone number")
    email: Optional[str] = Field(None, description="Email address")
    website: Optional[str] = Field(None, description="Website URL")

class VenueAddress(BaseModel):
    """Structured address for a venue."""
    street: Optional[str] = Field(None, description="Street address")
    city: Optional[str] = Field(None, description="City name")
    region: Optional[str] = Field(None, description="State/Province/Region")
    country: Optional[str] = Field(None, description="Country name")
    postcode: Optional[str] = Field(None, description="Postal/ZIP code")

class VenueBooking(BaseModel):
    """Booking and reservation information."""
    reference: Optional[str] = Field(None, description="Booking confirmation number")
    requirements: Optional[str] = Field(None, description="Special requirements for booking")
    phone: Optional[str] = Field(None, description="Booking contact phone")
    website: Optional[str] = Field(None, description="Booking website")

class Venue(BaseModel):
    """Represents a physical location where events can take place.
    
    Venues contain rich metadata to support:
    - AI image generation (cues, camera suggestions)
    - Trip planning (contact, booking info)
    - Data verification (sources, references)
    
    The model uses `extra="allow"` for extensibility.
    """
    
    model_config = ConfigDict(extra="allow")

    # Core identity
    venue_id: str = Field(..., pattern=r"^[a-z0-9\-]+$", description="Unique identifier for the venue")
    canonical_name: str = Field(..., description="Official name of the venue")
    aliases: List[str] = Field(default_factory=list, description="Alternative names or spellings")
    
    # Metadata
    metadata: VenueMetadata = Field(..., description="Creation and update timestamps")
    
    # Contact and location
    contact: Optional[VenueContact] = Field(None, description="Contact information")
    address: Optional[Union[str, VenueAddress]] = Field(None, description="Physical location (string or structured)")
    booking: Optional[VenueBooking] = Field(None, description="Reservation details")
    
    # AI enhancement fields
    primary_cues: List[str] = Field(default_factory=list, description="Key visual elements for image generation")
    secondary_cues: List[str] = Field(default_factory=list, description="Supporting visual elements")
    camera_suggestions: List[str] = Field(default_factory=list, description="Photography tips and angles")
    negative_cues: List[str] = Field(default_factory=list, description="Elements to avoid in images")
    reference_image_urls: List[str] = Field(default_factory=list, description="Example images for style reference")
    sources: List[str] = Field(default_factory=list, description="Source URLs for research/verification")
