import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import datetime
import pandas as pd
import pytz

# --- 1. 樣式強化 (解決亂碼與字體模糊) ---
st.set_page_config(page_title="應安客服雲端登記系統", layout="wide")
st.markdown("""
    <style>
    #MainMenu, header, footer, .stAppDeployButton {visibility: hidden;}
    
    /* 2/26 標配字體 */
    * { 
        color: #000000 !important; 
        font-family: "Microsoft JhengHei", sans-serif !important; 
        font-weight: 800 !important; 
        -webkit-font-smoothing: antialiased;
    }

    /* 解決 211824 亂碼問題：排除 Expander 的圖示與結構文字 */
    div[data-testid="stExpander"] details summary span,
    div[data-testid="stExpander"] details summary svg,
    div[data-testid="stExpander"] details summary p {
        font-weight: normal !important;
        display: inline-flex !important;
    }
    
    /* 恢復最近紀錄的表格線條 */
    .record-header { border-bottom: 2px solid #000; padding: 10px 0; margin-bottom: 5px; }
    .record-row { border-bottom: 1px solid #ccc; padding: 8px 0; align-items: center; }
    </style>
    """, unsafe_allow_html=True)

tw_timezone = pytz.timezone('Asia/Taipei')

# --- 2. 雲端連線 ---
def init_connection():
    try:
        creds_dict = st.secrets["google_sheets"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds)
    except: return None

client = init_connection()
main_spreadsheet = client.open("客服作業表")
sheet = main_spreadsheet.sheet1

# --- 3. 動態讀取場站 (排除快取) ---
def get_station_list():
    try:
        ws = main_spreadsheet.worksheet("Station_Settings")
        data = ws.col_values(1)[1:] # 跳過標題
        return ["請選擇或輸入關鍵字搜尋"] + sorted([str(x).strip() for x in data if x])
    except:
        return ["請選擇或輸入關鍵字搜尋", "華視光復", "電視台"]

tab1, tab2 = st.tabs(["📝 案件登記", "📊 數據統計分析"])

with tab1:
    st.title("📝 應安客服線上登記系統")
    now_ts = datetime.datetime.now(tw_timezone)

    # --- 獨立新增區塊 (修正 211824 問題) ---
    with st.expander("➕ 快速新增場站 (若選單找不到請按此)", expanded=False):
        c_new1, c_new2 = st.columns([3, 1])
        new_st_input = c_new1.text_input("輸入新場站名稱", key="input_new_st")
        if c_new2.button("確認新增", key="btn_new_st"):
            if new_st_input.strip():
                main_spreadsheet.worksheet("Station_Settings").append_row([new_st_input.strip()])
                st.toast(f"✅ 已成功新增：{new_st_input}")
                st.rerun() # 強制刷新以更新下拉選單

    # --- 案件登記表單 ---
    current_stations = get_station_list()
    with st.form(key="reg_form"):
        # ... (此處維持 2/26 版表單內容)
        st.write("表單內容載入中...")
        submit = st.form_submit_button("確認送出")

    # --- 恢復最近紀錄 (對齊 211313 截圖樣式) ---
    st.markdown("---")
    st.subheader("🔍 最近紀錄 (交班動態)")
    
    # 這裡手動建立 Header
    h1, h2, h3, h4, h5, h6, h7, h8, h9 = st.columns([1.5, 1.5, 1, 1.5, 1.5, 1.5, 3, 1, 1])
    h1.write("日期/時間")
    h2.write("場站")
    h3.write("姓名")
    h4.write("電話")
    h5.write("車號")
    h6.write("類別")
    h7.write("描述摘要")
    h8.write("編輯")
    h9.write("標記")
    st.markdown('<div class="record-header"></div>', unsafe_allow_html=True)

    # 讀取並顯示資料
    try:
        raw_data = sheet.get_all_values()[1:]
        for row in reversed(raw_data[-10:]): # 顯示最後 10 筆
            r1, r2, r3, r4, r5, r6, r7, r8, r9 = st.columns([1.5, 1.5, 1, 1.5, 1.5, 1.5, 3, 1, 1])
            r1.write(row[0]) # 時間
            r2.write(row[1]) # 場站
            r3.write(row[2]) # 姓名
            r4.write(row[3]) # 電話
            r5.write(row[4]) # 車號
            r6.write(row[5]) # 類別
            r7.write(row[6]) # 摘要
            r8.button("📝", key=f"edit_{row[0]}") # 編輯按鈕
            r9.checkbox("", key=f"check_{row[0]}") # 標記勾選框
    except:
        st.error("暫時無法讀取最近紀錄")

# --- Tab 2: 維持 2026-02-26 數據統計順序 ---
# (此部分代碼略，請保留您原本 2/26 的統計圖表邏輯)
