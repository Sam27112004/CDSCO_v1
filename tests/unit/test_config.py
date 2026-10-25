from app.core.config import Settings


def test_settings_default_values():
    """Verifies standard default configuration values."""
    settings = Settings()
    assert settings.PROJECT_NAME == "CDSCO Medical Device Dossier Builder"
    assert settings.VERSION == "1.0.0"
    assert settings.API_V1_STR == "/api/v1"
    assert settings.MAX_FILE_SIZE_BYTES == 10_485_760
    assert "postgresql" in settings.DATABASE_URL


def test_settings_sync_database_url():
    """Verifies synchronous database URL translation for Alembic."""
    settings = Settings()
    assert settings.sync_database_url.startswith("postgresql://") or settings.sync_database_url.startswith("sqlite://")
