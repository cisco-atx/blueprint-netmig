"""NetMig Flask Blueprint module.

Provides dynamic script loading, validation, and route registration
for the NetMig system. Scripts are discovered from a user directory,
validated, registered with a runner service, and exposed via API
routes dynamically.

File path: blueprint.py
"""

import importlib.util
import logging
import os
import sys

from flask import Blueprint, request, abort, session, current_app
from sqlitedict import SqliteDict

from . import routes, services

logger = logging.getLogger(__name__)


class NetMig(Blueprint):
    """Custom Flask Blueprint for NetMig script management."""

    meta = {
        "name": "NetMig",
        "description": "Script Management and Execution.",
        "version": "1.0.0",
        "icon": "netmig.ico",
        "url_prefix": "/netmig",
    }

    def __init__(self, **kwargs):
        """Initialize NetMig blueprint with required setup."""
        super().__init__(
            "netmig",
            __name__,
            url_prefix="/netmig",
            template_folder="templates",
            static_folder="static",
            **kwargs,
        )

        self.routes = routes
        self.services = services

        self.setup_paths()
        self.setup_directories()
        self.setup_db()
        self.setup_runner()
        self.setup_routes()

    def setup_paths(self):
        """Set up directory paths for NetMig."""
        self.HOME_DIR = os.path.join(
            os.path.expanduser("~"), ".netmigweb"
        )
        self.SCRIPTS_DIR = os.path.join(self.HOME_DIR, "scripts")
        self.DB_DIR = os.path.join(self.HOME_DIR, "db")

    def setup_directories(self):
        """Ensure required directories exist."""
        for directory in [
            self.HOME_DIR,
            self.SCRIPTS_DIR,
            self.DB_DIR,
        ]:
            os.makedirs(directory, exist_ok=True)

    def setup_db(self):
        """Initialize SqliteDict database for scripts."""
        db_path = os.path.join(self.DB_DIR, "scripts.sqlite")
        self.scripts_db = SqliteDict(db_path, autocommit=True)

    def setup_runner(self):
        """Initialize the script runner service."""
        self.runner = self.services.Runner()

    def setup_routes(self):
        """Register base routes and load scripts."""
        for route in self.routes.routes:
            self.add_url_rule(**route)

        self.load_scripts()

    def load_scripts(self):
        """Load and register scripts from the scripts directory."""
        self.scripts = {}
        self.scripts_db.clear()

        for script_id in os.listdir(self.SCRIPTS_DIR):
            script_path = os.path.join(self.SCRIPTS_DIR, script_id)

            if not os.path.isdir(script_path):
                continue

            init_py = os.path.join(script_path, "__init__.py")
            if not os.path.exists(init_py):
                continue

            try:

                script_cls = self._load_script_class(
                    script_id, script_path
                )
                self._validate_script_class(script_cls)

                metadata = {
                    "id": script_id,
                    "path": script_path,
                    **script_cls.meta,
                }

                self.scripts[script_id] = metadata
                self.scripts_db[script_id] = metadata

                self.runner.register_script(script_id, script_cls)
                self._register_script_routes(script_id, script_cls)

            except Exception:
                logger.exception("Failed loading script: %s", script_id)

    def _validate_script_class(self, script_cls):
        """Validate structure of a script class."""
        if not isinstance(script_cls, type):
            raise ValueError("SCRIPT_CLASS must be a class")

        meta = getattr(script_cls, "meta", None)
        if not isinstance(meta, dict):
            raise ValueError("meta must be a dict")

        for key in ("name", "version", "description"):
            if key not in meta:
                raise ValueError(f"meta missing '{key}'")

        required_fn = getattr(script_cls, "required", None)
        if not callable(required_fn):
            raise ValueError("required() method is required")

        input_fn = getattr(script_cls, "input", None)
        if not callable(input_fn):
            raise ValueError("input() method is required")

        run_fn = getattr(script_cls, "run", None)
        if not callable(run_fn):
            raise ValueError("run() method is required")

        url_rules = getattr(script_cls, "url_rules", [])
        if not isinstance(url_rules, list):
            raise ValueError("URL_RULES must be a list")

        for rule in url_rules:
            if not isinstance(rule, dict):
                raise ValueError("Each URL_RULE must be a dict")

            for key in ("rule", "endpoint", "view_func"):
                if key not in rule:
                    raise ValueError(f"URL_RULE missing '{key}'")

    def _load_script_class(self, script_id, script_path):
        """Dynamically load script class from module."""
        init_py = os.path.join(script_path, "__init__.py")

        spec = importlib.util.spec_from_file_location(
            f"scripts.{script_id}",
            init_py,
            submodule_search_locations=[script_path],
        )

        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module

        spec.loader.exec_module(module)

        script_cls = getattr(module, "SCRIPT_CLASS", None)

        if not script_cls:
            raise ValueError(f"{script_id} missing SCRIPT_CLASS")

        return script_cls

    def _register_script_routes(self, script_id, script_cls):
        """Register dynamic routes for a script."""
        for rule in getattr(script_cls, "url_rules", []):
            endpoint = f"{script_id}_{rule['endpoint']}"

            if f"netmig.{endpoint}" in current_app.view_functions:
                continue

            self.add_url_rule(
                rule=f"/{script_id}{rule['rule']}",
                endpoint=endpoint,
                view_func=self._make_view(
                    script_id,
                    script_cls,
                    rule["view_func"],
                    rule.get("is_global", False),
                ),
                methods=rule.get("methods", ["GET"]),
            )

    def _make_view(
            self, script_id, script_cls, method_name, is_global
    ):
        """Create a Flask view function for a script method."""

        def view(**kwargs):
            """Handle incoming request for script execution."""
            if is_global:
                context = self._get_script_context(script_id)
                script_instance = script_cls(context)
            else:
                data = request.get_json(silent=True) or {}

                task_id = (
                        data.get("task_id")
                        or request.form.get("task_id")
                        or request.args.get("task_id")
                )

                if not task_id:
                    logger.error("Missing task_id in request")
                    abort(400, description="Missing task_id")

                task = self.runner.tasks.get(task_id)

                if not task:
                    logger.error("Invalid task_id: %s", task_id)
                    abort(404, description="Invalid task_id")

                script_instance = task["script"]

            return getattr(script_instance, method_name)(**kwargs)

        view.__name__ = f"{script_id}_{method_name}_view"
        return view

    def _get_script_context(self, script_id):
        """Create and return script execution context."""
        output_dir = os.path.join(
            session["userdata"].get("reports_dir"), script_id
        )
        os.makedirs(output_dir, exist_ok=True)

        return self.services.ScriptContext(output_dir, {})
