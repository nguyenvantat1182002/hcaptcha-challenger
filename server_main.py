"""
Standalone entry point for the hcaptcha-challenger server.
Used by cx_Freeze to build a distributable .exe.
"""
import sys
import os

# Ensure .env is loaded from the directory containing the executable
if getattr(sys, "frozen", False):
    # Running as cx_Freeze .exe
    os.chdir(os.path.dirname(sys.executable))
    os.environ.setdefault("DOTENV_PATH", os.path.join(os.path.dirname(sys.executable), ".env"))

# Import directly from server module to avoid importing the full package
# (which pulls in playwright, msgpack, etc. via __init__.py)
from hcaptcha_challenger.server.app import app
from hcaptcha_challenger.utils import init_log

def main():
    init_log()
    
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    
    print(f"Starting hCaptcha Solver Server on {host}:{port}")
    print(f"Working directory: {os.getcwd()}")
    print(f".env location: {os.path.abspath('.env')}")
    
    from waitress import serve
    serve(app, host=host, port=port)

if __name__ == "__main__":
    main()
