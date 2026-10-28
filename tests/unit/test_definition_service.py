import uuid
import pytest
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application_definition import ApplicationDefinition
from app.schemas.definition import (
    CategorySection,
    ChapterGroup,
    FormBlueprint,
    ResolvedSlotHierarchy,
    SlotBlueprint,
)
from app.services.definition_service import (
    CATEGORY_METADATA,
    CHAPTER_TITLE_MAP,
    DefinitionService,
    definition_service,
)


def test_service_initialization():
    """Verifies default fixtures directory and custom path instantiation."""
    default_svc = DefinitionService()
    assert default_svc.fixtures_dir.is_dir()
    assert (default_svc.fixtures_dir / "form_md_14.json").exists()

    custom_path = Path(__file__).resolve().parent
    custom_svc = DefinitionService(fixtures_dir=custom_path)
    assert custom_svc.fixtures_dir == custom_path


def test_load_blueprint_from_file_valid():
    """Verifies loading and Pydantic validation of MD-14 fixture."""
    svc = DefinitionService()
    file_path = svc.fixtures_dir / "form_md_14.json"
    blueprint = svc.load_blueprint_from_file(file_path)

    assert isinstance(blueprint, FormBlueprint)
    assert blueprint.form_code == "MD-14"
    assert blueprint.version == "1.0"
    assert len(blueprint.slots) == 36


def test_load_blueprint_from_file_missing():
    """Verifies FileNotFoundError raised when blueprint file does not exist."""
    svc = DefinitionService()
    with pytest.raises(FileNotFoundError, match="Blueprint file not found"):
        svc.load_blueprint_from_file(svc.fixtures_dir / "non_existent_form.json")


def test_get_blueprint_caching_and_case_insensitivity():
    """Verifies retrieval by form code with caching and case-insensitivity."""
    svc = DefinitionService()

    # MD-14 lookup
    bp1 = svc.get_blueprint("md-14")
    assert bp1.form_code == "MD-14"

    # Subsequent lookup should hit memory cache
    bp2 = svc.get_blueprint("MD-14")
    assert bp1 is bp2

    # MD-7 lookup
    bp_md7 = svc.get_blueprint("md-7")
    assert bp_md7.form_code == "MD-7"
    assert len(bp_md7.slots) == 48


def test_get_blueprint_not_found():
    """Verifies FileNotFoundError when looking up an unknown form code."""
    svc = DefinitionService()
    with pytest.raises(FileNotFoundError, match="No blueprint fixture found"):
        svc.get_blueprint("MD-999")


def test_list_available_blueprints():
    """Verifies discovering all blueprint JSON fixtures."""
    svc = DefinitionService()
    available = svc.list_available_blueprints()

    codes = [item["form_code"] for item in available]
    assert "MD-14" in codes
    assert "MD-7" in codes

    md14_meta = next(item for item in available if item["form_code"] == "MD-14")
    assert md14_meta["total_slots"] == 36

    md7_meta = next(item for item in available if item["form_code"] == "MD-7")
    assert md7_meta["total_slots"] == 48


def test_resolve_slot_hierarchy_md14():
    """Verifies hierarchical decomposition of Form MD-14 blueprint."""
    svc = DefinitionService()
    bp = svc.get_blueprint("MD-14")
    hierarchy = svc.resolve_slot_hierarchy(bp)

    assert isinstance(hierarchy, ResolvedSlotHierarchy)
    assert hierarchy.form_code == "MD-14"
    assert hierarchy.total_slots == 36
    assert hierarchy.mandatory_slots == 30
    assert hierarchy.upload_only_slots + hierarchy.generatable_slots == 36

    # Verify category section structure
    assert len(hierarchy.sections) > 0
    total_slots_across_sections = sum(s.total_slots_count for s in hierarchy.sections)
    assert total_slots_across_sections == 36

    # Verify display order is sorted monotonically
    orders = [s.display_order for s in hierarchy.sections]
    assert orders == sorted(orders)

    # Verify TECHNICAL_DOSSIER_DMF section has chapters
    dmf_section = next(
        s for s in hierarchy.sections if s.category_code == "TECHNICAL_DOSSIER_DMF"
    )
    assert len(dmf_section.chapters) > 0
    chapter_codes = [c.chapter_code for c in dmf_section.chapters]
    assert "DMF_6_2" in chapter_codes
    assert "DMF_1_0" in chapter_codes


def test_resolve_slot_hierarchy_md7():
    """Verifies hierarchical decomposition of Form MD-7 domestic manufacturing blueprint."""
    svc = DefinitionService()
    bp = svc.get_blueprint("MD-7")
    hierarchy = svc.resolve_slot_hierarchy(bp)

    assert hierarchy.form_code == "MD-7"
    assert hierarchy.total_slots == 48
    assert hierarchy.mandatory_slots == 42


    section_codes = [s.category_code for s in hierarchy.sections]
    assert "ADMINISTRATIVE" in section_codes
    assert "TECHNICAL_DOSSIER_PMF" in section_codes
    assert "QUALITY_MANAGEMENT_SYSTEM" in section_codes
    assert "TECHNICAL_DOSSIER_DMF" in section_codes

    # Verify QMS Fifth Schedule chapter breakdown
    qms_section = next(
        s for s in hierarchy.sections if s.category_code == "QUALITY_MANAGEMENT_SYSTEM"
    )
    assert qms_section.total_slots_count == 11
    assert len(qms_section.chapters) == 11
    qms_chapters = [c.chapter_code for c in qms_section.chapters]
    assert "QMS_7_1" in qms_chapters
    assert "QMS_7_10" in qms_chapters


def test_resolve_slot_hierarchy_from_dict_and_orm():
    """Verifies hierarchy resolution accepts dict and ApplicationDefinition ORM models."""
    svc = DefinitionService()
    bp = svc.get_blueprint("MD-14")

    # From raw dict
    raw_dict = bp.model_dump()
    h_dict = svc.resolve_slot_hierarchy(raw_dict)
    assert h_dict.total_slots == 36

    # From ORM instance
    orm_def = ApplicationDefinition(
        id=uuid.uuid4(),
        code="MD-14",
        title=bp.form_title,
        version="1.0",
        schema_payload=raw_dict,
        is_active=True,
    )
    h_orm = svc.resolve_slot_hierarchy(orm_def)
    assert h_orm.total_slots == 36
    assert h_orm.form_code == "MD-14"


def test_resolve_slot_hierarchy_invalid_type():
    """Verifies TypeError raised on unsupported input types."""
    svc = DefinitionService()
    with pytest.raises(TypeError, match="Unsupported blueprint type"):
        svc.resolve_slot_hierarchy(12345)


def test_get_slot_by_id_and_category():
    """Verifies slot retrieval by ID and filtering by statutory category."""
    svc = DefinitionService()
    bp = svc.get_blueprint("MD-14")

    # Slot 1.0 (Covering Letter)
    slot_1 = svc.get_slot_by_id(bp, "1.0")
    assert slot_1 is not None
    assert slot_1.slot_id == "1.0"
    assert slot_1.title == "Covering Letter"
    assert "GENERATE" in slot_1.fulfillment_modes

    # Slot 10.11 (Biocompatibility)
    slot_bio = svc.get_slot_by_id(bp, "10.11")
    assert slot_bio is not None
    assert slot_bio.dossier_chapter == "DMF_6_2"

    # Non-existent slot
    assert svc.get_slot_by_id(bp, "99.99") is None

    # Filter by category
    admin_slots = svc.get_slots_by_category(bp, "ADMINISTRATIVE")
    assert len(admin_slots) == 4
    assert all(s.category == "ADMINISTRATIVE" for s in admin_slots)



def test_resolve_statutory_rule_map():
    """Verifies mapping statutory rules to their corresponding checklist slots."""
    svc = DefinitionService()
    bp = svc.get_blueprint("MD-14")
    rule_map = svc.resolve_statutory_rule_map(bp)

    assert "Rule 34(1)" in rule_map
    assert "1.0" in rule_map["Rule 34(1)"]
    assert len(rule_map) > 5


@pytest.mark.asyncio
async def test_sync_blueprints_to_db_and_query(db_session: AsyncSession):
    """Verifies synchronizing blueprints to database and querying by code and ID."""
    svc = DefinitionService()

    # Synchronize blueprints into database
    synced = await svc.sync_blueprints_to_db(db_session)
    assert len(synced) >= 2

    # Query definition by code
    md14_def = await svc.get_definition_from_db(db_session, "MD-14")
    assert md14_def is not None
    assert md14_def.code == "MD-14"
    assert md14_def.version == "1.0"
    assert len(md14_def.schema_payload["slots"]) == 36

    # Query definition by ID
    by_id = await svc.get_definition_by_id(db_session, md14_def.id)
    assert by_id is not None
    assert by_id.id == md14_def.id

    # Query non-existent
    assert await svc.get_definition_from_db(db_session, "MD-NON-EXISTENT") is None
    assert await svc.get_definition_by_id(db_session, uuid.uuid4()) is None

    # Test idempotency: syncing a second time should update existing records without errors
    synced_again = await svc.sync_blueprints_to_db(db_session)
    assert len(synced_again) >= 2
