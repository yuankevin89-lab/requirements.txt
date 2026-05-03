import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import datetime
import pandas as pd
import pytz
import plotly.express as px
import re

# --- 1. 樣式與設定 (2026-02-26 核心版) ---
st.set_page_config(page_title="應安客服雲端登記系統", page_icon="📝", layout="wide")
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
    * { color: #000000 !important; font-family: "Microsoft JhengHei", sans-serif !important; font-weight: 900 !important; }
    .stAppDeployButton {display: none;}
    </style>
    """, unsafe_allow_html=True)

tw_timezone = pytz.timezone('Asia/Taipei')

# --- 2. 連線與動態場站函數 ---
def init_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds_dict = st.secrets["google_sheets"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        return gspread.authorize(creds)
    except: return None

client = init_connection()
main_spreadsheet = client.open("客服作業表") if client else None
sheet = main_spreadsheet.sheet1 if main_spreadsheet else None

def get_station_list():
    """動態抓取場站，確保一定有新增選項"""
    try:
        setting_ws = main_spreadsheet.worksheet("Station_Settings")
        # 抓取第一欄 (排除標題)，並過濾空值
        raw_list = [str(x).strip() for x in setting_ws.col_values(1)[1:] if x]
        return ["請選擇或輸入關鍵字搜尋"] + raw_list + ["＋ 新增場站..."]
    except:
        return ["請選擇或輸入關鍵字搜尋", "華視光復", "其他(未登入場站)", "＋ 新增場站..."]

STAFF_LIST = ["請選擇填單人", "宗哲", "美妞", "政宏", "文輝", "恩佳", "志榮", "阿錨", "子毅", "浚"]
CATEGORY_LIST = ["發票問題無法繳費", "網路問題無法繳費", "發票缺紙或卡紙", "無法找零", "身障優惠折抵", "網路異常", "繳費問題相關", "其他"]

if "form_id" not in st.session_state: st.session_state.form_id = 0

tab1, tab2 = st.tabs(["📝 案件登記", "📊 數據統計分析"])

# --- Tab 1: 案件登記 ---
with tab1:
    st.title("📝 應安客服線上登記系統")
    current_stations = get_station_list()
    now_ts = datetime.datetime.now(tw_timezone)
    
    with st.form(key=f"main_form_{st.session_state.form_id}"):
        f_dt = now_ts.strftime("%Y-%m-%d %H:%M")
        st.info(f"🕒 案件時間：{f_dt}")
        
        c1, c2 = st.columns(2)
        with c1:
            selected_station = st.selectbox("場站名稱", options=current_stations)
            caller_name = st.text_input("姓名")
        with c2:
            user_name = st.selectbox("填單人", options=STAFF_LIST)
            caller_phone = st.text_input("電話")
            
        # 修正：新增場站輸入框顯示判斷
        new_station_name = ""
        if selected_station == "＋ 新增場站...":
            new_station_name = st.text_input("✨ 請輸入新場站名稱 (必填)", key="new_st_input")

        c3, c4 = st.columns(2)
        with c3: category = st.selectbox("類別", options=CATEGORY_LIST)
        with c4: car_num = st.text_input("車號")
        description = st.text_area("描述內容")
        
        submit_btn = st.form_submit_button("確認送出")

        if submit_btn:
            # 決定最終場站名稱
            final_st = new_station_name.strip() if selected_station == "＋ 新增場站..." else selected_station
            
            if user_name != "請選擇填單人" and final_st not in ["", "請選擇或輸入關鍵字搜尋"]:
                # 如果是新場站，寫入 Station_Settings
                if selected_station == "＋ 新增場站...":
                    main_spreadsheet.worksheet("Station_Settings").append_row([final_st])
                
                row = [f_dt, final_st, caller_name, caller_phone, car_num.upper(), category, description, user_name]
                sheet.append_row(row)
                st.success(f"✅ 已成功送出！")
                st.session_state.form_id += 1
                st.rerun()
            else:
                st.error("請檢查填單人或場站名稱是否正確")

    # --- 關鍵修正：最近紀錄顯示 (8小時內) ---
    st.markdown("---")
    st.subheader("🔍 最近紀錄 (8小時內自動顯示)")
    try:
        all_data = sheet.get_all_values()
        if len(all_data) > 1:
            df_recent = pd.DataFrame(all_data[1:], columns=all_data[0])
            df_recent['時間'] = pd.to_datetime(df_recent.iloc[:, 0], errors='coerce')
            
            # 過濾 8 小時內的資料
            cutoff = now_ts - datetime.timedelta(hours=8)
            # 確保時區一致進行比對
            df_recent = df_recent[pd.to_datetime(df_recent['時間']).dt.tz_localize(None) > cutoff.replace(tzinfo=None)]
            
            if not df_recent.empty:
                st.dataframe(df_recent.sort_values(by='時間', ascending=False), use_container_width=True)
            else:
                st.write("目前 8 小時內尚無紀錄。")
    except Exception as e:
        st.error(f"讀取最近紀錄失敗: {e}")

# (Tab 2 統計圖表維持 2026-02-26 版本順序與邏輯)
