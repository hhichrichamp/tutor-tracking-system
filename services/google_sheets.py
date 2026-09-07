import gspread
import streamlit as st


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

from datetime import datetime

def read_classes_from_sheet():

    spreadsheet = get_google_sheet()

    worksheet = spreadsheet.worksheet("Classes")

    records = worksheet.get_all_records()

    for record in records:

        if isinstance(record.get("start"), str):
            record["start"] = datetime.fromisoformat(record["start"])

        if isinstance(record.get("end"), str):
            record["end"] = datetime.fromisoformat(record["end"])

    return records

