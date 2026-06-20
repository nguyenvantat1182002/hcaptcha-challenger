from flask import Flask, jsonify, request
from loguru import logger

from hcaptcha_challenger.server.solve import get_solver_service

app = Flask(__name__)

# Initialize the solver service when the app starts
with app.app_context():
    try:
        get_solver_service()
    except Exception as e:
        logger.error(f"Failed to initialize SolverService: {e}")

@app.route("/health", methods=["GET"])
def health_check():
    """Simple health check endpoint."""
    return jsonify({
        "status": "ok",
        "version": "0.19.0"
    })

import asyncio

@app.route("/solve", methods=["POST"])
def solve():
    """
    Solve hCaptcha challenge.
    Expects JSON payload with 'prompt' (string) and 'image' (base64 string).
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Invalid or missing JSON payload"}), 400
            
        prompt = data.get("prompt")
        image_b64 = data.get("image")
        challenge_type = data.get("challenge_type")
        
        if not prompt or not image_b64:
            return jsonify({"success": False, "error": "Missing 'prompt' or 'image' in payload"}), 400
            
        solver = get_solver_service()
        
        # Run the async solver in a new event loop for this request
        coordinates = asyncio.run(solver.solve_challenge(prompt, image_b64, challenge_type))
        
        return jsonify({
            "success": True,
            "coordinates": coordinates
        })
        
    except Exception as e:
        logger.exception("Error processing /solve request")
        return jsonify({"success": False, "error": str(e)}), 500

def create_app():
    return app
