import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import datetime

# --- 1. 頁面基本設定 ---
st.set_page_config(page_title="應安客服雲端登記系統", page_icon="📝")

# --- 2. Google Sheets 連線函式 ---
def init_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["google_sheets"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client

# 嘗試連線
try:
    client = init_connection()
    # 已改為指定的試算表名稱：客服作業表
    sheet = client.open("客服作業表").sheet1
    conn_success = True
except Exception as e:
    st.error(f"連線失敗，請檢查 Secrets 格式或 Google Sheets 權限。")
    st.info(f"錯誤訊息：{e}")
    conn_success = False

# --- 3. 程式主介面 ---
st.title("📝 應安客服雲端登記系統")
st.write("請填寫下方欄位，系統將自動記錄提交時間。")

if conn_success:
    with st.form("my_form", clear_on_submit=True):
        
        # A. 自動抓取當下時間
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.info(f"🕒 登記時間：{now} (系統自動偵測)")
        
        # B. 使用者填寫內容
        col1, col2 = st.columns(2)
        with col1:
            # 範例已改為：華視光復場
            station_name = st.text_input("場站名稱 (必填)", placeholder="例如：華視光復場")
            caller_name = st.text_input("來電人 (選填)", placeholder="可留空")
        with col2:
            user_name = st.text_input("填單人姓名 (必填)", placeholder="請輸入姓名")
            caller_phone = st.text_input("電話 (選填)", placeholder="可留空")
        
        col3, col4 = st.columns(2)
        with col3:
            category = st.selectbox(
                "案件類別", 
                ["繳費機故障", "發票缺紙或卡紙", "無法找零", "身障優惠折抵", "其他"]
            )
        with col4:
            car_number = st.text_input("車號 (選填)", placeholder="可留空")
            
        description = st.text_area("詳細描述 (必填)", placeholder="請具體說明需求內容...")
        
        # C. 提交按鈕
        submit = st.form_submit_button("確認提交並同步雲端")

        if submit:
            if user_name and station_name and description:
                try:
                    # 寫入順序：[時間, 場站名稱, 填單人姓名, 案件類別, 來電人, 電話, 車號, 描述]
                    row_to_add = [now, station_name, user_name, category, caller_name, caller_phone, car_number, description]
                    sheet.append_row(row_to_add)
                    st.success("✅ 資料已成功上傳至 Google 表格！")
                    st.balloons()
                except Exception as upload_error:
                    st.error(f"上傳時發生錯誤：{upload_error}")
            else:
                st.warning("⚠️ 場站名稱、姓名與描述為必填項，請填寫完整。")

# --- 4. 頁尾資訊 ---
st.markdown("---")
st.caption("© 2026 應安客服管理系統 | 本系統僅供內部員工登記使用")
