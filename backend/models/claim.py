"""
Pydantic models for claims
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class ClaimType(str, Enum):
    AUTO = "auto"
    PROPERTY = "property"
    INJURY = "injury"
    COMMERCIAL = "commercial"
    LIABILITY = "liability"


class SeverityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Priority(str, Enum):
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ClaimStatus(str, Enum):
    UPLOADED = "uploaded"
    EXTRACTING = "extracting"
    SCORING = "scoring"
    ROUTING = "routing"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"
    REJECTED = "rejected"


class Party(BaseModel):
    name: str
    role: str  # claimant, insured, third_party, witness
    contact: Optional[str] = None
    address: Optional[str] = None


class Location(BaseModel):
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class Injury(BaseModel):
    person: str
    severity: str  # minor, moderate, serious, critical, fatal
    description: str
    medical_treatment: Optional[bool] = None


class ExtractedData(BaseModel):
    claim_amount: Optional[float] = None
    incident_type: Optional[str] = None
    incident_date: Optional[datetime] = None
    report_date: Optional[datetime] = None
    parties: List[Party] = []
    location: Optional[Location] = None
    injuries: List[Injury] = []
    policy_number: Optional[str] = None
    coverage_limits: Dict[str, Any] = {}
    description: Optional[str] = None
    fault_determination: Optional[str] = None
    attorney_involved: bool = False


class FraudFlag(BaseModel):
    type: str
    confidence: float  # 0-1
    evidence: str
    severity: str  # low, medium, high


class RoutingDecision(BaseModel):
    assigned_to: Optional[str] = None
    adjuster_id: Optional[str] = None
    priority: Priority
    reason: str
    estimated_workload_hours: Optional[float] = None
    investigation_checklist: List[str] = []


class ClaimDocument(BaseModel):
    claim_id: str
    document_types: List[str] = []  # acord, police_report, medical, email, photo
    file_paths: List[str] = []
    uploaded_at: datetime = Field(default_factory=datetime.now)

    extracted_data: Optional[ExtractedData] = None
    extracted_text: Optional[str] = None  # Raw text extracted by LandingAI

    severity_score: Optional[float] = None  # 0-100
    complexity_score: Optional[float] = None  # 0-100
    fraud_risk_score: Optional[float] = None  # 0-100

    fraud_flags: List[FraudFlag] = []
    routing_decision: Optional[RoutingDecision] = None

    status: ClaimStatus = ClaimStatus.UPLOADED
    processing_time_seconds: Optional[float] = None

    # Task tracking
    task_id: Optional[str] = None
    review_check_id: Optional[str] = None

    # Source tracking
    source: Optional[str] = "upload"  # "upload" or "gmail"
    source_metadata: Optional[Dict[str, Any]] = None  # Gmail email ID, sender, subject, etc.

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class ClaimResponse(BaseModel):
    claim_id: str
    status: ClaimStatus
    extracted_data: Optional[ExtractedData] = None
    severity_score: Optional[float] = None
    complexity_score: Optional[float] = None
    fraud_flags: List[FraudFlag] = []
    routing_decision: Optional[RoutingDecision] = None
    processing_time_seconds: Optional[float] = None
