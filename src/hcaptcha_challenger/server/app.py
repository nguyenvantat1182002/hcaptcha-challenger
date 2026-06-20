from flask import Flask, jsonify, request
from loguru import logger

from hcaptcha_challenger.server.solve import SolverService

app = Flask(__name__)

# (Removed singleton initialization)

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
        timeout = data.get("timeout")
        
        solver = SolverService(timeout=timeout)
        
        # Run the async solver in a new event loop for this request
        coordinates = asyncio.run(solver.solve_challenge(
            prompt=prompt, 
            image_b64=image_b64, 
            challenge_type=challenge_type
        ))
        
        return jsonify({
            "success": True,
            "coordinates": coordinates
        })
        
    except Exception as e:
        logger.exception("Error processing /solve request")
        return jsonify({"success": False, "error": str(e)}), 500

def create_app():
    return app
