import subprocess
import uuid

import pytest

from app.workers.scan_repository import _clone_github_repo
from config import settings


@pytest.fixture
def local_git_repo(tmp_path):
    """A tiny local git repo we can clone via file:// — no network needed."""
    repo_dir = tmp_path / "source_repo"
    repo_dir.mkdir()
    (repo_dir / "main.py").write_text("print('hello')\n")
    subprocess.run(["git", "init", "-q", str(repo_dir)], check=True)
    subprocess.run(["git", "-C", str(repo_dir), "config", "user.email", "a@b.com"], check=True)
    subprocess.run(["git", "-C", str(repo_dir), "config", "user.name", "test"], check=True)
    subprocess.run(["git", "-C", str(repo_dir), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo_dir), "commit", "-q", "-m", "init"], check=True)
    return repo_dir


def test_clone_github_repo_success(local_git_repo, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "STORAGE_PATH", str(tmp_path / "storage"))
    project_id = uuid.uuid4()
    repo_id = uuid.uuid4()

    dest = _clone_github_repo(f"file://{local_git_repo}", project_id, repo_id)

    assert dest.exists()
    assert (dest / "main.py").exists()


def test_clone_github_repo_invalid_url_raises(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "STORAGE_PATH", str(tmp_path / "storage"))
    project_id = uuid.uuid4()
    repo_id = uuid.uuid4()

    with pytest.raises(ValueError, match="git clone failed"):
        _clone_github_repo(f"file://{tmp_path}/does-not-exist", project_id, repo_id)


def test_clone_github_repo_overwrites_existing_dest(local_git_repo, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "STORAGE_PATH", str(tmp_path / "storage"))
    project_id = uuid.uuid4()
    repo_id = uuid.uuid4()

    dest = _clone_github_repo(f"file://{local_git_repo}", project_id, repo_id)
    (dest / "stale_file.txt").write_text("should be gone after re-clone")

    dest2 = _clone_github_repo(f"file://{local_git_repo}", project_id, repo_id)

    assert dest == dest2
    assert not (dest2 / "stale_file.txt").exists()
    assert (dest2 / "main.py").exists()
