import importlib.util
import logging
import os
import sys

from flask import Blueprint, request, abort, session, current_app
from sqlitedict import SqliteDict

from . import routes, services

class NetMig(Blueprint):
    meta = {
        "name": "NetMig",
        "description": "Script Management and Execution.",
        "version": "1.0.0",
        "icon": "netmig.ico",
        "url_prefix": "/netmig"
    }

    def __init__(self, **kwargs):
        super().__init__(
            "netmig",
            __name__,
            url_prefix="/netmig",
            template_folder="templates",
            static_folder="static",
            **kwargs
        )

        self.routes = routes
        self.services = services
        self.setup_paths()
        self.setup_directories()
        self.setup_db()
        self.setup_runner()
        self.setup_routes()

    def setup_paths(self):
        """ Sets up the directory paths for the NetMig blueprint, allowing for customization through keyword arguments or defaulting to a standard structure within the user's home directory. """
        self.HOME_DIR = os.path.join(os.path.expanduser("~"), ".netmigweb")
        self.SCRIPTS_DIR = os.path.join(self.HOME_DIR, "scripts")
        self.DB_DIR = os.path.join(self.HOME_DIR, "db")

    def setup_directories(self):
        """ Ensures that all necessary directories for the NetMig blueprint exist, creating them if they do not. """
        for d in [
            self.HOME_DIR,
            self.SCRIPTS_DIR,
            self.DB_DIR
        ]:
            os.makedirs(d, exist_ok=True)

    def setup_db(self):
        """ Initializes the databases for scripts using SqliteDict, storing it in the designated database directory for the NetMig blueprint. """
        self.scripts_db = SqliteDict(os.path.join(self.DB_DIR, "scripts.sqlite"), autocommit=True)

    def setup_runner(self):
        """ Initializes the Runner service for the NetMig blueprint, allowing for the management and execution of scripts defined within the blueprint's functionality. """
        self.runner = self.services.Runner()

    def setup_routes(self):
        """ Registers the routes defined in the NetMig blueprint's routes module, allowing the blueprint to handle incoming requests according to the specified endpoints and methods. """
        for route in self.routes.routes:
            self.add_url_rule(**route)
        self.load_scripts()

    def load_scripts(self):
        """Scans the scripts directory for valid script modules, loads their classes, validates their structure, and registers them with the Runner service and as Flask routes based on their defined URL rules."""
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
                script_cls = self._load_script_class(script_id, script_path)

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
                logging.exception(f"Failed loading {script_id}")

    def _validate_script_class(self, script_cls):
        # Must be a class
        if not isinstance(script_cls, type):
            raise ValueError("SCRIPT_CLASS must be a class")

        # ---- meta ----
        meta = getattr(script_cls, "meta", None)
        if not isinstance(meta, dict):
            raise ValueError("meta must be a dict")

        for key in ("name", "version", "description"):
            if key not in meta:
                raise ValueError(f"meta missing '{key}'")

        # ---- input() ----
        input_fn = getattr(script_cls, "input", None)
        if not callable(input_fn):
            raise ValueError("input() method is required")

        # ---- run() ----
        run_fn = getattr(script_cls, "run", None)
        if not callable(run_fn):
            raise ValueError("run() method is required")

        # ---- url_rules (optional) ----
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
                    rule.get("is_global", False)
                ),
                methods=rule.get("methods", ["GET"]),
            )

    def _make_view(self, script_id, script_cls, method_name, is_global):
        def view(**kwargs):
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
                    abort(400, description="Missing task_id")

                task = self.runner.tasks.get(task_id)

                if not task:
                    abort(404, description="Invalid task_id")

                script_instance = task["script"]

            return getattr(script_instance, method_name)(**kwargs)

        view.__name__ = f"{script_id}_{method_name}_view"
        return view

    def _get_script_context(self, script_id):
        output_dir = os.path.join(session["userdata"].get("reports_dir"), script_id)
        os.makedirs(output_dir, exist_ok=True)

        return self.services.ScriptContext(output_dir, {})