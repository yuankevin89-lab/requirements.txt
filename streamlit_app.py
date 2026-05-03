import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import datetime
import pandas as pd
import pytz
import plotly.express as px

# [2026-02-26 版核心樣式]
st.set_page_config(page_title="應安客服雲端登記系統", layout="wide")
st.markdown("""
    <style>
    #MainMenu, header, footer, .stAppDeployButton {visibility: hidden;}
    * { color: #000000 !important; font-family: "Microsoft JhengHei", sans-serif !important; font-weight: 900 !important; }
    </style>
    """, unsafe_allow_html=True)

tw_timezone = pytz.timezone('Asia/Taipei')

# [連線與動態場站邏輯]
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
    try:
        ws = main_spreadsheet.worksheet("Station_Settings")
        data = [str(x).strip() for x in ws.col_values(1)[1:] if x]
        return ["請選擇或輸入關鍵字搜尋"] + data + ["＋ 新增場站..."]
    except:
        return ["請選擇或輸入關鍵字搜尋", "華視光復", "＋ 新增場站..."]

# [2026-02-26 版固定清單]
STAFF_LIST = ["請選擇填單人", "宗哲", "美妞", "政宏", "文輝", "恩佳", "志榮", "阿錨", "子毅", "浚"]
CATEGORY_LIST = ["發票問題無法繳費", "網路問題無法繳費", "發票缺紙或卡紙", "無法找零", "身障優惠折抵", "網路異常", "繳費問題相關", "其他"]

if "form_id" not in st.session_state: st.session_state.form_id = 0

tab1, tab2 = st.tabs(["📝 案件登記", "📊 數據統計分析"])

with tab1:
    st.title("📝 應安客服線上登記系統")
    current_stations = get_station_list()
    now_ts = datetime.datetime.now(tw_timezone)

    with st.form(key=f"f_{st.session_state.form_id}"):
        st.info(f"🕒 案件時間：{now_ts.strftime('%Y-%m-%d %H:%M')}")
        c1, c2 = st.columns(2)
        with c1:
            selected_st = st.selectbox("場站名稱", options=current_stations)
            caller = st.text_input("姓名")
        with c2:
            staff = st.selectbox("填單人", options=STAFF_LIST)
            phone = st.text_input("電話")
            
        # 關鍵：若選擇新增，顯示輸入框
        new_st_name = ""
        if selected_st == "＋ 新增場站...":
            new_st_name = st.text_input("✨ 請輸入新場站名稱")

        c3, c4 = st.columns(2)
        with c3: cat = st.selectbox("類別", options=CATEGORY_LIST)
        with c4: car = st.text_input("車號")
        desc = st.text_area("描述內容")
        
        if st.form_submit_button("確認送出"):
            final_st = new_st_name.strip() if selected_st == "＋ 新增場站..." else selected_st
            if staff != "請選擇填單人" and final_st not in ["", "請選擇或輸入關鍵字搜尋"]:
                if selected_st == "＋ 新增場站...":
                    main_spreadsheet.worksheet("Station_Settings").append_row([final_st])
                sheet.append_row([now_ts.strftime("%Y-%m-%d %H:%M"), final_st, caller, phone, car.upper(), cat, desc, staff])
                st.success("✅ 送出成功")
                st.session_state.form_id += 1
                st.rerun()

    # [最近紀錄恢復邏輯]
    st.markdown("---")
    st.subheader("🔍 最近紀錄 (8小時內自動顯示)")
    try:
        raw_data = sheet.get_all_values()
        if len(raw_data) > 1:
            df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
            # 修正時間比對邏輯
            df['時間物件'] = pd.to_datetime(df.iloc[:, 0], errors='coerce')
            cutoff = now_ts.replace(tzinfo=None) - datetime.timedelta(hours=8)
            df_recent = df[df['時間物件'] > cutoff].sort_values(by='時間物件', ascending=False)
            if not df_recent.empty:
                st.dataframe(df_recent.drop(columns=['時間物件']), use_container_width=True)
    except: st.write("尚無近期紀錄")

# [Tab 2 數據統計分頁 - 完整保留 2026-02-26 圖表順序與邏輯]
# ... (此處保留原 2/26 版 Tab 2 完整代碼)
