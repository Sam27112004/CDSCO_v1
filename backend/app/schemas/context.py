"""Pydantic schemas for regulatory context, filing parameters, and evaluated slot states."""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

from app.schemas.definition import SlotBlueprint


class IVDParameters(BaseModel):
    """Specific parameters for In Vitro Diagnostic (IVD) submissions."""

    is_veterinary: bool = Field(
        default=False,
        description="Whether IVD is for veterinary use (requires DADF NOC)",
    )
    is_radioimmunoassay: bool = Field(
        default=False,
        description="Whether RIA kit contains radioactive isotopes (requires BARC NOC)",
    )


class RegulatoryContext(BaseModel):
    """Regulatory context parameters driving the Rules Engine."""

    device_category: Literal["MEDICAL_DEVICE", "IVD"] = Field(
        default="MEDICAL_DEVICE",
        description="Statutory category under MDR 2017",
    )
    risk_class: Literal["CLASS_A", "CLASS_B", "CLASS_C", "CLASS_D"] = Field(
        default="CLASS_C",
        description="MDR 2017 risk classification",
    )
    filing_modality: Literal["FRESH", "ENDORSEMENT", "RETENTION"] = Field(
        default="FRESH",
        description="Regulatory filing modality",
    )
    is_sterile: bool = Field(
        default=False,
        description="Whether the finished device is supplied sterile (activates sterilization validation)",
    )
    is_contact_device: bool = Field(
        default=True,
        description="Whether device contacts patient tissue or mucosal membranes",
    )
    has_software: bool = Field(
        default=False,
        description="Whether device incorporates software or is Software as a Medical Device (SaMD)",
    )
    is_samd: bool = Field(
        default=False,
        description="Alias for Software as a Medical Device (IEC 62304)",
    )
    has_predicate: bool = Field(
        default=True,
        description="Whether equivalent predicate device exists in India",
    )
    has_medicinal_substance: bool = Field(
        default=False,
        description="Whether device incorporates active pharmaceutical ingredient / drug substance",
    )
    has_drug_substance: bool = Field(
        default=False,
        description="Alias for medicinal substance presence",
    )
    has_animal_origin: bool = Field(
        default=False,
        description="Whether device incorporates animal tissues or biological origin materials",
    )
    has_animal_studies: bool = Field(
        default=False,
        description="Whether in-vivo animal preclinical studies were conducted",
    )
    is_investigational: bool = Field(
        default=False,
        description="Whether device is an unapproved investigational device (requires Form MD-27)",
    )
    is_active_implantable: bool = Field(
        default=False,
        description="Whether device is an active implantable medical device",
    )
    ivd_parameters: Optional[IVDParameters] = Field(
        default_factory=IVDParameters,
        description="IVD-specific regulatory parameters",
    )


class EvaluatedSlot(BaseModel):
    """Evaluated runtime state of a discrete checklist slot."""

    slot_id: str = Field(description="Unique slot identifier")
    slot_number: str = Field(description="Display slot number")
    title: str = Field(description="Checklist slot title")
    category: str = Field(description="Statutory category")
    is_mandatory: bool = Field(description="Statutory mandatory status")
    is_active: bool = Field(description="Whether slot is active given current regulatory context")
    status: Literal["MISSING", "OPTIONAL", "NOT_APPLICABLE"] = Field(
        description="Initial slot state"
    )
    deactivation_reason: Optional[str] = Field(
        default=None,
        description="Explanatory reason if slot was deactivated",
    )
    slot: SlotBlueprint = Field(description="Underlying declarative slot blueprint")
