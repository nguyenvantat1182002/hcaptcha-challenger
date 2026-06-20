import os
import typer
from loguru import logger

app = typer.Typer()

@app.command(name="run", help="Start the API server")
def run_server(
    host: str = typer.Option("0.0.0.0", help="Host IP to bind to"),
    port: int = typer.Option(8000, help="Port to bind to"),
    dev: bool = typer.Option(False, "--dev", help="Run in development mode using standard Flask server")
):
    from hcaptcha_challenger.server.app import app as flask_app
    
    if dev:
        logger.info(f"Starting Flask development server on {host}:{port}")
        flask_app.run(host=host, port=port, debug=True)
    else:
        # Production mode
        if os.name == 'nt':
            # Windows
            logger.info(f"Starting Waitress server on {host}:{port} (Windows production)")
            try:
                from waitress import serve
                serve(flask_app, host=host, port=port)
            except ImportError:
                logger.error("Waitress is not installed. Run 'pip install waitress' or 'uv pip install waitress'.")
                raise typer.Exit(code=1)
        else:
            # Linux / Mac
            logger.info(f"Starting Gunicorn server on {host}:{port} (Linux/Mac production)")
            import subprocess
            try:
                # Gunicorn cannot be imported directly to serve via function in the same way easily,
                # invoking via subprocess is standard or running its internal app runner.
                cmd = ["gunicorn", "-b", f"{host}:{port}", "hcaptcha_challenger.server.app:app"]
                subprocess.run(cmd)
            except FileNotFoundError:
                logger.error("Gunicorn is not installed. Run 'pip install gunicorn' or 'uv pip install gunicorn'.")
                raise typer.Exit(code=1)
