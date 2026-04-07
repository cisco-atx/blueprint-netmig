$(document).ready(function () {

    // Initialize the DataTable with specified configuration and filters
    const table = $('#manageDatatable').DataTable({
        stateSave: true,
        orderCellsTop: true,
        fixedHeader: true,
        paging: true,
        searching: true,
        info: true,
        autoWidth: true,
        columnDefs: [{ width: '30px', targets: 0 }],
        initComplete: function () {
            const api = this.api();

            // Lock column widths to prevent layout shifts
            api.columns().every(function () {
                const th = $(this.header());
                th.css('width', th.width() + 'px');
            });

            // Bind filter inputs to their respective columns
            $('#manageDatatable thead tr:eq(1) th input.col-filter').each(function () {
                const colIndex = $(this).data('col') + 1;
                $(this).on('keyup change clear', function () {
                    if (table.column(colIndex).search() !== this.value) {
                        table.column(colIndex).search(this.value).draw();
                    }
                });
            });
        }
    });

    // Reference to bulk delete button and "select all" checkbox
    const deleteSelectedBtn = $("#deleteSelectedBtn")[0];
    const selectAll = $("#selectAll")[0];

    /**
     * Toggles the visibility of the bulk delete button based on the number of checked rows.
     */
    function toggleDeleteBtn() {
        const checkedCount = $(".row-check:checked").length;
        deleteSelectedBtn.style.display = checkedCount > 0 ? "inline-flex" : "none";
    }

    // Monitor changes to individual row checkboxes and adjust the bulk delete button
    $(document).on("change", ".row-check", toggleDeleteBtn);

    // Handle "select all" functionality, checking/unchecking all rows
    selectAll.addEventListener("change", () => {
        $(".row-check").prop('checked', selectAll.checked);
        toggleDeleteBtn();
    });

    // Manages the delete modal visibility and items to delete
    let itemsToDelete = [];

    /**
     * Opens the delete confirmation modal and sets the items to delete.
     * @param {Array} items - List of item IDs to delete.
     */
     let rowsToDelete = [];

     function openDeleteModal(items, rows = []) {
         itemsToDelete = items;
         rowsToDelete = rows;
         $("#deleteConfirmModal").css("display", "flex");
     }

    /**
     * Normalizes a string by trimming whitespace and converting to lowercase.
     * @param {string} str - The string to normalize.
     * @returns {string} The normalized string.
     */
     function normalizeKey(str) {
         return str.replace(/\s+/g, ' ').trim().toLowerCase();
     }

     function itemExists(key) {
         const normalized = normalizeKey(key);

         return $('#manageDatatable tbody tr').toArray().some(row => {
             const cellText = $(row).find('td:eq(1)').text();
             return normalizeKey(cellText) === normalized;
         });
     }

     window.itemExists = itemExists;

    /**
     * Closes the delete confirmation modal.
     */
    function closeDeleteModal() {
        $("#deleteConfirmModal").css("display", "none");
    }

    // Close modal buttons
    $("#cancelDeleteBtn, #closeDeleteModalBtn").on("click", closeDeleteModal);

    // Handle bulk delete button action
    $('#deleteSelectedBtn').on('click', function () {
        const rows = [];
        const ids = [];

        $('.row-check:checked').each(function () {
            const tr = $(this).closest('tr')[0]; // DOM node
            rows.push(tr);
            ids.push(this.dataset.id);
        });

        if (ids.length) {
            openDeleteModal(ids, rows);
        }
    });

    // Handle individual row delete button action
    $(document).on("click", ".delete-btn", function () {
        const tr = $(this).closest("tr")[0];
        const id = tr.querySelector(".row-check").dataset.id;

        openDeleteModal([id], [tr]);
    });

    /**
     * Confirms the deletion of the selected items via an AJAX request.
     */
    $('#confirmDeleteBtn').on('click', function () {
        if (!"scripts" || !itemsToDelete.length) return;

        $.ajax({
            url: '/netmig/manage',
            method: 'DELETE',
            contentType: 'application/json',
            data: JSON.stringify({ keys: itemsToDelete }),
            success: function () {
                window.location.href = '/netmig/manage';
            },
            error: function () {
                alert("Delete operation failed.");
            }
        });
    });

    $('#openModalBtn').on('click', function () {
        $('#modalForm')[0].reset();
        $('#modalTitle').text('Add Script');
        $("#modalOverlay").css("display", "flex");
    });

    $('#cancelModalBtn, #closeModalBtn').on('click', function () {
        $("#modalOverlay").css("display", "none");
    });

    // Upload local directory
    $('#uploadFileBtn').on('click', function () {
        const dirInput = $('<input type="file" webkitdirectory directory multiple style="display:none;">');

        dirInput.on('change', function (event) {
            const files = event.target.files;
            if (!files.length) return;

            const rootDir = files[0].webkitRelativePath.split('/')[0];
            $('#scriptDir').val(rootDir);

            const formData = new FormData();
            for (let file of files) {
                formData.append('files', file);
            }

            $.ajax({
                url: '/netmig/manage/upload',
                method: 'POST',
                data: formData,
                processData: false,
                contentType: false,
                success: function () {
                    location.reload();
                },
                error: function (err) {
                    alert(err.responseJSON?.error || 'Upload failed');
                }
            });
        });

        dirInput.trigger('click');
    });

    // Clone git repo
    $('#cloneGitBtn').on('click', function () {
        const repoUrl = $('#scriptGit').val().trim();
        if (!repoUrl) {
            alert('Git repository URL is required');
            return;
        }

        $.ajax({
            url: '/netmig/manage/clone',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ repo_url: repoUrl }),
            success: function () {
                location.reload();
            },
            error: function (err) {
                alert(err.responseJSON?.error || 'Clone failed');
            }
        });
    });
});
