"""
Script management routes.

Provides endpoints for rendering, uploading, deleting, and cloning
scripts within the NetMig module. Handles file system operations,
Git interactions, and integrates with Flask request/response flow.

File path: routes/manage.py
"""

import logging
import os
import shutil
import subprocess

from flask import (
    current_app,
    jsonify,
    render_template,
    request,
    url_for,
)

logger = logging.getLogger(__name__)


def render_manage_scripts():
    """Render the script management page."""
    netmig_bp = current_app.blueprints["netmig"]

    kwargs = {
        "add_text": "Add Script",
        "columns": ["Name", "Version", "Description"],
        "dataset": [
            {
                "Id": script_id,
                "Name": script_data.get("name", "Unnamed Script"),
                "Version": script_data.get("version", "Unknown"),
                "Description": script_data.get(
                    "description",
                    "No description available."
                ),
                "Icon": script_data.get("icon", "fa fa-terminal"),
            }
            for script_id, script_data in netmig_bp.scripts.items()
        ],
        "breadcrumbs": [
            {"title": "NetMig", "url": url_for("netmig.render")},
            {"title": "Scripts"},
        ],
        "scripts": netmig_bp.scripts,
    }

    return render_template("netmig.manage.html", **kwargs)


def delete_scripts():
    """Delete selected scripts from the file system."""
    netmig_bp = current_app.blueprints["netmig"]
    payload = request.get_json()
    keys_to_delete = payload.get("keys", [])
    deleted = []

    logger.info("Deleting scripts: %s", keys_to_delete)

    for key in keys_to_delete:
        script_path = os.path.join(netmig_bp.SCRIPTS_DIR, key)
        if os.path.exists(script_path):
            try:
                shutil.rmtree(script_path)
                logger.info("Deleted script directory: %s", script_path)
                deleted.append(key)
            except Exception as exc:
                logger.exception(
                    "Error deleting script: %s", script_path
                )
                return jsonify(error=str(exc)), 500

        netmig_bp.load_scripts()
        deleted.append(key)

    return jsonify(deleted=deleted)


def upload_script():
    """Upload and extract a new script from provided files."""
    netmig_bp = current_app.blueprints["netmig"]
    files = request.files.getlist("files")

    if not files:
        logger.warning("No files uploaded")
        return jsonify({"error": "No files uploaded"}), 400

    scripts_dir = netmig_bp.SCRIPTS_DIR

    first_file = files[0]
    root_dir = first_file.filename.split("/", 1)[0]
    target_dir = os.path.join(scripts_dir, root_dir)

    if os.path.exists(target_dir):
        logger.warning("Script already exists: %s", target_dir)
        return jsonify({"error": "Script already exists"}), 400

    os.makedirs(target_dir, exist_ok=True)

    for file in files:
        rel_path = file.filename
        full_path = os.path.join(scripts_dir, rel_path)

        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        file.save(full_path)
        logger.info("Saved file: %s", full_path)

    netmig_bp.load_scripts()

    return jsonify({"status": "ok"})


def clone_script():
    """Clone a script from a Git repository."""
    netmig_bp = current_app.blueprints["netmig"]
    data = request.get_json()
    repo_url = data.get("repo_url")

    if not repo_url:
        logger.warning("Repository URL not provided")
        return jsonify({"error": "Repository URL required"}), 400

    scripts_dir = netmig_bp.SCRIPTS_DIR
    repo_name = os.path.splitext(
        os.path.basename(repo_url.rstrip("/"))
    )[0]
    target_dir = os.path.join(scripts_dir, repo_name)

    if os.path.exists(target_dir):
        logger.warning("Script already exists: %s", target_dir)
        return jsonify({"error": "Script already exists"}), 400

    try:
        logger.info("Cloning repository: %s", repo_url)
        subprocess.check_call(
            ["git", "clone", repo_url, target_dir]
        )
    except subprocess.CalledProcessError:
        logger.exception("Git clone failed for: %s", repo_url)
        return jsonify({"error": "Git clone failed"}), 500

    netmig_bp.load_scripts()
    logger.info("Scripts reloaded after clone")

    return jsonify({"status": "ok"})
