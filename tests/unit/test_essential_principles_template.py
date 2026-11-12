"""Unit tests for the Engine 1 essential_principles.html Jinja2 template."""

from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape


TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "backend" / "app" / "templates"


def _get_jinja_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )


def _sample_context() -> dict:
    return {
        "applicant": {
            "legal_name": "Apex MedTech Private Limited",
            "registered_address": "Plot 42, Okhla Industrial Area, New Delhi, 110020",
            "signatory_name": "Dr. Rajesh Sharma",
            "signatory_designation": "Director & Authorized Indian Agent",
        },
        "manufacturer": {
            "legal_name": "BioSensors International AG",
            "country": "Switzerland",
            "signatory_name": "Dr. Markus Weber",
            "signatory_designation": "VP Global Regulatory Affairs",
        },
        "device": {
            "brand_name": "CardioTrack Pacemaker Lead System",
            "generic_name": "Implantable Cardiac Pacing Lead",
            "risk_class": "CLASS_D",
            "is_sterile": True,
            "contains_software": False,
            "contains_medicinal_substance": False,
            "contains_animal_tissue": False,
        },
        "submission": {
            "tracking_code": "SUB-2026-MD14-00412",
            "application_code": "MD-14",
            "submission_date": "2026-10-22",
        },
    }


def test_essential_principles_renders_custom_clauses_and_summary():
    """Verifies custom clause table rendering, standards, evidence citations, and metrics."""
    env = _get_jinja_env()
    template = env.get_template("essential_principles.html")

    context = _sample_context()
    form_data = {
        "clauses": [
            {
                "clause_id": "EP_01",
                "clause_number": "1",
                "title": "General Safety and Performance Principles",
                "applicable": True,
                "justification": None,
                "cited_standards": ["ISO 13485:2016", "ISO 14971:2019"],
                "evidence_document_titles": ["Risk Management Report RMR-2025-01", "ISO 13485 Certificate"],
            },
            {
                "clause_id": "EP_08",
                "clause_number": "8",
                "title": "Infection and Microbial Contamination (Sterility)",
                "applicable": True,
                "justification": None,
                "cited_standards": ["ISO 11135:2014"],
                "evidence_document_titles": ["Ethylene Oxide Sterilization Validation Report VAL-ETO-2024"],
            },
            {
                "clause_id": "EP_12",
                "clause_number": "12",
                "title": "Devices Incorporating Software",
                "applicable": False,
                "justification": "Passive mechanical lead containing no embedded software.",
                "cited_standards": [],
                "evidence_document_titles": [],
            },
        ]
    }

    html = template.render(context=context, form_data=form_data)

    # Print CSS & Base Inheritance
    assert "size: A4 portrait;" in html
    assert "display: table-header-group;" in html
    assert "Essential Principles Checklist" in html

    # Metrics summary
    assert "3 Principles" in html
    assert "2 Complied" in html
    assert "1 Waived" in html

    # Clause Details
    assert "ISO 13485:2016" in html
    assert "Risk Management Report RMR-2025-01" in html
    assert "Ethylene Oxide Sterilization Validation Report VAL-ETO-2024" in html
    assert "Passive mechanical lead containing no embedded software." in html
    assert "Dr. Markus Weber" in html


def test_essential_principles_defaults_to_15_predicate_driven_clauses():
    """Verifies that omitting form_data.clauses generates all 15 MDR clauses dynamically."""
    env = _get_jinja_env()
    template = env.get_template("essential_principles.html")

    # Non-sterile, passive device
    ctx_passive = _sample_context()
    ctx_passive["device"]["is_sterile"] = False
    ctx_passive["device"]["contains_software"] = False

    html_passive = template.render(context=ctx_passive, form_data={})
    assert "15 Principles" in html_passive
    assert "12 Complied" in html_passive
    assert "3 Waived" in html_passive
    assert "Device is supplied non-sterile per product specification" in html_passive
    assert "contains no embedded software" in html_passive

    # Sterile + Software + Drug-device combination -> all 15 complied!
    ctx_active = _sample_context()
    ctx_active["device"]["is_sterile"] = True
    ctx_active["device"]["contains_software"] = True
    ctx_active["device"]["contains_medicinal_substance"] = True

    html_active = template.render(context=ctx_active, form_data={})
    assert "15 Principles" in html_active
    assert "15 Complied" in html_active
    assert "0 Waived" in html_active
    assert "IEC 62304:2006" in html_active
    assert "ISO 11135:2014" in html_active


def test_essential_principles_handles_minimal_context_safely():
    """Verifies no raw 'None' leakage when optional metadata is missing."""
    env = _get_jinja_env()
    template = env.get_template("essential_principles.html")

    minimal_ctx = {
        "applicant": {"legal_name": "MedTech Solutions Pvt Ltd"},
        "manufacturer": {},
        "device": {"brand_name": "OrthoScrew System"},
        "submission": {"application_code": "MD-7"},
    }

    html = template.render(context=minimal_ctx, form_data={})
    assert "MedTech Solutions Pvt Ltd" in html
    assert "OrthoScrew System" in html
    assert "CDSCO Form MD-7" in html
    assert "None" not in html
