from .runner import (
    render,
    render_script,
    scan_scripts,
    run_script,
    stream_script_output,
    download_script_output,
    get_script_info
)

from .manage import (
    render_manage_scripts,
    delete_scripts,
    upload_script,
    clone_script
)

from flask import redirect, url_for, current_app

routes = [
    {
        "rule": "/",
        "endpoint": "redirect_root",
        "view_func": lambda: redirect(url_for("netmig.render")),
        "methods": ["GET"]
    },
    {
        "rule": "/runner",
        "endpoint": "render",
        "view_func": current_app.routes.login_required(render),
        "methods": ["GET"]
    },
    {
        "rule": "/<script_id>",
        "endpoint": "render_script",
        "view_func": current_app.routes.login_required(render_script),
        "methods": ["GET"]
    },
    {
        "rule": "/scan",
        "endpoint": "scan_scripts",
        "view_func": current_app.routes.login_required(scan_scripts),
        "methods": ["GET"]
    },
    {
        "rule": "/run/<script_id>",
        "endpoint": "run_script",
        "view_func": current_app.routes.login_required(run_script),
        "methods": ["POST"]
    },
    {
        "rule": "/stream/<task_id>",
        "endpoint": "stream_script_output",
        "view_func": current_app.routes.login_required(stream_script_output),
        "methods": ["GET"]
    },
    {
        "rule": "/download/<script_id>",
        "endpoint": "download_script_output",
        "view_func": current_app.routes.login_required(download_script_output),
        "methods": ["GET"]
    },
    {
        "rule": "/info/<script_id>",
        "endpoint": "get_script_info",
        "view_func": current_app.routes.login_required(get_script_info),
        "methods": ["GET"]
    },
    {
        "rule": "/manage",
        "endpoint": "manage_scripts",
        "view_func": current_app.routes.admin_required(render_manage_scripts),
        "methods": ["GET"]
    },
    {
        "rule": "/manage",
        "endpoint": "delete_scripts",
        "view_func": current_app.routes.admin_required(delete_scripts),
        "methods": ["DELETE"]
    },
    {
        "rule": "/manage/upload",
        "endpoint": "upload_script",
        "view_func": current_app.routes.admin_required(upload_script),
        "methods": ["POST"]
    },
    {
        "rule": "/manage/clone",
        "endpoint": "clone_script",
        "view_func": current_app.routes.admin_required(clone_script),
        "methods": ["POST"]
    }
]
