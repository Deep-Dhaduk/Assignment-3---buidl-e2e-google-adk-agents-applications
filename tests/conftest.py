import pytest

from assignment.db import engine_for, initialize


@pytest.fixture(autouse=True)
def isolated_data(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{(tmp_path / 'test.db').as_posix()}")
    monkeypatch.setenv("ADK_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("ADK_ARTIFACT_DIR", str(tmp_path / "artifacts"))
    monkeypatch.setenv("REVIEW_EXECUTION", "disabled")
    initialize()
    yield
    # Release Windows database handles before pytest cleans temporary directories.
    from assignment.db import engine

    engine().dispose()
    engine_for.cache_clear()
