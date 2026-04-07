import datetime
import logging
import os
import shutil
import subprocess
import bcrypt

from flask import current_app, render_template, url_for, jsonify, request, session


def render_manage_scripts():
    netmig_bp = current_app.blueprints["netmig"]

    kwargs = {
        "add_text": "Add Script",
        "columns": ["Name", "Version", "Description"],
        "dataset": [
            {
                "Id": script_id,
                "Name": script_data.get("name", "Unnamed Script"),
                "Version": script_data.get("version", "Unknown"),
                "Description": script_data.get("description", "No description available."),
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
    netmig_bp = current_app.blueprints["netmig"]
    payload = request.get_json()
    keys_to_delete = payload.get("keys", [])
    deleted = []

    for key in keys_to_delete:
        script_path = os.path.join(netmig_bp.SCRIPTS_DIR, key)
        if os.path.exists(script_path):
            try:
                shutil.rmtree(script_path)
                deleted.append(key)
            except Exception as e:
                return jsonify(error=str(e)), 500
        netmig_bp.load_scripts()
        deleted.append(key)
    return jsonify(deleted=deleted)


def upload_script():
    """
    Handles the upload of a new script as a zip file, extracts it to the scripts directory, and registers it.
    """
    netmig_bp = current_app.blueprints["netmig"]
    files = request.files.getlist("files")

    if not files:
        return jsonify({"error": "No files uploaded"}), 400

    scripts_dir = netmig_bp.SCRIPTS_DIR

    # Determine top-level directory name from first file
    first_file = files[0]
    root_dir = first_file.filename.split("/", 1)[0]
    target_dir = os.path.join(scripts_dir, root_dir)

    if os.path.exists(target_dir):
        return jsonify({"error": "Script already exists"}), 400

    os.makedirs(target_dir, exist_ok=True)

    for file in files:
        rel_path = file.filename
        full_path = os.path.join(scripts_dir, rel_path)

        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        file.save(full_path)

    # Re-scan scripts after upload
    netmig_bp.load_scripts()

    return jsonify({"status": "ok"})


def clone_script():
    """
    Clones a new script from a given Git repository URL, extracts it to the scripts directory, and registers it.
    """
    netmig_bp = current_app.blueprints["netmig"]
    data = request.get_json()
    repo_url = data.get("repo_url")

    if not repo_url:
        return jsonify({"error": "Repository URL required"}), 400

    scripts_dir = netmig_bp.SCRIPTS_DIR

    # Extract repo name
    repo_name = os.path.splitext(os.path.basename(repo_url.rstrip("/")))[0]
    target_dir = os.path.join(scripts_dir, repo_name)

    if os.path.exists(target_dir):
        return jsonify({"error": "Script already exists"}), 400

    try:
        subprocess.check_call(["git", "clone", repo_url, target_dir])
    except subprocess.CalledProcessError:
        return jsonify({"error": "Git clone failed"}), 500

    # Re-scan scripts after clone
    netmig_bp.load_scripts()

    return jsonify({"status": "ok"})
