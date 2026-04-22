"""Script execution and streaming service.

This module provides functionality to register and execute user-defined
scripts with real-time output streaming. It includes a ScriptContext
for managing execution state and a Runner for handling script lifecycle
and task management.

File path: services.py
"""

import json
import logging
import os
import queue
import threading
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


class ScriptContext:
    """Context for a running script."""

    def __init__(self, output_dir, config=None):
        """Initialize ScriptContext."""
        self.output_dir = output_dir
        self.config = config or {}
        self.queue = queue.Queue()
        self.finished = False

    def _emit(self, type, message):
        """Emit an event to the queue."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        event = {
            "type": type,
            "message": message,
            "timestamp": timestamp,
        }
        self.queue.put(event)

    def log(self, message):
        """Log a standard output message."""
        self._emit("stdout", message)

    def error(self, message):
        """Log an error message."""
        self._emit("stderr", message)

    def set_progress(self, percent):
        """Set progress percentage."""
        self._emit("progress", percent)

    def set_html(self, element_id, html):
        """Emit HTML update event."""
        event = {
            "type": "html_update",
            "id": element_id,
            "message": html,
        }
        self.queue.put(event)

    def save_file(self, filename, content):
        """Save a file to the output directory."""
        path = os.path.join(self.output_dir, filename)
        try:
            with open(path, "wb") as file:
                file.write(content)
            self._emit("file", {"filename": filename, "path": path})
        except Exception:
            raise

    def finish(self):
        """Mark script execution as finished."""
        self.finished = True
        self._emit("done", None)


class Runner:
    """Manages script registration and execution."""

    def __init__(self):
        """Initialize Runner."""
        self.scripts = {}
        self.tasks = {}

    def register_script(self, script_id, script_cls):
        """Register a script with the runner."""
        self.scripts[script_id] = script_cls

    def create_task(self, script_id, inputs, config, output_dir):
        """Create a new execution task."""
        if script_id not in self.scripts:
            logger.error("Script ID not found: %s", script_id)
            raise ValueError(f"Script '{script_id}' is not registered")

        task_id = str(uuid.uuid4())
        context = ScriptContext(output_dir, config)

        self.tasks[task_id] = {
            "id": task_id,
            "status": "pending",
            "start_time": None,
            "end_time": None,
            "script": self.scripts[script_id](context),
            "thread": None,
            "inputs": inputs,
            "context": context,
        }

        return task_id

    def run(self, task_id):
        """Run a task in a separate thread."""
        thread = threading.Thread(
            target=lambda: self._run_task(task_id),
            daemon=True,
        )
        self.tasks[task_id]["thread"] = thread
        thread.start()

    def _run_task(self, task_id):
        """Execute the task logic."""
        task = self.tasks[task_id]
        task["status"] = "running"
        task["start_time"] = datetime.now()

        try:
            task["script"].run(task["inputs"])
            task["status"] = "completed"
        except Exception as exc:
            task["context"].error(str(exc))
            task["status"] = "failed"
        finally:
            task["context"].finish()
            task["end_time"] = datetime.now()

            # Schedule task cleanup after 10 minutes
            threading.Timer(
                600,
                lambda: self.tasks.pop(task_id, None),
            ).start()

    def stream_output(self, task_id):
        """Stream task output events."""
        task = self.tasks.get(task_id)
        if not task or not task["context"]:
            raise ValueError("Invalid task ID or context not initialized")

        ctx = task["context"]

        while not ctx.finished or not ctx.queue.empty():
            try:
                event = ctx.queue.get(timeout=1)
                yield f"data: {json.dumps(event)}\n\n"
            except queue.Empty:
                continue

        yield f"data: {json.dumps({'type': 'done'})}\n\n"
