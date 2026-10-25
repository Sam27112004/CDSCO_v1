from app.models.base import Base
from app.models.application_definition import ApplicationDefinition
from app.models.profile import Profile
from app.models.submission import Submission
from app.models.submission_entity import SubmissionEntity
from app.models.evidence import EvidenceDocument, EvidenceLink
from app.models.validation import ValidationIssue
from app.models.job import BackgroundJob


def test_core_tables_registered_in_metadata():
    """Verifies that all 8 core tables are properly registered in SQLAlchemy metadata."""
    expected_tables = {
        "application_definitions",
        "profiles",
        "submissions",
        "submission_entities",
        "evidence_documents",
        "evidence_links",
        "validation_issues",
        "background_jobs",
    }
    actual_tables = set(Base.metadata.tables.keys())
    assert expected_tables.issubset(actual_tables), f"Missing tables: {expected_tables - actual_tables}"


def test_model_instantiation():
    """Verifies basic model attribute binding and defaults."""
    app_def = ApplicationDefinition(
        code="MD-14",
        title="Application for Grant of Licence to Import Medical Device",
        version="1.0",
        schema_payload={"slots": []},
        is_active=True,
    )
    assert app_def.code == "MD-14"
    assert app_def.is_active is True

    profile = Profile(
        profile_type="APPLICANT",
        name="MedTech India Pvt Ltd",
        data_payload={"pan": "AAACM1234F"},
    )
    assert profile.profile_type == "APPLICANT"
    assert profile.name == "MedTech India Pvt Ltd"
