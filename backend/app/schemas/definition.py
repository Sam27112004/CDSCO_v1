from typing import List, Optional, Literal, Any, Dict
from pydantic import BaseModel, Field


class ApplicabilityRule(BaseModel):
    """Rule determining dynamic slot activation or deactivation."""

    condition: Optional[Literal["ALWAYS_TRUE", "ALWAYS_FALSE"]] = None
    field: Optional[str] = None
    operator: Optional[Literal["EQUALS", "NOT_EQUALS", "IN", "NOT_IN"]] = None
    value: Optional[Any] = None


class SlotGuidance(BaseModel):
    """8-Point statutory guidance card for a discrete portal slot."""

    what_it_is: str = Field(description="Statutory explanation of the document")
    why_it_is_needed: str = Field(description="Regulatory purpose under MDR 2017")
    official_citation: str = Field(description="Legal citation in MDR 2017 or Fourth Schedule")
    who_issues: str = Field(description="Issuing authority or responsible signatory")
    validity_period: str = Field(description="Acceptable document age or shelf-life window")
    mandatory_inclusions: List[str] = Field(description="Must-have elements inside the document")
    critical_pitfalls: List[str] = Field(description="Common reasons for rejection by CDSCO evaluators")
    pro_forma_available: bool = Field(description="Whether in-app template generation is supported")


class SlotBlueprint(BaseModel):
    """Declarative specification for a single upload or generation slot."""

    slot_id: str = Field(description="Unique slot identifier (e.g. 1.0, 10.11)")
    slot_number: str = Field(description="Display slot number")
    category: str = Field(description="Slot grouping category (e.g. ADMINISTRATIVE, TECHNICAL_DOSSIER_DMF)")
    title: str = Field(description="Official checklist slot title")
    statutory_rule: str = Field(description="Specific MDR 2017 statutory rule reference")
    is_mandatory: bool = Field(description="Whether the slot is mandatory by default")
    fulfillment_modes: List[Literal["UPLOAD", "GENERATE"]] = Field(
        description="Supported fulfillment methods"
    )
    default_fulfillment_mode: Literal["UPLOAD", "GENERATE"] = Field(
        description="Initial active fulfillment toggle mode"
    )
    template_key: Optional[str] = Field(
        default=None, description="Engine 1 Jinja2/docxtpl template identifier"
    )
    max_size_mb: float = Field(default=10.0, description="Maximum allowed file size in megabytes")
    allowed_mimes: List[str] = Field(
        default_factory=lambda: ["application/pdf"],
        description="Allowed MIME types for upload",
    )
    dossier_chapter: Optional[str] = Field(
        default=None, description="Fourth Schedule chapter mapping (e.g. DMF_6_2)"
    )
    guidance: SlotGuidance = Field(description="8-Point regulatory guidance card")
    applicability_rule: ApplicabilityRule = Field(
        description="Predicate condition controlling slot visibility"
    )


class FormBlueprint(BaseModel):
    """Top-level declarative blueprint contract for a statutory CDSCO form."""

    form_code: str = Field(description="Statutory form code (e.g. MD-14, MD-7)")
    form_title: str = Field(description="Official CDSCO form title")
    version: str = Field(description="Blueprint version identifier")
    governing_rules: List[str] = Field(description="Governing rules under MDR 2017")
    slots: List[SlotBlueprint] = Field(description="Decomposed discrete checklist slots")
