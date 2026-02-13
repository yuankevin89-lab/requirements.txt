import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import datetime

# --- 頁面設定 ---
st.set_page_config(page_title="公司內部案件登記系統", page_icon="📝")

# --- Google Sheets 連線設定 ---
def init_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # 從 Streamlit Secrets 讀取金鑰
    creds_dict = st.secrets["google_sheets"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client

try:
    client = init_connection()
    # 請確保下方的名稱與你的 Google Sheets 檔名完全一致
    sheet = client.open("你的試算表名稱").sheet1
    conn_success = True
except Exception as e:
    st.error(f"連線 Google Sheets 失敗: {e}")
    conn_success = False

# --- 程式主畫面 ---
st.title("📝 公司內部案件登記系統")
st.write("請填寫下方欄位，系統將自動記錄提交時間。")

if conn_success:
    with st.form("registration_form", clear_on_submit=True):
        # 自動抓取當下時間
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.info(f"🕒 登記時間：{current_time} (系統自動抓取)")
        
        # 使用者填寫欄位
        name = st.text_input("填單人姓名")
        category = st.selectbox("案件類別", ["設備報修", "行政需求", "資訊諮詢", "其他"])
        content = st.text_area("內容描述")
        
        submit_button = st.form_submit_button("確認提交並同步雲端")

        if submit_button:
            if name and content:
                try:
                    # 將資料組成清單：[時間, 姓名, 類別, 內容]
                    new_data = [current_time, name, category, content]
                    sheet.append_row(new_data)
                    st.success("✅ 資料已成功上傳至 Google 表格！")
                    st.balloons()
                except Exception as ex:
                    st.error(f"上傳失敗：{ex}")
            else:
                st.warning("⚠️ 請填寫完整內容再提交。")

# --- 頁尾標示 ---
st.markdown("---")
st.caption("本系統僅供公司內部使用")
