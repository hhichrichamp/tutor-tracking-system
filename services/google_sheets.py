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


def read_classes_from_sheet():

    spreadsheet = get_google_sheet()

    worksheets = spreadsheet.worksheets()


    worksheet = spreadsheet.worksheet("Classes")

    records = worksheet.get_all_records()

    return records