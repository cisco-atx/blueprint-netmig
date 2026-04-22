"""Route definitions for the application.

This module defines all route mappings for the Flask application,
including runner and management endpoints. It applies authentication
and authorization decorators where required and organizes route
configuration in a centralized structure.

File path: routes/__init__.py
"""

from flask import current_app, redirect, url_for

# Local application imports
from .manage import (
    clone_script,
    delete_scripts,
    render_manage_scripts,
    upload_script,
)
from .runner import (
    download_script_output,
    get_script_info,
    render,
    render_script,
    run_script,
    scan_scripts,
    stream_script_output,
)


def redirect_root():
    """Redirect root URL to the main render endpoint."""
    return redirect(url_for("netmig.render"))


routes = [
    {
        "rule": "/",
        "endpoint": "redirect_root",
        "view_func": redirect_root,
        "methods": ["GET"],
    },
    {
        "rule": "/runner",
        "endpoint": "render",
        "view_func": current_app.routes.login_required(render),
        "methods": ["GET"],
    },
    {
        "rule": "/<script_id>",
        "endpoint": "render_script",
        "view_func": current_app.routes.login_required(render_script),
        "methods": ["GET"],
    },
    {
        "rule": "/scan",
        "endpoint": "scan_scripts",
        "view_func": current_app.routes.login_required(scan_scripts),
        "methods": ["GET"],
    },
    {
        "rule": "/run/<script_id>",
        "endpoint": "run_script",
        "view_func": current_app.routes.login_required(run_script),
        "methods": ["POST"],
    },
    {
        "rule": "/stream/<task_id>",
        "endpoint": "stream_script_output",
        "view_func": current_app.routes.login_required(
            stream_script_output
        ),
        "methods": ["GET"],
    },
    {
        "rule": "/download/<script_id>",
        "endpoint": "download_script_output",
        "view_func": current_app.routes.login_required(
            download_script_output
        ),
        "methods": ["GET"],
    },
    {
        "rule": "/info/<script_id>",
        "endpoint": "get_script_info",
        "view_func": current_app.routes.login_required(get_script_info),
        "methods": ["GET"],
    },
    {
        "rule": "/manage",
        "endpoint": "manage_scripts",
        "view_func": current_app.routes.admin_required(
            render_manage_scripts
        ),
        "methods": ["GET"],
    },
    {
        "rule": "/manage",
        "endpoint": "delete_scripts",
        "view_func": current_app.routes.admin_required(delete_scripts),
        "methods": ["DELETE"],
    },
    {
        "rule": "/manage/upload",
        "endpoint": "upload_script",
        "view_func": current_app.routes.admin_required(upload_script),
        "methods": ["POST"],
    },
    {
        "rule": "/manage/clone",
        "endpoint": "clone_script",
        "view_func": current_app.routes.admin_required(clone_script),
        "methods": ["POST"],
    },
]
