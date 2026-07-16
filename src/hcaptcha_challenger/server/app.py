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
import threading
import uuid
import time

pending_tasks = {}
task_lock = threading.Lock()
background_loop = None
bg_thread_started = False
bg_thread_lock = threading.Lock()

def get_or_create_background_loop():
    global background_loop, bg_thread_started
    if not bg_thread_started:
        with bg_thread_lock:
            if not bg_thread_started:
                background_loop = asyncio.new_event_loop()
                def start_loop(loop):
                    asyncio.set_event_loop(loop)
                    loop.run_forever()
                t = threading.Thread(target=start_loop, args=(background_loop,), daemon=True)
                t.start()
                bg_thread_started = True
    return background_loop

def cleanup_expired_tasks():
    current_time = time.time()
    with task_lock:
        keys_to_delete = []
        for task_id, task_data in pending_tasks.items():
            if current_time > task_data.get("created_at", 0) + task_data.get("timeout", 300):
                keys_to_delete.append(task_id)
        for k in keys_to_delete:
            del pending_tasks[k]

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

@app.route("/createTask", methods=["POST"])
def create_task():
    """
    Create an async hCaptcha solve task.
    Expects JSON payload with 'prompt' and 'image' (base64).
    Optional 'timeout' (default 300s).
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Invalid or missing JSON payload"}), 400
            
        prompt = data.get("prompt")
        image_b64 = data.get("image")
        challenge_type = data.get("challenge_type")
        timeout = float(data.get("timeout", 300))
        
        logger.info(f"Received createTask request - prompt: '{prompt}', timeout: {timeout}")
        
        cleanup_expired_tasks()
        
        task_id = str(uuid.uuid4())
        with task_lock:
            pending_tasks[task_id] = {
                "status": "processing",
                "result": None,
                "error": None,
                "created_at": time.time(),
                "timeout": timeout
            }
            
        loop = get_or_create_background_loop()
        
        async def run_solver_task():
            try:
                solver = SolverService(timeout=timeout)
                coordinates = await solver.solve_challenge(
                    prompt=prompt, 
                    image_b64=image_b64, 
                    challenge_type=challenge_type
                )
                with task_lock:
                    if task_id in pending_tasks:
                        pending_tasks[task_id]["status"] = "ready"
                        pending_tasks[task_id]["result"] = coordinates
            except Exception as e:
                logger.exception("Error in background solver task")
                with task_lock:
                    if task_id in pending_tasks:
                        pending_tasks[task_id]["status"] = "failed"
                        pending_tasks[task_id]["error"] = str(e)
                        
        asyncio.run_coroutine_threadsafe(run_solver_task(), loop)
        
        return jsonify({
            "success": True,
            "taskId": task_id
        })
        
    except Exception as e:
        logger.exception("Error processing /createTask request")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/getTaskResult", methods=["POST"])
def get_task_result():
    """
    Get the result of an async hCaptcha solve task.
    Expects JSON payload with 'taskId'.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Invalid or missing JSON payload"}), 400
            
        task_id = data.get("taskId")
        if not task_id:
            return jsonify({"success": False, "error": "Missing 'taskId' in payload"}), 400
            
        cleanup_expired_tasks()
        
        with task_lock:
            if task_id not in pending_tasks:
                return jsonify({"success": False, "error": "Task not found or expired"}), 404
                
            task_data = pending_tasks[task_id]
            status = task_data["status"]
            
            if status == "processing":
                return jsonify({"success": True, "status": "processing"})
                
            elif status == "ready":
                result = task_data["result"]
                del pending_tasks[task_id]
                return jsonify({
                    "success": True,
                    "status": "ready",
                    "solution": {"coordinates": result}
                })
                
            elif status == "failed":
                error_msg = task_data.get("error", "Unknown error")
                del pending_tasks[task_id]
                return jsonify({
                    "success": False,
                    "status": "failed",
                    "error": error_msg
                })
                
    except Exception as e:
        logger.exception("Error processing /getTaskResult request")
        return jsonify({"success": False, "error": str(e)}), 500

def create_app():
    return app
