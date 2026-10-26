import json
from pathlib import Path
from app.schemas.definition import FormBlueprint


def test_form_md_14_fixture_integrity():
    """Validates that Form MD-14 JSON blueprint fixture adheres to statutory contract."""
    fixture_path = (
        Path(__file__).resolve().parent.parent.parent
        / "backend"
        / "app"
        / "fixtures"
        / "blueprints"
        / "form_md_14.json"
    )
    assert fixture_path.exists(), f"Fixture file not found at {fixture_path}"

    with open(fixture_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    # Validate against Pydantic schema contract
    blueprint = FormBlueprint.model_validate(raw_data)
    assert blueprint.form_code == "MD-14"
    assert blueprint.version == "1.0"

    # Verify exactly 36 discrete upload slots
    assert len(blueprint.slots) == 36, f"Expected 36 slots, found {len(blueprint.slots)}"

    # Verify uniqueness of slot_ids
    slot_ids = [slot.slot_id for slot in blueprint.slots]
    assert len(slot_ids) == len(set(slot_ids)), "Duplicate slot_id detected in blueprint"

    # Verify regulatory constraints
    for slot in blueprint.slots:
        assert slot.max_size_mb <= 10.0, f"Slot {slot.slot_id} exceeds 10MB portal threshold"
        assert "application/pdf" in slot.allowed_mimes

        # If generatable, template_key must be present
        if "GENERATE" in slot.fulfillment_modes:
            assert slot.template_key is not None, f"Slot {slot.slot_id} is generatable but missing template_key"

        # Verify all 8 guidance points are populated
        assert len(slot.guidance.what_it_is) > 0
        assert len(slot.guidance.why_it_is_needed) > 0
        assert len(slot.guidance.official_citation) > 0
        assert len(slot.guidance.who_issues) > 0
        assert len(slot.guidance.validity_period) > 0
        assert len(slot.guidance.mandatory_inclusions) > 0
        assert len(slot.guidance.critical_pitfalls) > 0


def test_form_md_14_slot_taxonomy_coverage():
    """Verifies statutory anchor slots exist in Form MD-14 taxonomy."""
    fixture_path = (
        Path(__file__).resolve().parent.parent.parent
        / "backend"
        / "app"
        / "fixtures"
        / "blueprints"
        / "form_md_14.json"
    )
    with open(fixture_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    blueprint = FormBlueprint.model_validate(raw_data)
    slot_map = {slot.slot_id: slot for slot in blueprint.slots}

    # Statutory mandatory slots verification
    assert "1.0" in slot_map  # Covering Letter
    assert "2.0" in slot_map  # Fee Challan
    assert "3.0" in slot_map  # Form MD-14
    assert "4.0" in slot_map  # Power of Attorney
    assert "7.1" in slot_map  # FSC Origin
    assert "7.2" in slot_map  # FSC Reference
    assert "8.1" in slot_map  # ISO 13485
    assert "8.3" in slot_map  # Declaration of Conformity
    assert "9.0" in slot_map  # PMF
    assert "10.1" in slot_map # DMF Executive Summary
    assert "10.8" in slot_map # Essential Principles
    assert "10.11" in slot_map # Biocompatibility
    assert "10.14" in slot_map # Sterilization Validation
    assert "10.20" in slot_map # 3 Batch CoAs
