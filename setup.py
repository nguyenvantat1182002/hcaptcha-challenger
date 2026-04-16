import os
from setuptools import setup, find_packages

# This setup.py is provided for legacy compatibility.
# The project is primarily managed via pyproject.toml and hatchling/uv.

setup(
    name="hcaptcha-challenger",
    version="0.19.0", # Controlled by uv-dynamic-versioning in pyproject.toml
    author="QIN2DIM",
    author_email="yaoqinse@gmail.com",
    description="🥂 Gracefully face hCaptcha challenge with multimodal large language model.",
    long_description=open("README.md", encoding="utf-8").read() if os.path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    url="https://github.com/QIN2DIM/hcaptcha-challenger",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "opencv-python>=4.11.0.88,<5.0",
        "pillow>=11.1.0",
        "msgpack>=1.1.1,<2.0.0",
        "typer>=0.21.1",
        "matplotlib>=3.10.8",
        "google-genai>=1.56.0",
        "pytz>=2025.2",
        "httpx[http2]>=0.28.1",
        "loguru>=0.7.3",
        "pydantic-settings>=2.12.0",
        "drissionpage>=4.1.1.2",
        "humancursor>=1.1.5",
        "pyyaml>=6.0.3",
    ],
    # extras_require={
    #     "server": ["fastapi[all]>=0.115.12"],
    #     "dataset": ["typer"],
    #     "camoufox": ["camoufox[geoip]>=0.4.11"],
    # },
    python_requires=">=3.10",
    # entry_points={
    #     "console_scripts": [
    #         "hc=hcaptcha_challenger.cli.main:main",
    #     ],
    # },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Image Processing",
        "Topic :: Scientific/Engineering :: Image Recognition",
        "Topic :: Software Development",
    ],
)
