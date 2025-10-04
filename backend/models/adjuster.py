"""
Pydantic models for adjusters
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class ExperienceLevel(str, Enum):
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    EXPERT = "expert"


class AdjusterSpecialization(str, Enum):
    AUTO = "auto"
    PROPERTY = "property"
    INJURY = "injury"
    COMMERCIAL = "commercial"
    LIABILITY = "liability"
    SIU = "siu"  # Special Investigation Unit


class AdjusterProfile(BaseModel):
    adjuster_id: str
    name: str
    email: str
    phone: Optional[str] = None

    specializations: List[AdjusterSpecialization]
    experience_level: ExperienceLevel
    years_experience: int

    # Capacity limits
    max_claim_amount: float  # Maximum claim amount they can handle
    max_concurrent_claims: int = 15
    current_workload: int = 0  # Number of active claims

    # Territory and availability
    territories: List[str] = []  # States or regions
    available: bool = True

    # Performance metrics
    average_resolution_days: Optional[float] = None
    customer_satisfaction_score: Optional[float] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class AdjusterWorkload(BaseModel):
    adjuster_id: str
    adjuster_name: str
    current_claims: int
    max_claims: int
    capacity_percentage: float
    active_claims: List[str] = []  # List of claim IDs
