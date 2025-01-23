import streamlit as st
import pandas as pd
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def authenticate_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credits.json", scope)
    client = gspread.authorize(creds)
    return client

def extract_sheet_id(sheet_url):
    # 假設使用者輸入的是完整的 Google Sheets URL
    try:
        return sheet_url.split("/d/")[1].split("/")[0]
    except IndexError:
        st.error("無效的試算表連結，請檢查 URL 格式。")
        return None
    
sheet_url = st.text_input("請輸入 Google Sheet 連結")

def fetch(sheet_url):
    if sheet_url:
        sheet_id = extract_sheet_id(sheet_url)
        if sheet_id:
            client = authenticate_google_sheets()
            try:
                sheet = client.open_by_key(sheet_id)
                worksheet = sheet.sheet1
                data = worksheet.get_all_records()

                st.write(data)
            except:
                st.write("Connection Failed")

def insert(sheet_url, row: list):
    if sheet_url:
        sheet_id = extract_sheet_id(sheet_url)
        if sheet_id:
            client = authenticate_google_sheets()
            try:
                sheet = client.open_by_key(sheet_id)
                worksheet = sheet.sheet1
                worksheet.append_row(row)

                records = worksheet.get_all_records()
                st.write("Updated successfully:")
                
            except Exception as e:
                st.write(f"Connection Failed: {e}")

insert(sheet_url, ["id", "title", "summary"])
time.sleep(5)
fetch(sheet_url)