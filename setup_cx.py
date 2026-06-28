"""
cx_Freeze build script for hcaptcha-challenger server.

Usage:
    python setup_cx.py build
"""
import sys
from pathlib import Path
from cx_Freeze import setup, Executable

# Collect all .md data files used as system prompts
src_root = Path("src/hcaptcha_challenger")
md_data_files = []
for md_file in src_root.rglob("*.md"):
    # Destination preserves relative path inside the package
    dest_dir = str(md_file.parent)
    md_data_files.append((str(md_file), dest_dir))

# Include data files that cx_Freeze can't auto-detect
include_files = []
for md_file in src_root.rglob("*.md"):
    rel = md_file.relative_to("src")
    include_files.append((str(md_file), str(Path("lib") / rel)))

# Also include .env.example as a template
if Path(".env.example").exists():
    include_files.append((".env.example", ".env.example"))

build_exe_options = {
    "packages": [
        # Core server
        "hcaptcha_challenger.server",
        "hcaptcha_challenger.server.app",
        "hcaptcha_challenger.server.solve",
        "hcaptcha_challenger.agent.config",
        "hcaptcha_challenger.models",
        "hcaptcha_challenger.utils",
        # Tools
        "hcaptcha_challenger.tools",
        "hcaptcha_challenger.tools.challenge_router",
        "hcaptcha_challenger.tools.image_classifier",
        "hcaptcha_challenger.tools.spatial",
        "hcaptcha_challenger.tools.internal",
        "hcaptcha_challenger.tools.internal.providers",
        "hcaptcha_challenger.tools.internal.providers.gemini",
        "hcaptcha_challenger.tools.internal.providers.openrouter",
        "hcaptcha_challenger.tools.supervisor",
        # Helper
        "hcaptcha_challenger.helper",
        # Agent (required by __init__.py import chain)
        "hcaptcha_challenger.agent",
        "hcaptcha_challenger.agent.challenger",
        "hcaptcha_challenger.agent.collector",
        "hcaptcha_challenger.agent.robotic_arm",
        # Dependencies that need explicit inclusion
        "flask",
        "waitress",
        "pydantic",
        "pydantic_settings",
        "pydantic_core",
        "dotenv",
        "google.genai",
        "openai",
        "httpx",
        "cv2",
        "matplotlib",
        "numpy",
        "PIL",
        "loguru",
        "filelock",
        "tenacity",
        "pytz",
        "certifi",
        "anyio",
        "httpcore",
        "sniffio",
        "idna",
        "annotated_types",
        "typing_extensions",
        "msgpack",
        "playwright",
        "camoufox",
    ],
    "excludes": [
        # Exclude heavy packages not needed by server
        "tkinter",
        "unittest",
        "test",
        "ipykernel",
        "ipywidgets",
        "jupyterlab",
        "notebook",
        "black",
        "ruff",
        "pytest",
    ],
    "include_files": include_files,
    "path": [*sys.path, "src"],
}

setup(
    name="hcaptcha-solver-server",
    version="0.19.0",
    description="hCaptcha Solver API Server",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            script="server_main.py",
            target_name="hcaptcha_server.exe",
            base=None,  # Console application
        )
    ],
)
