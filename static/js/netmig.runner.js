/**
 * scripts.layout.js
    * Handles the layout and interactions for the script execution page, including:
    * - Console output streaming
    * - Outputs table management
    * - Run modal with Connector selection
    * - Script info modal with documentation
 */


document.addEventListener("DOMContentLoaded", () => {

    let scriptEventSource = null;
    let outputsTable = null;
    let currentTaskId = null;

    /* ---------- Console ---------- */

    function resetConsole() {
        const el = document.getElementById("consoleOutput");
        if (el) el.innerHTML = "";
    }

    function formatTimestamp(ts = null) {
        const d = ts ? new Date(ts) : new Date();
        return d.toLocaleString("en-GB", {
            day: "2-digit",
            month: "short",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit"
        });
    }

    function appendLine({ type = "stdout", message = "", ts = null }) {
        const consoleEl = document.getElementById("consoleOutput");
        if (!consoleEl) return;

        const line = document.createElement("div");
        line.className = `console-line ${type}`;

        if (type === "start") line.classList.add("start");
        if (type === "done") line.classList.add("done");
        if (type === "stderr") line.classList.add("stderr");

        line.innerHTML = `
            <span class="ts">${formatTimestamp(ts)}</span>
            <span class="msg">${message}</span>
        `;

        consoleEl.appendChild(line);
        consoleEl.scrollTop = consoleEl.scrollHeight;
    }

    /* ---------- Outputs Table ---------- */

    function loadOutputsTable() {
        if (!outputsTable) {
            outputsTable = $("#outputsTable").DataTable({
                ajax: {
                    url: `/api/reports/${scriptId}`,
                    dataSrc: ""
                },
                columns: [
                    { data: "filename" },
                    {
                        data: "filename",
                        render: data => `
                            <div class="action-cell">
                                <button class="btn-download-output icon-only-btn"
                                        data-filename="${data}"
                                        title="Download">
                                    <span class="material-icons button">download</span>
                                </button>
                                <button class="btn-delete-output icon-only-btn"
                                        data-filename="${data}"
                                        title="Delete">
                                    <span class="material-icons button">delete</span>
                                </button>
                            </div>
                        `,
                        orderable: false,
                        searchable: false
                    }
                ],
                responsive: true,
                scrollY: "74vh",
                scrollCollapse: true,
                paging: false,
                searching: false,
                info: false,
                language: {
                    emptyTable: "No outputs generated"
                }
            });
        } else {
            outputsTable.ajax.reload(null, false);
        }
    }


    /* ---------- Script Routes ---------- */
    async function callScriptRoute(endpoint, payload = {}, method = "GET") {

        const options = {
            method: method,
            headers: { "Content-Type": "application/json" }
        };

        if (method === "POST") {
            options.body = JSON.stringify({
                task_id: currentTaskId,
                ...payload
            });
        }

        const response = await fetch(`/netmig/${scriptId}/${endpoint}`, options);

        if (!response.ok) {
            throw new Error(`Route call failed: ${endpoint}`);
        }

        return response.json();
    }

    // Expose globally for script-specific JS
    window.callScriptRoute = callScriptRoute;


    /* ---------- Run Script ---------- */

    async function runScript(connectorConfig) {

        resetConsole();
        appendLine({ type: "start", message: "Starting script…" });

        try {
            /* Collect inputs */
            const form = document.getElementById("scriptInterfaceForm");
            const inputs = {};

            new FormData(form).forEach((value, key) => {
                if (inputs[key]) {
                    // Already exists → convert to array or append
                    if (!Array.isArray(inputs[key])) {
                        inputs[key] = [inputs[key]];
                    }
                    inputs[key].push(value);
                } else {
                    inputs[key] = value;
                }
            });

            const payload = {
                inputs,
                config: {
                    connector: connectorConfig
                }
            };

            const resp = await fetch(`/netmig/run/${scriptId}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            if (!resp.ok) throw new Error("Run failed");

            const { task_id } = await resp.json();

            currentTaskId = task_id;

            if (scriptEventSource) scriptEventSource.close();
            scriptEventSource = new EventSource(`/netmig/stream/${task_id}`);

            scriptEventSource.onmessage = (e) => {
                const event = JSON.parse(e.data);

                // Update an element's innerHTML if type === "html_update"
                if (event.type === "html_update") {
                    const el = document.getElementById(event.id);
                    if (el) el.innerHTML = event.message;
                    return;
                }

                if (event.type === "file") {
                    loadOutputsTable();
                    return;
                }

                if (event.type === "done") {
                    appendLine({ type: "done", message: "Script finished" });
                    loadOutputsTable();
                    scriptEventSource.close();
                    return;
                }

                appendLine(event);
            };

            scriptEventSource.onerror = () => {
                appendLine({
                    type: "stderr",
                    message: "Stream disconnected"
                });
                scriptEventSource.close();
            };

        } catch (err) {
            console.error(err);
            appendLine({
                type: "stderr",
                message: "Failed to start script"
            });
        }
    }

    /* ---------- Run Button ---------- */

    document.getElementById("runScriptBtn").addEventListener("click", () => {
        RunModal.open(({ config }) => {
            runScript(config);
        });
    });

    /* ---------- Tabs ---------- */

    document.querySelectorAll(".tabs .tab").forEach(tab => {
        tab.addEventListener("click", () => {
            const container = tab.closest("section");
            const tabName = tab.dataset.tab;

            container.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
            container.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));

            tab.classList.add("active");
            container.querySelector(`#${tabName}`).classList.add("active");

            if (tabName === "files") {
                loadOutputsTable();
            }
        });
    });

    // -------------------- Output Dock --------------------
    const outputDock = document.getElementById('output-dock');
    const outputToggleBtn = document.getElementById('output-dock-toggle');

    function openOutputDock() {
        outputDock.classList.add('open');
        outputToggleBtn.innerHTML =
            '<span class="material-icons">keyboard_arrow_right</span>Output';
    }

    function closeOutputDock() {
        outputDock.classList.remove('open');
        outputToggleBtn.innerHTML =
            '<span class="material-icons">keyboard_arrow_left</span>Output';
    }

    outputToggleBtn.addEventListener('click', () => {
        if (outputDock.classList.contains('open')) {
            closeOutputDock();
        } else {
            openOutputDock();
        }
    });

    document.getElementById("confirmRunModal")
    .addEventListener("click", () => {
        openOutputDock();
    });

    /* ---------- Download ---------- */

    $(document).on("click", ".btn-download-output", function () {
        const filename = $(this).data("filename");
        window.location.href =
            `/api/report/download/${scriptId}/${encodeURIComponent(filename)}`;
    });

    /* ---------- Delete ---------- */

    $(document).on("click", ".btn-delete-output", function () {
        const filename = $(this).data("filename");

        if (!confirm(`Delete ${filename}?`)) return;

        fetch(`/api/report/${scriptId}/${encodeURIComponent(filename)}`, {
            method: "DELETE"
        })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    loadOutputsTable();
                } else {
                    alert(data.message || "Delete failed");
                }
            })
            .catch(() => alert("Delete failed"));
    });

    /* ---------- Script Info Modal ---------- */

    $(document).on("click", "#scriptInfoBtn", function () {
        const overlay = $("#scriptInfoModal");
        const content = $("#scriptInfoContent");

        overlay.css("display", "flex");
        content.html("Loading documentation…");

        fetch(`/netmig/info/${scriptId}`)
            .then(res => res.json())
            .then(data => {
                content.html(
                    data.readme
                        ? marked.parse(data.readme)
                        : "<p>No documentation available.</p>"
                );
            })
            .catch(() => {
                content.html("<p style='color:red;'>Failed to load documentation.</p>");
            });
    });

    $("#closeScriptInfoModalBtn").on("click", function () {
        $("#scriptInfoModal").css("display", "none");
    });

    /* ---------- Initial preload ---------- */

    loadOutputsTable();

});
