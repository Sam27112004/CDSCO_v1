"""Statutory Form Definition Service.

Manages declarative form blueprints, synchronizes blueprints with the PostgreSQL
persistence tier, and resolves statutory slot hierarchies for workspace navigation
and dossier compilation.
"""

import json
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application_definition import ApplicationDefinition
from app.schemas.definition import (
    CategorySection,
    ChapterGroup,
    FormBlueprint,
    ResolvedSlotHierarchy,
    SlotBlueprint,
)

logger = logging.getLogger(__name__)

# Standard statutory taxonomy ordering and human-readable titles
CATEGORY_METADATA: Dict[str, Dict[str, Any]] = {
    "ADMINISTRATIVE": {
        "title": "Administrative Documents",
        "order": 1,
    },
    "ADMINISTRATIVE_LEGAL": {
        "title": "Administrative & Legal Documents",
        "order": 1,
    },
    "LEGAL_ELIGIBILITY": {
        "title": "Legal & Corporate Eligibility",
        "order": 2,
    },
    "REGULATORY_APPROVALS": {
        "title": "Regulatory Free Sale & Global Approvals",
        "order": 3,
    },
    "QUALITY_CERTIFICATES": {
        "title": "Quality & Standards Certifications",
        "order": 4,
    },
    "PLANT_MASTER_FILE_APPENDIX_I": {
        "title": "Plant Master File (Appendix I)",
        "order": 5,
    },
    "TECHNICAL_DOSSIER_PMF": {
        "title": "Plant Master File (PMF)",
        "order": 5,
    },
    "FIFTH_SCHEDULE_QMS": {
        "title": "Fifth Schedule Quality Management System",
        "order": 6,
    },
    "QUALITY_MANAGEMENT_SYSTEM": {
        "title": "Quality Management System (Fifth Schedule)",
        "order": 6,
    },
    "DEVICE_MASTER_FILE_APPENDIX_II": {
        "title": "Device Master File (Appendix II)",
        "order": 7,
    },
    "TECHNICAL_DOSSIER_DMF": {
        "title": "Device Master File (DMF)",
        "order": 7,
    },
    "SUPPLEMENTARY": {
        "title": "Supplementary Information & Undertakings",
        "order": 8,
    },
    "SUPPLEMENTARY_REGULATORY": {
        "title": "Supplementary Regulatory Documents",
        "order": 8,
    },
}

# Statutory chapter mapping for Fourth Schedule DMF, PMF, and Fifth Schedule QMS
CHAPTER_TITLE_MAP: Dict[str, str] = {
    # Device Master File (DMF) Chapters (Fourth Schedule Part III)
    "DMF_1_0": "1.0 Executive Summary & Device Description",
    "DMF_2_0": "2.0 Product Specifications & Design Principles",
    "DMF_3_0": "3.0 Predicate Device Equivalence Analysis",
    "DMF_4_0": "4.0 Essential Principles Compliance Matrix",
    "DMF_5_0": "5.0 Risk Management Report (ISO 14971)",
    "DMF_6_0": "6.0 Verification & Validation Studies Overview",
    "DMF_6_1": "6.1 Pre-clinical Bench Testing",
    "DMF_6_2": "6.2 Biocompatibility Evaluation (ISO 10993)",
    "DMF_6_2_OVERVIEW": "6.2 Biocompatibility Evaluation Overview",
    "DMF_6_3": "6.3 Sterilization Validation (ISO 11135 / 11137)",
    "DMF_6_4": "6.4 Software & Cybersecurity (IEC 62304)",
    "DMF_6_5": "6.5 Usability & Human Factors (IEC 62366)",
    "DMF_6_6": "6.6 Electrical Safety & EMC (IEC 60601-1)",
    "DMF_6_7": "6.7 Shelf Life & Accelerated Stability Testing",
    "DMF_6_8": "6.8 Packaging Validation & Transit Simulation",
    "DMF_6_9": "6.9 Animal Studies & Histopathology",
    "DMF_6_10": "6.10 In Vitro Diagnostic (IVD) Performance Analytics",
    "DMF_6_11": "6.11 Clinical Investigation & CER",
    "DMF_7_0": "7.0 Clinical Evidence & Post-Market Surveillance",
    "DMF_8_0": "8.0 Device Labeling, Artwork & IFU",
    # Plant Master File (PMF) Chapters (Fourth Schedule Part II & Appendix I)
    "PMF_ALL": "Plant Master File (Comprehensive Dossier)",
    "PMF_1_0": "1.0 General Facility & Corporate Overview",
    "PMF_2_0": "2.0 Manufacturing Operations & Cleanrooms",
    "PMF_2_1": "2.1 Manufacturing Process Flow & Controls",
    "PMF_4_0": "4.0 Personnel, Organogram & Competencies",
    "PMF_4_1": "4.1 Key Technical & Quality Personnel",
    "PMF_5_0": "5.0 Premises, Cleanrooms, HVAC & Water Systems",
    "PMF_6_0": "6.0 Equipment Inventory & Calibration Master Plan",
    "PMF_7_0": "7.0 Contamination Control & Sanitation",
    "PMF_8_0": "8.0 Raw Material Procurement & Warehousing",
    "PMF_9_0": "9.0 Finished Product Quarantine & Release",
    "PMF_10_0": "10.0 Waste Disposal & Environmental Controls",
    # Quality Management System (Fifth Schedule)
    "QMS_7_1": "7.1 General Requirements & Quality Manual",
    "QMS_7_2": "7.2 Management Responsibility & Quality Policy",
    "QMS_7_3": "7.3 Resource Management & Personnel",
    "QMS_7_4": "7.4 Product Realization & Design Controls",
    "QMS_7_5": "7.5 Purchasing & Supplier Evaluation",
    "QMS_7_6": "7.6 Production & Service Provision",
    "QMS_7_7": "7.7 Monitoring & Measuring Equipment Controls",
    "QMS_7_8": "7.8 Measurement, Analysis & Internal Audit",
    "QMS_7_9": "7.9 Control of Non-Conforming Product",
    "QMS_7_10": "7.10 Corrective & Preventive Action (CAPA)",
    "QMS_7_11": "7.11 Post-Market Surveillance & Feedback",
}


class DefinitionService:
    """Service providing blueprint loading, persistence synchronization,

    and statutory slot hierarchy resolution.
    """

    def __init__(self, fixtures_dir: Optional[Path] = None) -> None:
        if fixtures_dir is None:
            self.fixtures_dir = (
                Path(__file__).resolve().parent.parent / "fixtures" / "blueprints"
            )
        else:
            self.fixtures_dir = Path(fixtures_dir)
        self._blueprint_cache: Dict[str, FormBlueprint] = {}

    def load_blueprint_from_file(self, file_path: Union[str, Path]) -> FormBlueprint:
        """Loads and validates a single blueprint JSON fixture from disk.

        Args:
            file_path: Absolute or relative filesystem path to blueprint JSON.

        Returns:
            Validated FormBlueprint instance.

        Raises:
            FileNotFoundError: If the specified file does not exist.
            ValueError: If the file contents fail schema validation.
        """
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Blueprint file not found: {path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            blueprint = FormBlueprint.model_validate_json(content)
            self._blueprint_cache[blueprint.form_code] = blueprint
            return blueprint
        except Exception as exc:
            raise ValueError(f"Failed to parse blueprint at {path}: {exc}") from exc

    def get_blueprint(self, form_code: str) -> FormBlueprint:
        """Retrieves a form blueprint by its statutory form code (e.g. 'MD-14', 'MD-7').

        Checks in-memory cache first, then scans the fixtures directory.

        Args:
            form_code: Statutory code (case-insensitive, e.g. 'MD-14' or 'md_14').

        Returns:
            FormBlueprint instance.

        Raises:
            FileNotFoundError: If no blueprint file matches the form code.
        """
        normalized_code = form_code.strip().upper()
        if normalized_code in self._blueprint_cache:
            return self._blueprint_cache[normalized_code]

        # Try common file naming patterns
        slug = normalized_code.lower().replace("-", "_")
        candidate_names = [
            f"form_{slug}.json",
            f"{slug}.json",
            f"form_{normalized_code.lower()}.json",
        ]

        for name in candidate_names:
            file_path = self.fixtures_dir / name
            if file_path.is_file():
                return self.load_blueprint_from_file(file_path)

        # Fallback: scan all JSON files in fixtures_dir
        if self.fixtures_dir.is_dir():
            for json_path in self.fixtures_dir.glob("*.json"):
                try:
                    bp = self.load_blueprint_from_file(json_path)
                    if bp.form_code.upper() == normalized_code:
                        return bp
                except Exception:
                    continue

        raise FileNotFoundError(
            f"No blueprint fixture found for form code '{form_code}' in {self.fixtures_dir}"
        )

    def list_available_blueprints(self) -> List[Dict[str, Any]]:
        """Scans the fixtures directory and returns metadata summaries of all available blueprints.

        Returns:
            List of dictionaries containing blueprint summary information.
        """
        summaries = []
        if not self.fixtures_dir.is_dir():
            return summaries

        for json_path in sorted(self.fixtures_dir.glob("*.json")):
            try:
                bp = self.load_blueprint_from_file(json_path)
                summaries.append(
                    {
                        "form_code": bp.form_code,
                        "form_title": bp.form_title,
                        "version": bp.version,
                        "governing_rules": bp.governing_rules,
                        "total_slots": len(bp.slots),
                        "file_path": str(json_path),
                    }
                )
            except Exception as exc:
                logger.warning(
                    "Skipping invalid blueprint file %s: %s", json_path, exc
                )

        return summaries

    async def sync_blueprints_to_db(
        self, session: AsyncSession
    ) -> List[ApplicationDefinition]:
        """Loads all blueprint fixtures from disk and synchronizes them into the database.

        Performs an idempotent upsert: if an ApplicationDefinition with matching
        (code, version) exists, its title and schema_payload are updated; otherwise
        a new record is inserted.

        Args:
            session: Active SQLAlchemy AsyncSession.

        Returns:
            List of persisted ApplicationDefinition instances.
        """
        available = self.list_available_blueprints()
        synced_records = []

        for item in available:
            bp = self.get_blueprint(item["form_code"])
            stmt = select(ApplicationDefinition).where(
                ApplicationDefinition.code == bp.form_code,
                ApplicationDefinition.version == bp.version,
            )
            result = await session.execute(stmt)
            existing = result.scalars().first()

            if existing:
                existing.title = bp.form_title
                existing.schema_payload = bp.model_dump()
                existing.is_active = True
                synced_records.append(existing)
            else:
                new_def = ApplicationDefinition(
                    code=bp.form_code,
                    title=bp.form_title,
                    version=bp.version,
                    schema_payload=bp.model_dump(),
                    is_active=True,
                )
                session.add(new_def)
                synced_records.append(new_def)

        await session.flush()
        return synced_records

    async def get_definition_from_db(
        self,
        session: AsyncSession,
        code: str,
        version: Optional[str] = None,
    ) -> Optional[ApplicationDefinition]:
        """Queries the database for an active ApplicationDefinition matching code.

        Args:
            session: Active SQLAlchemy AsyncSession.
            code: Statutory form code (e.g. 'MD-14', 'MD-7').
            version: Optional version string. If omitted, returns latest active version.

        Returns:
            ApplicationDefinition instance or None if not found.
        """
        stmt = select(ApplicationDefinition).where(
            ApplicationDefinition.code == code.upper(),
            ApplicationDefinition.is_active == True,  # noqa: E712
        )
        if version:
            stmt = stmt.where(ApplicationDefinition.version == version)
        else:
            stmt = stmt.order_by(ApplicationDefinition.version.desc())

        result = await session.execute(stmt)
        return result.scalars().first()

    async def get_definition_by_id(
        self,
        session: AsyncSession,
        definition_id: Union[str, uuid.UUID],
    ) -> Optional[ApplicationDefinition]:
        """Queries an ApplicationDefinition by primary key ID.

        Args:
            session: Active SQLAlchemy AsyncSession.
            definition_id: UUID or string UUID.

        Returns:
            ApplicationDefinition instance or None.
        """
        if isinstance(definition_id, str):
            try:
                definition_id = uuid.UUID(definition_id)
            except ValueError:
                return None

        stmt = select(ApplicationDefinition).where(
            ApplicationDefinition.id == definition_id
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    def resolve_slot_hierarchy(
        self,
        blueprint_or_data: Union[FormBlueprint, ApplicationDefinition, Dict[str, Any]],
    ) -> ResolvedSlotHierarchy:
        """Transforms a flat blueprint into a structured, hierarchical slot tree.

        Groups slots by statutory category and technical chapter for display in
        the frontend checklist tree and multi-level dossier assembly.

        Args:
            blueprint_or_data: FormBlueprint instance, ApplicationDefinition ORM
                instance, or raw dictionary representing schema_payload.

        Returns:
            ResolvedSlotHierarchy with structured CategorySection nodes and chapter groupings.
        """
        # Normalize input to FormBlueprint
        if isinstance(blueprint_or_data, FormBlueprint):
            bp = blueprint_or_data
        elif isinstance(blueprint_or_data, ApplicationDefinition):
            bp = FormBlueprint.model_validate(blueprint_or_data.schema_payload)
        elif isinstance(blueprint_or_data, dict):
            bp = FormBlueprint.model_validate(blueprint_or_data)
        else:
            raise TypeError(
                f"Unsupported blueprint type for hierarchy resolution: {type(blueprint_or_data)}"
            )

        # Group slots by category preserving appearance order
        slots_by_category: Dict[str, List[SlotBlueprint]] = {}
        for slot in bp.slots:
            cat = slot.category
            if cat not in slots_by_category:
                slots_by_category[cat] = []
            slots_by_category[cat].append(slot)

        # Sort categories based on standard regulatory order
        def get_category_order(cat_code: str) -> int:
            return CATEGORY_METADATA.get(cat_code, {}).get("order", 99)

        sorted_category_codes = sorted(
            slots_by_category.keys(), key=get_category_order
        )

        sections: List[CategorySection] = []
        for cat_code in sorted_category_codes:
            cat_slots = slots_by_category[cat_code]
            meta = CATEGORY_METADATA.get(cat_code, {})
            cat_title = meta.get(
                "title", cat_code.replace("_", " ").title()
            )
            cat_order = meta.get("order", 99)

            # Build sub-chapter groupings if slots contain dossier_chapter mappings
            chapters: List[ChapterGroup] = []
            slots_by_chapter: Dict[str, List[SlotBlueprint]] = {}
            for s in cat_slots:
                if s.dossier_chapter:
                    ch_code = s.dossier_chapter
                    if ch_code not in slots_by_chapter:
                        slots_by_chapter[ch_code] = []
                    slots_by_chapter[ch_code].append(s)

            for ch_code, ch_slots in slots_by_chapter.items():
                ch_title = CHAPTER_TITLE_MAP.get(
                    ch_code, ch_code.replace("_", " ").title()
                )
                chapters.append(
                    ChapterGroup(
                        chapter_code=ch_code,
                        chapter_title=ch_title,
                        slots=ch_slots,
                    )
                )

            total_cat = len(cat_slots)
            mandatory_cat = sum(1 for s in cat_slots if s.is_mandatory)

            sections.append(
                CategorySection(
                    category_code=cat_code,
                    category_title=cat_title,
                    display_order=cat_order,
                    slots=cat_slots,
                    chapters=chapters,
                    total_slots_count=total_cat,
                    mandatory_slots_count=mandatory_cat,
                )
            )

        total_slots = len(bp.slots)
        mandatory_slots = sum(1 for s in bp.slots if s.is_mandatory)
        generatable_slots = sum(
            1 for s in bp.slots if "GENERATE" in s.fulfillment_modes
        )
        upload_only_slots = sum(
            1 for s in bp.slots if s.fulfillment_modes == ["UPLOAD"]
        )

        return ResolvedSlotHierarchy(
            form_code=bp.form_code,
            form_title=bp.form_title,
            version=bp.version,
            governing_rules=bp.governing_rules,
            total_slots=total_slots,
            mandatory_slots=mandatory_slots,
            upload_only_slots=upload_only_slots,
            generatable_slots=generatable_slots,
            sections=sections,
        )

    def get_slot_by_id(
        self, blueprint: FormBlueprint, slot_id: str
    ) -> Optional[SlotBlueprint]:
        """Finds a specific slot by its unique slot identifier within a blueprint.

        Args:
            blueprint: FormBlueprint to search.
            slot_id: Unique slot ID (e.g. '1.0', '10.11', '6.2').

        Returns:
            SlotBlueprint or None if not found.
        """
        for slot in blueprint.slots:
            if slot.slot_id == slot_id:
                return slot
        return None

    def get_slots_by_category(
        self, blueprint: FormBlueprint, category: str
    ) -> List[SlotBlueprint]:
        """Filters slots belonging to a specific category.

        Args:
            blueprint: FormBlueprint to filter.
            category: Statutory category code.

        Returns:
            List of SlotBlueprint instances.
        """
        return [s for s in blueprint.slots if s.category == category]

    def resolve_statutory_rule_map(
        self, blueprint: FormBlueprint
    ) -> Dict[str, List[str]]:
        """Maps statutory rules to the list of slot IDs governed by each rule.

        Args:
            blueprint: FormBlueprint to analyze.

        Returns:
            Dictionary mapping rule strings to lists of slot IDs.
        """
        rule_map: Dict[str, List[str]] = {}
        for slot in blueprint.slots:
            rule = slot.statutory_rule
            if rule not in rule_map:
                rule_map[rule] = []
            rule_map[rule].append(slot.slot_id)
        return rule_map


# Default global singleton instance
definition_service = DefinitionService()
