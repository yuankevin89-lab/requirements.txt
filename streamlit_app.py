import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime

# --- 1. 連線到 Google Sheets 的函式 ---
def connect_to_sheets():
    try:
        # 從 Streamlit 雲端後台的 Secrets 讀取金鑰
        creds_dict = st.secrets["google_sheets"]
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # 【重要】請確保這裡的名稱與你的 Google 試算表檔名完全一致
        # 如果你的試算表叫「客服資料」，請改成 client.open("客服資料")
        sheet = client.open("你的試算表名稱").sheet1 
        return sheet
    except Exception as e:
        st.error(f"連線 Google Sheets 失敗: {e}")
        return None

# --- 2. 網頁介面設計 ---
st.set_page_config(page_title="雲端客服登記系統", page_icon="☁️")
st.title("☁️ 雲端客服案件登記系統")

# 建立輸入表單
with st.form("service_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        date = st.date_input("日期", datetime.now())
        name = st.text_input("客戶姓名")
        car_id = st.text_input("車號")
    with col2:
        time = st.time_input("時間", datetime.now())
        phone = st.text_input("聯絡電話")
        location = st.selectbox("場別", ["台北總站", "台中分站", "高雄辦事處", "其他"])

    description = st.text_area("內容描述")
    staff = st.text_input("記錄人")

    submit_button = st.form_submit_button("確認提交並同步雲端")

# --- 3. 按下按鈕後的處理邏輯 ---
if submit_button:
    if not name or not description:
        st.error("請填寫『姓名』與『內容描述』！")
    else:
        sheet = connect_to_sheets()
        if sheet:
            # 整理資料列
            new_row = [
                str(date), 
                str(time), 
                name, 
                phone, 
                car_id, 
                location, 
                description, 
                staff
            ]
            # 寫入 Google Sheets
            sheet.append_row(new_row)
            st.success("✅ 資料已成功上傳至 Google 表格！")
            st.balloons()

# --- 4. 顯示最近紀錄 ---
st.divider()
if st.button("查看雲端最新 5 筆資料"):
    sheet = connect_to_sheets()
    if sheet:
        data = sheet.get_all_records()
        if data:
            df = pd.DataFrame(data)
            st.write("### 最近登記紀錄")
            st.dataframe(df.tail(5))
        else:
            st.info("目前表格中尚無資料。")
