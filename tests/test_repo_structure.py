import subprocess
import os
from pathlib import Path

def test_project_root_exists():
    """Verify that the project root directory exists."""
    assert Path(".").resolve().name == "SPMM"

def test_git_repository_exists():
    """Verify that the project is a Git repository."""
    result = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], capture_output=True, text=True)
    assert result.returncode == 0
    assert result.stdout.strip() == "true"

def test_remote_origin_is_correct():
    """Verify the remote origin URL of the Git repository."""
    result = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "https://github.com/larkinthebest/semestralka-spmm-ai.git" in result.stdout.strip()

def test_key_directories_exist():
    """Verify the presence of essential project directories."""
    expected_directories = ["src/", "static/", "tests/", "models/", "samples/", "uploads/"]
    for directory in expected_directories:
        assert Path(directory).is_dir(), f"Directory '{directory}' does not exist."

def test_key_files_exist():
    """Verify the presence of essential project files."""
    expected_files = [
        "Makefile",
        "requirements.txt",
        "README.md",
        "run.py",
        "migrate_database.py",
        "src/api/main.py",
        "static/app.html",
        "static/app.js",
        "static/ui.js",
        "static/chat.js",
        "static/assets.js",
        "static/quiz.js",
        "static/profile.js",
        "static/api.js",
        ".gitignore",
        "Dockerfile",
        "docker-compose.yml",
        "setup.py",
    ]
    for file in expected_files:
        assert Path(file).is_file(), f"File '{file}' does not exist."

def test_static_folder_content_listed():
    """Verify that the static folder contains the expected files."""
    static_files = [f.name for f in Path("static/").iterdir() if f.is_file()]
    expected_static_files = [
        "api.js",
        "app.css",
        "app.html",
        "app.js",
        "assets.js",
        "auth.html",
        "chat.js",
        "enola.jpg",
        "profile.js",
        "quiz.js",
        "styles.css",
        "tutor.png",
        "ui.js",
        "user.png",
    ]
    for expected_file in expected_static_files:
        assert expected_file in static_files, f"Expected file '{expected_file}' not found in static/."
