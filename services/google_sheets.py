import gspread
import streamlit as st
from datetime import datetime, date


def get_google_sheet():

    credentials = dict(st.secrets["gcp_service_account"])

    gc = gspread.service_account_from_dict(credentials)

    try:
        spreadsheet = gc.open_by_key(
            "1VrbV0NHmP5e2nfscIqhNHTP9cONmBwf3v9rCMNndlkY"
        )

        return spreadsheet

    except Exception as e:
        st.error(f"Could not open spreadsheet: {e}")
        raise



def read_classes_from_sheet():
    spreadsheet = get_google_sheet()

    worksheet = spreadsheet.worksheet("Classes")
    records = worksheet.get_all_records()

    classes = []

    for record in records:

        class_date = datetime.strptime(
            str(record["date"]),
            "%Y-%m-%d"
        ).date()

        start_time = datetime.strptime(
            str(record["start"]),
            "%H:%M"
        ).time()

        end_time = datetime.strptime(
            str(record["end"]),
            "%H:%M"
        ).time()

        class_record = {
            "id": record["id"],
            "course": record["course"],
            "title": record["title"],
            "date": class_date,
            "start": datetime.combine(
                class_date,
                start_time
            ),
            "end": datetime.combine(
                class_date,
                end_time
            ),
            "room": record["room"],
            "max_tutors": int(record["max_tutors"]),
            "status": record["status"],
            "qr_token": record["qr_token"]
        }

        classes.append(class_record)

    return classes


def add_class_to_sheet(class_data):
    spreadsheet = get_google_sheet()
    worksheet = spreadsheet.worksheet("Classes")

    row = [
        class_data["id"],
        class_data["course"],
        class_data["title"],
        class_data["date"].strftime("%Y-%m-%d"),
        class_data["start"].strftime("%H:%M"),
        class_data["end"].strftime("%H:%M"),
        class_data["room"],
        class_data["max_tutors"],
        class_data["status"],
        class_data["qr_token"]
    ]

    worksheet.append_row(row , value_input_option="RAW")





# ── Class Signups ──────────────────────────────────────────────
def read_class_signups_from_sheet():
    spreadsheet = get_google_sheet()
    ws = spreadsheet.worksheet("Class Signups")
    records = ws.get_all_records()
    signups = []
    for r in records:
        signups.append({
            "id": r["id"].strip(),
            "class_id": r["class_id"].strip(),
            "tutor_id": r["tutor_id"].strip(),  # ← Add .strip() here
            "signup_time": datetime.fromisoformat(r["signup_time"]),
        })
    return signups

def add_class_signup_to_sheet(signup_data):
    """Columns: signup_id | class_id | tutor_id | signup_time"""
    spreadsheet = get_google_sheet()
    ws = spreadsheet.worksheet("Class Signups")
    ws.append_row([
        signup_data["id"],                                    # add this field when you create signups
        signup_data["class_id"],
        signup_data["tutor_id"],
        signup_data["signup_time"].strftime("%Y-%m-%d %H:%M:%S")
    ],
        value_input_option="RAW")


# ── Sessions ───────────────────────────────────────────────────

def read_sessions_from_sheet():
    spreadsheet = get_google_sheet()
    ws = spreadsheet.worksheet("Sessions")
    records = ws.get_all_records()
    sessions = []
    for r in records:
        sessions.append({
            "id": r["id"].strip(),
            "type": r["type"].strip(),
            "tutor_id": r["tutor_id"].strip(),  # ← Add .strip() here
            "student_ids": [s.strip() for s in str(r["student_ids"]).split(",") if s.strip()],
            "title": r["title"].strip(),
            "date": date.fromisoformat(r["date"]),
            "scheduled_start": datetime.fromisoformat(r["scheduled_start"]),
            "scheduled_end": datetime.fromisoformat(r["scheduled_end"]),
            "actual_start": datetime.fromisoformat(r["actual_start"]) if r["actual_start"] else None,
            "actual_end": datetime.fromisoformat(r["actual_end"]) if r["actual_end"] else None,
            "status": r["status"].strip(),
            "qr_token": r["qr_token"].strip() if r["qr_token"] else None,
        })
    return sessions

def add_session_to_sheet(session_data):
    """Columns: id | type | tutor_id | student_ids | title |
                date | scheduled_start | scheduled_end |
                actual_start | actual_end | status | qr_token"""
    spreadsheet = get_google_sheet()
    ws = spreadsheet.worksheet("Sessions")
    ws.append_row([
        session_data["id"],
        session_data["type"],
        session_data["tutor_id"],
        ",".join(str(s) for s in session_data["student_ids"]),
        session_data["title"],
        str(session_data["date"]),
        session_data["scheduled_start"].strftime("%Y-%m-%d %H:%M:%S"),
        session_data["scheduled_end"].strftime("%Y-%m-%d %H:%M:%S"),
        session_data["actual_start"].strftime("%Y-%m-%d %H:%M:%S") if session_data["actual_start"] else "",
        session_data["actual_end"].strftime("%Y-%m-%d %H:%M:%S") if session_data["actual_end"] else "",
        session_data["status"],
        session_data["qr_token"] or ""
    ],
        value_input_option="RAW")

def update_session_in_sheet(session_id, updated_fields: dict):
    """Patch specific columns of an existing session row by its ID."""
    spreadsheet = get_google_sheet()
    ws = spreadsheet.worksheet("Sessions")
    records = ws.get_all_records()
    col_map = {
        "status": 11, "actual_start": 9,
        "actual_end": 10, "qr_token": 12,
    }
    for i, row in enumerate(records, start=2):   # row 1 = header
        if str(row["id"]) == str(session_id):
            for field, value in updated_fields.items():
                if field in col_map:
                    if hasattr(value, "strftime"):
                        value = value.strftime("%Y-%m-%d %H:%M:%S")
                    ws.update_cell(i, col_map[field], value or "")
            break


# ── Attendance ─────────────────────────────────────────────────
def read_attendance_from_sheet():
    spreadsheet = get_google_sheet()
    ws = spreadsheet.worksheet("Attendance")
    records = ws.get_all_records()
    attendance = []
    for r in records:
        attendance.append({
            "id": r["id"].strip(),
            "type": r["type"].strip(),
            "session_id": r["session_id"].strip() if r["session_id"] else None,
            "class_id": r["class_id"].strip() if r["class_id"] else None,
            "student_id": str(r["student_id"]).strip() if r["student_id"] else None,
            "tutor_id": r["tutor_id"].strip() if r["tutor_id"] else None,
            "check_in": datetime.fromisoformat(r["check_in"]) if r["check_in"] else None,
            "check_out": datetime.fromisoformat(r["check_out"]) if r["check_out"] else None,
            "status": r["status"].strip(),
        })
    return attendance

def add_attendance_to_sheet(attendance_data):
    """Columns: id | type | session_id | class_id |
                student_id | tutor_id | check_in | check_out | status"""
    spreadsheet = get_google_sheet()
    ws = spreadsheet.worksheet("Attendance")
    ws.append_row([
        attendance_data["id"],
        attendance_data["type"],
        attendance_data["session_id"] or "",
        attendance_data["class_id"] or "",
        attendance_data["student_id"] or "",
        attendance_data["tutor_id"] or "",
        attendance_data["check_in"].strftime("%Y-%m-%d %H:%M:%S") if attendance_data["check_in"] else "",
        attendance_data["check_out"].strftime("%Y-%m-%d %H:%M:%S") if attendance_data["check_out"] else "",
        attendance_data["status"]
    ],
        value_input_option="RAW")

def update_attendance_checkout_in_sheet(att_id, check_out):
    """Write check_out time to an existing attendance row."""
    spreadsheet = get_google_sheet()
    ws = spreadsheet.worksheet("Attendance")
    records = ws.get_all_records()
    for i, row in enumerate(records, start=2):
        if str(row["id"]) == str(att_id):
            ws.update_cell(i, 8, check_out.strftime("%Y-%m-%d %H:%M:%S"))
            break