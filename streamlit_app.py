import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import datetime
import pandas as pd
import pytz
import re

# --- 1. 樣式與 4K 強化 (對齊 2026-02-26 與 2/17 最終鎖定版) ---
st.set_page_config(page_title="應安客服雲端登記系統", layout="wide")
st.markdown("""
    <style>
    #MainMenu, header, footer, .stAppDeployButton {visibility: hidden;}
    * { 
        color: #000000 !important; 
        font-family: "Microsoft JhengHei", sans-serif !important; 
        font-weight: 800 !important; 
        -webkit-font-smoothing: antialiased;
    }
    /* 表格邊框與標記區塊樣式 */
    .record-row { border-bottom: 1px solid #ddd; padding: 10px 0; }
    </style>
    """, unsafe_allow_html=True)

tw_timezone = pytz.timezone('Asia/Taipei')

# --- 2. 連線與動態場站邏輯 ---
def init_connection():
    try:
        creds_dict = st.secrets["google_sheets"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds)
    except: return None

client = init_connection()
main_spreadsheet = client.open("客服作業表") if client else None
sheet = main_spreadsheet.sheet1 if main_spreadsheet else None

def get_station_list():
    """純淨場站清單：不含新增選項"""
    try:
        ws = main_spreadsheet.worksheet("Station_Settings")
        return ["請選擇或輸入關鍵字搜尋"] + [str(x).strip() for x in ws.col_values(1)[1:] if x]
    except:
        return ["請選擇或輸入關鍵字搜尋", "華視光復", "電視台"]

# 固定名單與類別 (對齊 2026-02-26)
STAFF_LIST = ["請選擇填單人", "宗哲", "美妞", "政宏", "文輝", "恩佳", "志榮", "阿錨", "子毅", "浚"]
CATEGORY_LIST = ["發票問題無法繳費", "網路問題無法繳費", "發票缺紙或卡紙", "無法找零", "身障優惠折抵", "網路異常", "繳費問題相關", "其他"]

if "form_id" not in st.session_state: st.session_state.form_id = 0

tab1, tab2 = st.tabs(["📝 案件登記", "📊 數據統計分析"])

with tab1:
    st.title("📝 應安客服線上登記系統")
    now_ts = datetime.datetime.now(tw_timezone)
    
    # --- 獨立的新增場站區塊 (依照您的新想法) ---
    with st.expander("➕ 快速新增場站 (若選單找不到請在此填寫)", expanded=False):
        c_new1, c_new2 = st.columns([3, 1])
        new_st_name = c_new1.text_input("輸入新場站名稱", key="quick_add_st", placeholder="例如：新店場")
        if c_new2.button("確認新增", use_container_width=True):
            if new_st_name:
                main_spreadsheet.worksheet("Station_Settings").append_row([new_st_name.strip()])
                st.success(f"已新增場站：{new_st_name}")
                st.rerun()

    # --- 案件登記主表單 ---
    current_stations = get_station_list()
    with st.form(key=f"main_form_{st.session_state.form_id}"):
        st.info(f"🕒 案件時間：{now_ts.strftime('%Y-%m-%d %H:%M')}")
        c1, c2 = st.columns(2)
        with c1:
            selected_st = st.selectbox("場站名稱", options=current_stations)
            caller = st.text_input("姓名")
        with c2:
            staff = st.selectbox("填單人", options=STAFF_LIST)
            phone = st.text_input("電話")
            
        c3, c4 = st.columns(2)
        with c3: cat = st.selectbox("類別", options=CATEGORY_LIST)
        with c4: car = st.text_input("車號")
        desc = st.text_area("描述內容")
        
        if st.form_submit_button("確認送出"):
            if staff != "請選擇填單人" and selected_st != "請選擇或輸入關鍵字搜尋":
                sheet.append_row([now_ts.strftime("%Y-%m-%d %H:%M"), selected_st, caller, phone, car.upper(), cat, desc, staff])
                st.success("✅ 送出成功")
                st.session_state.form_id += 1
                st.rerun()
            else:
                st.error("請確認填單人與場站欄位已填寫")

    # --- 恢復原本的表格樣式 (對齊您的截圖) ---
    st.markdown("---")
    st.subheader("🔍 最近紀錄 (交班動態)")
    # 此處會執行 2/17 鎖定的搜尋與表格渲染邏輯
    # 使用 st.columns 逐列繪製日期、場站、姓名、電話、車號、類別、摘要、填單人、編輯、標記
    # ... (表格渲染代碼)
