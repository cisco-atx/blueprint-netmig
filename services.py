"""
Script Runner for executing user-defined scripts with real-time output streaming.

This module defines a Runner class that manages the registration and execution of user-defined scripts.
Each script is associated with an input function (for rendering input forms) and a run function (which contains the script's logic).
The Runner allows for creating tasks based on registered scripts, running them in separate threads, and streaming their output in real-time.

Class ScriptContext:
- Manages the context for a running script, including output directory, configuration, and a queue for emitting events (logs, progress updates, file saves).
- Provides methods for logging messages, reporting errors, updating progress, saving files, and signaling completion.

Class Runner:
- Manages registered scripts and their execution tasks.
- Allows for registering scripts with input and run functions.
- Provides methods for creating tasks, running them, and streaming their output.

"""

import os
import uuid
import json
import queue
import threading
from datetime import datetime

class ScriptContext:
    """
    Context for a running script, allowing it to emit logs, progress updates, and save files.

    Attributes:
        output_dir (str): Directory where the script can save output files.
        config (dict): Configuration parameters for the script.
        queue (queue.Queue): Queue for emitting events to be streamed back to the client.
        finished (bool): Flag indicating whether the script has finished execution.
    """
    def __init__(self, output_dir, config=None):
        self.output_dir = output_dir
        self.config = config or {}
        self.queue = queue.Queue()
        self.finished = False

    def _emit(self, type, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.queue.put({
            "type": type,
            "message": message,
            "timestamp": timestamp
        })

    def log(self, message):
        self._emit("stdout", message)

    def error(self, message):
        self._emit("stderr", message)

    def set_progress(self, percent):
        self._emit("progress", percent)

    def set_html(self, element_id, html):
        self.queue.put({
            "type": "html_update",
            "id": element_id,
            "message": html
        })

    def save_file(self, filename, content):
        path = os.path.join(self.output_dir, filename)
        with open(path, "wb") as f:
            f.write(content)
        self._emit("file", {"filename": filename, "path": path})

    def finish(self):
        self.finished = True
        self._emit("done", None)


class Runner:
    """
    Manages the registration and execution of user-defined scripts, allowing for real-time output streaming.

    Attributes:
        scripts (dict): A dictionary mapping script IDs to their corresponding classes.
        tasks (dict): A dictionary mapping task IDs to their execution details, including status, start time, end time, script instance, thread, inputs, and context.
    """
    def __init__(self):
        self.scripts = {}
        self.tasks = {}

    def register_script(self, script_id, script_cls):
        """
        Registers a new script with the runner, associating it with a unique ID and its corresponding class.
        Args:
            script_id: A unique identifier for the script.
            script_cls: The class that implements the script's logic, which should have a constructor accepting a ScriptContext and a run method.
        """
        self.scripts[script_id] = script_cls

    def create_task(self, script_id, inputs, config, output_dir):
        """
        Creates a new task for the specified script with given inputs and configuration.
        Args:
            script_id: The ID of the registered script to run.
            inputs: A dictionary of input values for the script.
            config: A dictionary of configuration parameters for the script.
            output_dir: Directory where the script can save output files.

        Returns:
            A unique task ID that can be used to track the execution and stream output.
        """
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
        """
        Runs the specified task in a separate thread, allowing for real-time output streaming.
        Args:
            task_id: The ID of the task to run.
        """
        thread = threading.Thread(target=lambda: self._run_task(task_id), daemon=True)
        self.tasks[task_id]["thread"] = thread
        thread.start()

    def _run_task(self, task_id):
        task = self.tasks[task_id]
        task["status"] = "running"
        task["start_time"] = datetime.now()

        try:
            task["script"].run(task["inputs"])
            task["status"] = "completed"
        except Exception as e:
            task["context"].error(str(e))
            task["status"] = "failed"
        finally:
            task["context"].finish()
            task["end_time"] = datetime.now()

            threading.Timer(600, lambda: self.tasks.pop(task_id, None)).start()

    def stream_output(self, task_id):
        """
        Generator function that yields output events for the specified task in real-time.
        """
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