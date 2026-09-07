import streamlit as st
import gspread


st.title("Google Sheets Connection Test")


try:

    # 1. Read credentials
    credentials = dict(st.secrets["gcp_service_account"])

    # 2. Authenticate
    gc = gspread.service_account_from_dict(credentials)

    st.success("✓ Google authentication successful")

    # 3. Open spreadsheet
    spreadsheet = gc.open("Tutor Tracking System")

    st.success("✓ Spreadsheet opened successfully")

    st.write("Spreadsheet:", spreadsheet.title)

    # 4. Open Classes worksheet
    worksheet = spreadsheet.worksheet("Classes")

    st.success("✓ Classes worksheet opened successfully")

    # 5. Read data
    records = worksheet.get_all_records()

    st.success(f"✓ Read {len(records)} class records")

    # 6. Display data
    st.dataframe(records)


except Exception as e:

    st.error("Google Sheets connection failed")

    st.exception(e)