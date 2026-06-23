from flask import Flask, jsonify, request
from loguru import logger

from hcaptcha_challenger.server.solve import SolverService

app = Flask(__name__)

# (Removed singleton initialization)

from pathlib import Path
from hcaptcha_challenger.agent.config import AgentConfig
from hcaptcha_challenger.tools.supervisor import SupervisorCache

@app.route("/health", methods=["GET"])
def health_check():
    """Simple health check endpoint."""
    config = AgentConfig()
    cache = SupervisorCache(
        cache_file=Path(config.cache_dir, "supervisor_guidelines.json")
    )
    return jsonify({
        "status": "ok",
        "version": "0.19.0",
        "solve_stats": cache.get_all_stats()
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
        
        logger.info(f"Received solve request - prompt: '{prompt}', challenge_type: '{challenge_type}', timeout: {timeout}")
        
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

@app.route("/report", methods=["POST"])
def report():
    """
    Report the success or failure of a challenge to update the Supervisor cache.
    Expects JSON payload with 'prompt' (string) and 'success' (boolean).
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Invalid or missing JSON payload"}), 400
            
        prompt = data.get("prompt")
        success = data.get("success")
        
        if prompt is None or success is None:
            return jsonify({"success": False, "error": "Missing 'prompt' or 'success' in payload"}), 400
            
        config = AgentConfig()
        cache = SupervisorCache(
            cache_file=Path(config.cache_dir, "supervisor_guidelines.json")
        )
        
        if success:
            cache.increment_success_count(prompt)
            logger.info(f"Reported success for prompt: '{prompt}'")
        else:
            cache.increment_fail_count(prompt)
            logger.info(f"Reported failure for prompt: '{prompt}'")
            
        return jsonify({"success": True})
        
    except Exception as e:
        logger.exception("Error processing /report request")
        return jsonify({"success": False, "error": str(e)}), 500

def create_app():
    return app
