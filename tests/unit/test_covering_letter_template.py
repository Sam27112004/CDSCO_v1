"""Unit tests for the Engine 1 covering_letter.html Jinja2 template and statutory print CSS."""

from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape


TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "backend" / "app" / "templates"


def _get_jinja_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )


def _sample_md14_context() -> dict:
    return {
        "applicant": {
            "legal_name": "Apex MedTech Private Limited",
            "registered_address": "Plot 42, Okhla Industrial Area, Phase-III, New Delhi, 110020, India",
            "constitution_type": "Private Limited Company",
            "wholesale_licence_number": "DL-OKH-2023-004218 (Form 20B/21B)",
            "cin": "U33110DL2018PTC334912",
            "signatory_name": "Dr. Rajesh Sharma",
            "signatory_designation": "Director & Authorized Indian Agent",
            "contact_email": "regulatory@apexmedtech.in",
            "contact_phone": "+91-11-45678900",
        },
        "manufacturer": {
            "legal_name": "BioSensors International AG",
            "site_name": "Main Manufacturing Campus",
            "site_address": "Technoparkstrasse 1, 8005 Zurich, Switzerland",
            "country": "Switzerland",
            "site_registration_number": "CH-MFG-2018-9921",
        },
        "device": {
            "brand_name": "CardioTrack Pacemaker Lead System",
            "generic_name": "Implantable Cardiac Pacing Lead",
            "device_type": "MEDICAL_DEVICE",
            "risk_class": "CLASS_D",
            "intended_use": "Transvenous pacing and sensing of cardiac chambers in bradycardia therapies.",
            "model_variants": ["CT-PL-052", "CT-PL-058"],
            "shelf_life_months": 36,
            "is_sterile": True,
            "sterilization_method": "Ethylene Oxide (EtO)",
        },
        "submission": {
            "tracking_code": "SUB-2026-MD14-00412",
            "application_code": "MD-14",
            "filing_modality": "FRESH",
            "submission_date": "2026-10-22",
            "bharatkosh_challan_id": "BK-2026-881920",
            "fee_paid_inr": 150000,
        },
    }


def test_covering_letter_md14_renders_all_statutory_sections():
    """Verifies Form MD-14 covering letter renders print CSS, CLA addressee, table, and enclosures."""
    env = _get_jinja_env()
    template = env.get_template("covering_letter.html")

    context = _sample_md14_context()
    form_data = {
        "subject_line": "Application for Grant of Licence to Import Class D Medical Device under Rule 34",
        "reference_portal_id": "CDSCO/MD/2026/009182",
        "payment_date": "2026-10-20",
        "device_model_table": [
            {
                "model_number": "CT-PL-052",
                "specification": "52cm Bipolar Active Fixation Lead",
                "accessories": "Stylet Kit",
            },
            {
                "model_number": "CT-PL-058",
                "specification": "58cm Bipolar Active Fixation Lead",
                "accessories": "Stylet Kit",
            },
        ],
        "enclosures_list": [
            "Treasury Fee Challan in BharatKosh",
            "Executed Power of Attorney in First Schedule Part I",
            "Free Sale Certificate issued by Swissmedic",
        ],
        "custom_declarations": "We confirm that applied models match those marketed in Switzerland.",
    }

    html = template.render(context=context, form_data=form_data)

    # 1. Print CSS verification (DEF-CDSCO-001 Section 10.4)
    assert "size: A4 portrait;" in html
    assert "margin: 20mm 15mm 20mm 15mm;" in html
    assert "display: table-header-group;" in html
    assert "page-break-inside: avoid;" in html
    assert "@bottom-center" in html

    # 2. Letterhead & CLA addressee
    assert "Apex MedTech Private Limited" in html
    assert "DL-OKH-2023-004218 (Form 20B/21B)" in html
    assert "Drugs Controller General (India)" in html
    assert "FDA Bhawan, Kotla Road, New Delhi" in html

    # 3. Context injection & dynamic table rows
    assert "CDSCO/MD/2026/009182" in html
    assert "SUB-2026-MD14-00412" in html
    assert "BioSensors International AG" in html
    assert "Technoparkstrasse 1, 8005 Zurich, Switzerland" in html
    assert "BK-2026-881920" in html
    assert "INR 150000" in html
    assert "CT-PL-052" in html
    assert "58cm Bipolar Active Fixation Lead" in html
    assert "Free Sale Certificate issued by Swissmedic" in html
    assert "Dr. Rajesh Sharma" in html


def test_covering_letter_md7_domestic_and_md3_sla_routing():
    """Verifies addressee routing and domestic rule text for MD-7 (CLA) and MD-3 (SLA)."""
    env = _get_jinja_env()
    template = env.get_template("covering_letter.html")

    # MD-7 Domestic Class C/D -> CLA
    md7_ctx = _sample_md14_context()
    md7_ctx["submission"]["application_code"] = "MD-7"
    md7_ctx["device"]["is_sterile"] = False
    html_md7 = template.render(context=md7_ctx, form_data={})

    assert "Drugs Controller General (India)" in html_md7
    assert "Manufacturing Licence in Form MD-7" in html_md7
    assert "Non-Sterile" in html_md7
    assert "Rule 26" in html_md7

    # MD-3 Domestic Class A/B -> State Licensing Authority (SLA)
    md3_ctx = _sample_md14_context()
    md3_ctx["submission"]["application_code"] = "MD-3"
    md3_ctx["device"]["risk_class"] = "CLASS_B"
    html_md3 = template.render(context=md3_ctx, form_data={})

    assert "The State Licensing Authority (SLA)" in html_md3
    assert "Drugs Controller General (India)" not in html_md3


def test_covering_letter_handles_minimal_context_gracefully():
    """Verifies safe default fallbacks when optional form_data or context keys are omitted."""
    env = _get_jinja_env()
    template = env.get_template("covering_letter.html")

    minimal_ctx = {
        "applicant": {"legal_name": "MedTest India Pvt Ltd"},
        "manufacturer": {},
        "device": {"brand_name": "OrthoFix Bone Plate"},
        "submission": {"application_code": "MD-14"},
    }

    html = template.render(context=minimal_ctx, form_data={})

    assert "MedTest India Pvt Ltd" in html
    assert "OrthoFix Bone Plate" in html
    assert "Standard Family Configuration" in html
    assert "None" not in html
