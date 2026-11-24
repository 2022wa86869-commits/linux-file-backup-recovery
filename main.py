
import streamlit as st
import hashlib
import zipfile
import io
from datetime import datetime

# ---------------- PAGE CONFIGURATION ----------------

st.set_page_config(
    page_title="Linux File Backup & Recovery Simulator",
    page_icon="💾",
    layout="wide"
)

# ---------------- SESSION STORAGE ----------------

if "backups" not in st.session_state:
    st.session_state.backups = []

if "activity" not in st.session_state:
    st.session_state.activity = []

if "files" not in st.session_state:
    st.session_state.files = {}

# ---------------- HELPER FUNCTIONS ----------------

def calculate_hash(data):
    return hashlib.sha256(data).hexdigest()


def log_activity(message):
    st.session_state.activity.insert(
        0,
        {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "message": message
        }
    )


def format_size(size):
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.2f} KB"
    return f"{size / (1024 * 1024):.2f} MB"


# ---------------- SIDEBAR ----------------

st.sidebar.title("💾 Backup Simulator")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "File Management",
        "Create Backup",
        "Backup History",
        "File Recovery",
        "Integrity Check",
        "Failure Simulation",
        "Activity Logs"
    ]
)

st.sidebar.markdown("---")
st.sidebar.info("Linux File Backup & Recovery Simulator")
st.sidebar.caption("Educational project - Version 1.0")

# ---------------- DASHBOARD ----------------

if page == "Dashboard":

    st.title("💾 Linux File Backup & Recovery Simulator")
    st.write("Monitor, manage and restore your backup files.")

    total_files = len(st.session_state.files)
    total_backups = len(st.session_state.backups)
    total_size = sum(
        len(item["data"])
        for item in st.session_state.files.values()
    )

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Files", total_files)
    col2.metric("Total Backups", total_backups)
    col3.metric("Storage Used", format_size(total_size))

    st.markdown("---")
    st.subheader("System Overview")

    col1, col2 = st.columns(2)

    with col1:
        st.success("Backup Simulator: Ready")
        st.info(f"Files Available: {total_files}")

    with col2:
        st.success("Recovery Module: Ready")
        st.info(f"Backup Records: {total_backups}")

    st.subheader("Recent Activities")

    if st.session_state.activity:
        for item in st.session_state.activity[:5]:
            st.write(f"🕒 {item['time']} — {item['message']}")
    else:
        st.write("No activities recorded yet.")

# ---------------- FILE MANAGEMENT ----------------

elif page == "File Management":

    st.title("📁 File Management")

    st.write("Upload files to the simulator.")

    uploaded_files = st.file_uploader(
        "Choose files",
        accept_multiple_files=True
    )

    if st.button("Add Files", type="primary"):

        if uploaded_files:
            count = 0

            for file in uploaded_files:
                st.session_state.files[file.name] = file.getvalue()
                count += 1

            log_activity(f"{count} file(s) uploaded successfully.")
            st.success(f"{count} file(s) added successfully!")
        else:
            st.warning("Please select at least one file.")

    st.markdown("---")
    st.subheader("Available Files")

    if st.session_state.files:

        for name, data in st.session_state.files.items():

            col1, col2, col3 = st.columns([3, 2, 1])

            col1.write(f"📄 {name}")
            col2.write(format_size(len(data)))

            if col3.button("Delete", key=f"delete_{name}"):

                del st.session_state.files[name]
                log_activity(f"File deleted: {name}")
                st.rerun()

    else:
        st.info("No files uploaded yet.")

# ---------------- CREATE BACKUP ----------------

elif page == "Create Backup":

    st.title("📦 Create Backup")

    st.write("Create full or incremental backups of uploaded files.")

    backup_type = st.selectbox(
        "Select Backup Type",
        ["Full Backup", "Incremental Backup"]
    )

    if st.button("Start Backup", type="primary"):

        if not st.session_state.files:
            st.warning("Upload files before creating a backup.")

        else:

            previous_files = {}

            if st.session_state.backups:
                previous_files = st.session_state.backups[-1]["files"]

            backup_files = {}

            if backup_type == "Full Backup":

                backup_files = dict(st.session_state.files)

            else:

                for name, data in st.session_state.files.items():

                    old_data = previous_files.get(name)

                    if old_data is None or calculate_hash(old_data) != calculate_hash(data):
                        backup_files[name] = data

            if not backup_files:
                st.info("No new or modified files found. Incremental backup not required.")

            else:

                backup = {
                    "id": len(st.session_state.backups) + 1,
                    "type": backup_type,
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "files": dict(backup_files),
                    "hashes": {
                        name: calculate_hash(data)
                        for name, data in backup_files.items()
                    }
                }

                st.session_state.backups.append(backup)

                log_activity(
                    f"{backup_type} completed with {len(backup_files)} file(s)."
                )

                st.success("Backup completed successfully!")

                st.metric("Files Backed Up", len(backup_files))

                st.metric(
                    "Backup Size",
                    format_size(sum(len(x) for x in backup_files.values()))
                )

                st.write("Backed-up files:")

                for name in backup_files:
                    st.write(f"✅ {name}")

# ---------------- BACKUP HISTORY ----------------

elif page == "Backup History":

    st.title("📜 Backup History")

    if st.session_state.backups:

        for backup in reversed(st.session_state.backups):

            with st.expander(
                f"Backup #{backup['id']} - {backup['type']} - {backup['time']}"
            ):

                st.write(f"Files: {len(backup['files'])}")

                for name, data in backup["files"].items():
                    st.write(
                        f"📄 {name} — {format_size(len(data))}"
                    )

                buffer = io.BytesIO()

                with zipfile.ZipFile(
                    buffer, "w", zipfile.ZIP_DEFLATED
                ) as zip_file:

                    for name, data in backup["files"].items():
                        zip_file.writestr(name, data)

                st.download_button(
                    "Download Backup ZIP",
                    data=buffer.getvalue(),
                    file_name=f"backup_{backup['id']}.zip",
                    mime="application/zip",
                    key=f"download_{backup['id']}"
                )

    else:
        st.info("No backups have been created yet.")

# ---------------- FILE RECOVERY ----------------

elif page == "File Recovery":

    st.title("♻️ File Recovery")

    st.write("Restore files from an available backup.")

    if st.session_state.backups:

        backup_options = {
            f"Backup #{b['id']} - {b['type']} - {b['time']}": b
            for b in st.session_state.backups
        }

        selected = st.selectbox(
            "Select Backup",
            list(backup_options.keys())
        )

        backup = backup_options[selected]

        available_files = list(backup["files"].keys())

        if available_files:

            selected_file = st.selectbox(
                "Select File to Restore",
                available_files
            )

            if st.button("Restore File", type="primary"):

                restored_data = backup["files"][selected_file]

                st.session_state.files[selected_file] = restored_data

                log_activity(f"File restored: {selected_file}")

                st.success(f"{selected_file} restored successfully!")

                st.download_button(
                    "Download Restored File",
                    data=restored_data,
                    file_name=selected_file,
                    key="restored_download"
                )

        else:
            st.info("This backup contains no files.")

    else:
        st.warning("Create a backup before attempting recovery.")

# ---------------- INTEGRITY CHECK ----------------

elif page == "Integrity Check":

    st.title("🔐 File Integrity Verification")

    st.write(
        "Verify file integrity using SHA-256 cryptographic hashes."
    )

    if st.session_state.backups:

        backup_options = {
            f"Backup #{b['id']}": b
            for b in st.session_state.backups
        }

        selected = st.selectbox(
            "Choose Backup",
            list(backup_options.keys())
        )

        backup = backup_options[selected]

        if st.button("Verify Integrity", type="primary"):

            passed = 0
            failed = 0

            for name, data in backup["files"].items():

                current_hash = calculate_hash(data)
                original_hash = backup["hashes"][name]

                if current_hash == original_hash:
                    st.success(f"✅ {name}: Integrity Verified")
                    passed += 1
                else:
                    st.error(f"❌ {name}: Integrity Failed")
                    failed += 1

            st.metric("Files Passed", passed)
            st.metric("Files Failed", failed)

            if failed == 0:
                st.success("All checked files passed integrity verification.")

            log_activity("SHA-256 integrity verification performed.")

    else:
        st.info("Create a backup to perform integrity verification.")

# ---------------- FAILURE SIMULATION ----------------

elif page == "Failure Simulation":

    st.title("⚠️ Backup Failure Simulation")

    st.write(
        "Demonstrate what happens when a backup operation fails."
    )

    st.warning(
        "This is a simulated failure. It does not damage your uploaded files."
    )

    if st.button("Simulate Backup Failure", type="primary"):

        if st.session_state.files:

            log_activity("Simulated backup failure.")

            st.error("Backup operation failed!")

            st.write("Possible reasons:")

            st.write("- Insufficient storage space")
            st.write("- Network interruption")
            st.write("- Permission denied")
            st.write("- Unexpected system error")

            st.info(
                "Original uploaded files remain unchanged."
            )

        else:
            st.warning("Upload some files before running the simulation.")

# ---------------- ACTIVITY LOGS ----------------

elif page == "Activity Logs":

    st.title("📋 Activity Logs")

    if st.session_state.activity:

        for item in st.session_state.activity:

            st.write(f"🕒 {item['time']}")
            st.write(item["message"])
            st.markdown("---")

        if st.button("Clear Activity Logs"):

            st.session_state.activity = []
            st.success("Activity logs cleared.")
            st.rerun()

    else:
        st.info("No activity logs available.")

# ---------------- FOOTER ----------------

st.sidebar.markdown("---")
st.sidebar.caption("Linux File Backup & Recovery Simulator")
st.sidebar.caption("Developed using Python and Streamlit")
