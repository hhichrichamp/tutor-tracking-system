import gspread
import streamlit as st


# def get_google_sheet():
#     """
#     Connect to the Google Spreadsheet.
#     """

#     credentials = dict(st.secrets["gcp_service_account"])

#     gc = gspread.service_account_from_dict(credentials)

#     spreadsheet = gc.open("Tutor Tracking System")

#     return spreadsheet


def get_google_sheet():

    credentials = dict(st.secrets["gcp_service_account"])

    gc = gspread.service_account_from_dict(credentials)

    try:
        # spreadsheet = gc.open("Tutor Tracking System")
        spreadsheet = gc.open_by_key("6996a757d5b6197daacb56254dc410c3e8c87873")

    except Exception as e:
        st.error(f"Could not open spreadsheet: {e}")
        raise

def read_classes_from_sheet():
    spreadsheet = get_google_sheet()

    worksheet = spreadsheet.worksheet("Classes")

    records = worksheet.get_all_records()

    return records