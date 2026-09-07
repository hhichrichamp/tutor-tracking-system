import gspread
import streamlit as st
from datetime import datetime


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

    worksheet.append_row(row)