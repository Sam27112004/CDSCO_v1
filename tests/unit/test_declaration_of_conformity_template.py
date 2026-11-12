"""Unit tests for the Engine 1 declaration_of_conformity.html Jinja2 template."""

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
            "wholesale_licence_number": "DL-OKH-2023-004218 (Form 20B/21B)",
            "signatory_name": "Dr. Rajesh Sharma",
            "signatory_designation": "Director & Authorized Indian Agent",
        },
        "manufacturer": {
            "legal_name": "BioSensors International AG",
            "site_name": "Zürich Cleanroom Campus",
            "site_address": "Technoparkstrasse 1, 8005 Zurich, Switzerland",
            "country": "Switzerland",
            "site_registration_number": "CH-MFG-2018-9921",
            "signatory_name": "Dr. Markus Weber",
            "signatory_designation": "VP Global Regulatory Affairs",
        },
        "device": {
            "brand_name": "CardioTrack Pacemaker Lead System",
            "generic_name": "Implantable Cardiac Pacing Lead",
            "device_type": "MEDICAL_DEVICE",
            "risk_class": "CLASS_D",
            "intended_use": "Transvenous pacing and sensing of cardiac chambers.",
            "model_variants": ["CT-PL-052", "CT-PL-058"],
            "is_sterile": True,
            "contains_software": False,
        },
        "submission": {
            "tracking_code": "SUB-2026-MD14-00412",
            "application_code": "MD-14",
            "submission_date": "2026-10-22",
        },
    }


def test_doc_md14_renders_manufacturer_letterhead_and_all_sections():
    """Verifies DoC renders on manufacturer letterhead with sole responsibility & Notified Body details."""
    env = _get_jinja_env()
    template = env.get_template("declaration_of_conformity.html")

    context = _sample_context()
    form_data = {
        "doc_number": "DOC-2026-BS-09",
        "issue_date": "2026-10-18",
        "place_of_issue": "Zurich, Switzerland",
        "manufacturer_srn": "CH-MF-00001234",
        "gmdn_code": "35852",
        "basic_udi_di": "0761234567890123",
        "iso_13485_cert_no": "QMS-2025-8812",
        "iso_13485_valid_until": "2028-11-30",
        "conformity_route": "MDR 2017 Fourth Schedule & EU MDR Annex IX",
        "notified_body_name": "BSI Assurance UK Ltd",
        "notified_body_id": "0086",
        "ce_certificate_no": "CE-719920",
        "applied_models": [
            {"code": "CT-PL-052", "description": "52cm Bipolar Lead"},
            {"code": "CT-PL-058", "description": "58cm Bipolar Lead"},
        ],
        "harmonized_standards": [
            {"code": "ISO 13485:2016", "title": "Quality management systems"},
            {"code": "ISO 14971:2019", "title": "Risk management to medical devices"},
        ],
    }

    html = template.render(context=context, form_data=form_data)

    # Letterhead uses Manufacturer, not Indian Agent
    assert "BioSensors International AG" in html
    assert "CH-MF-00001234" in html

    # Sole responsibility & MDR 2017 citation
    assert "sole responsibility" in html
    assert "Medical Devices Rules, 2017" in html

    # Indian Agent included for Import MD-14
    assert "Authorized Indian Agent (Rule 34)" in html
    assert "Apex MedTech Private Limited" in html
    assert "DL-OKH-2023-004218" in html

    # Product codes, GMDN, Notified Body, Signatory
    assert "DOC-2026-BS-09" in html
    assert "35852" in html
    assert "0761234567890123" in html
    assert "BSI Assurance UK Ltd" in html
    assert "CE-719920" in html
    assert "58cm Bipolar Lead" in html
    assert "Dr. Markus Weber" in html


def test_doc_predicate_default_standards_and_domestic_md7_mode():
    """Verifies predicate-driven default standards and omission of Indian Agent block for MD-7."""
    env = _get_jinja_env()
    template = env.get_template("declaration_of_conformity.html")

    # Domestic MD-7 with Sterile + Software enabled
    ctx = _sample_context()
    ctx["submission"]["application_code"] = "MD-7"
    ctx["device"]["is_sterile"] = True
    ctx["device"]["contains_software"] = True

    html = template.render(context=ctx, form_data={})

    assert "Authorized Indian Agent (Rule 34)" not in html
    assert "ISO 11135 / ISO 11137" in html
    assert "IEC 62304:2006+A1:2015" in html
    assert "CT-PL-052" in html


def test_doc_handles_minimal_context_safely():
    """Verifies safe default fallbacks with zero raw 'None' leakage."""
    env = _get_jinja_env()
    template = env.get_template("declaration_of_conformity.html")

    minimal_ctx = {
        "applicant": {"legal_name": "Apex MedTech Pvt Ltd"},
        "manufacturer": {},
        "device": {"brand_name": "Surgical Catheter"},
        "submission": {"application_code": "MD-14"},
    }

    html = template.render(context=minimal_ctx, form_data={})
    assert "Apex MedTech Pvt Ltd" in html
    assert "Surgical Catheter" in html
    assert "Full Product Family" in html
    assert "None" not in html
