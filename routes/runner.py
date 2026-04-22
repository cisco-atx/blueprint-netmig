"""Flask routes for script rendering and execution.

This module handles rendering of scripts, execution, streaming outputs,
and file downloads for the NetMig blueprint. It integrates with the
runner and script registry to manage user-triggered script workflows.

File path: routes/runner.py
"""

import logging
import os

from flask import (
    current_app,
    render_template,
    url_for,
    jsonify,
    request,
    session,
    abort,
    send_from_directory,
    Response,
    redirect,
)

logger = logging.getLogger(__name__)


def render():
    """Render the main NetMig page or redirect to the first script."""
    netmig_bp = current_app.blueprints.get("netmig")

    if netmig_bp.scripts:
        first_script_id = next(iter(netmig_bp.scripts))
        return redirect(
            url_for("netmig.render_script", script_id=first_script_id)
        )

    kwargs = {
        "breadcrumbs": [
            {"title": "NetMig", "url": url_for("netmig.render")},
            {"title": "Home"},
        ],
        "scripts": netmig_bp.scripts,
    }
    return render_template("netmig.html", **kwargs)


def render_script(script_id):
    """Render a specific script page with input form."""
    netmig_bp = current_app.blueprints.get("netmig")
    script_data = netmig_bp.scripts_db.get(script_id)

    if not script_data:
        logger.warning("Script not found: %s", script_id)
        abort(404)

    kwargs = {
        "breadcrumbs": [
            {"title": "NetMig", "url": url_for("netmig.render")},
            {
                "title": script_data.get("name", "Unknown Script"),
            },
        ],
        "scripts": netmig_bp.scripts,
        "script_data": script_data,
        "input_html": netmig_bp.runner.scripts[script_id].input(),
    }
    return render_template("netmig.runner.html", **kwargs)


def scan_scripts():
    """Scan and load available scripts."""
    netmig_bp = current_app.blueprints["netmig"]
    netmig_bp.load_scripts()
    return jsonify(netmig_bp.scripts)


def list_script_outputs(script_id):
    """List output files for a given script."""
    base_dir = session["userdata"].get("reports_dir")
    script_dir = os.path.join(base_dir, script_id)

    if not os.path.isdir(script_dir):
        logger.info("No output directory found for script: %s", script_id)
        return jsonify([])

    rows = [
        {"filename": fname}
        for fname in os.listdir(script_dir)
        if os.path.isfile(os.path.join(script_dir, fname))
    ]

    return jsonify(rows)


def stream_script_output(task_id):
    """Stream real-time output of a running task via SSE."""
    netmig_bp = current_app.blueprints.get("netmig")

    return Response(
        netmig_bp.runner.stream_output(task_id),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


def download_script_output(script_id, filename):
    """Download a specific script output file."""
    base_dir = session["userdata"].get("reports_dir")
    script_dir = os.path.join(base_dir, script_id)

    return send_from_directory(
        script_dir,
        filename,
        as_attachment=True,
    )


def run_script(script_id):
    """Execute a script with provided inputs and configuration."""
    netmig_bp = current_app.blueprints.get("netmig")
    script = netmig_bp.scripts_db.get(script_id)

    if not script:
        logger.warning("Attempted to run non-existent script: %s", script_id)
        abort(404)

    data = request.get_json(force=True)

    output_dir = os.path.join(
        session["userdata"].get("reports_dir"), script_id
    )
    os.makedirs(output_dir, exist_ok=True)

    task_params = {
        "script_id": script_id,
        "inputs": data.get("inputs", {}),
        "config": data.get("config", {}),
        "output_dir": output_dir,
    }

    try:
        task = netmig_bp.runner.create_task(**task_params)
        netmig_bp.runner.run(task)
    except Exception as exc:
        logger.exception(
            "Error running script %s: %s", script_id, exc
        )
        abort(500)

    return jsonify({"task_id": task})


def get_script_info(script_id):
    """Retrieve script metadata and README content."""
    netmig_bp = current_app.blueprints.get("netmig")
    script = netmig_bp.scripts_db.get(script_id)

    if not script:
        logger.warning("Script info not found: %s", script_id)
        abort(404)

    readme_path = os.path.join(script["path"], "README.md")
    readme_content = ""

    if os.path.exists(readme_path):
        try:
            with open(readme_path, "r", encoding="utf-8") as file:
                readme_content = file.read()
        except Exception as exc:
            logger.exception(
                "Error reading README for script %s: %s",
                script_id,
                exc,
            )

    return jsonify({"readme": readme_content})
