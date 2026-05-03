import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import datetime
import pandas as pd
import pytz
import plotly.express as px

# --- 1. 樣式優化 (修正字體暈開問題，保留 2026-02-26 核心風格) ---
st.set_page_config(page_title="應安客服雲端登記系統", layout="wide")
st.markdown("""
    <style>
    #MainMenu, header, footer, .stAppDeployButton {visibility: hidden;}
    
    /* 修正字體糊掉：加入 antialiasing 與優化粗細 */
    * { 
        color: #000000 !important; 
        font-family: "Microsoft JhengHei", "PingFang TC", sans-serif !important; 
        font-weight: 800 !important; /* 從 900 調至 800，避免筆畫擠在一起 */
        -webkit-font-smoothing: antialiased; /* 增加字體銳利度 */
        -moz-osx-font-smoothing: grayscale;
    }
    
    /* 確保 4K 邊框清晰 */
    .stDataFrame, .stTable { border: 2px solid #000000 !important; }
    </style>
    """, unsafe_allow_html=True)

tw_timezone = pytz.timezone('Asia/Taipei')

# --- 2. 連線與動態場站邏輯 (對齊 Station_Settings 表格) ---
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
    """從 Station_Settings 讀取場站，並絕對確保『新增選項』存在"""
    final_list = ["請選擇或輸入關鍵字搜尋"]
    try:
        # 讀取圖片中的 Station_Settings 分頁
        ws = main_spreadsheet.worksheet("Station_Settings")
        # 抓取 A 欄資料，排除標題並去空白
        cloud_data = [str(x).strip() for x in ws.col_values(1)[1:] if x]
        final_list.extend(cloud_data)
    except:
        final_list.extend(["華視光復", "電視台"]) # 備援
    
    final_list.append("＋ 新增場站...")
    return final_list

# --- 3. 2026-02-26 固定清單與顏色 ---
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
            
        # --- 顯示新增場站輸入框 ---
        new_st_name = ""
        if selected_st == "＋ 新增場站...":
            new_st_name = st.text_input("✨ 請輸入新場站名稱", placeholder="例如：西門停車場")

        c3, c4 = st.columns(2)
        with c3: cat = st.selectbox("類別", options=CATEGORY_LIST)
        with c4: car = st.text_input("車號")
        desc = st.text_area("描述內容")
        
        if st.form_submit_button("確認送出"):
            final_st = new_st_name.strip() if selected_st == "＋ 新增場站..." else selected_st
            if staff != "請選擇填單人" and final_st not in ["", "請選擇或輸入關鍵字搜尋"]:
                # 如果是新增場站，同步寫入 Station_Settings 表格
                if selected_st == "＋ 新增場站...":
                    main_spreadsheet.worksheet("Station_Settings").append_row([final_st])
                
                sheet.append_row([now_ts.strftime("%Y-%m-%d %H:%M"), final_st, caller, phone, car.upper(), cat, desc, staff])
                st.success(f"✅ 成功送出！場站：{final_st}")
                st.session_state.form_id += 1
                st.rerun()
            else:
                st.error("請確認填單人與場站欄位已完整填寫")

    # --- 最近紀錄恢復 (修正時間比對邏輯) ---
    st.markdown("---")
    st.subheader("🔍 最近紀錄 (8小時內自動顯示)")
    try:
        raw_data = sheet.get_all_values()
        if len(raw_data) > 1:
            df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
            df['time_obj'] = pd.to_datetime(df.iloc[:, 0], errors='coerce')
            # 8 小時過濾邏輯
            cutoff = now_ts.replace(tzinfo=None) - datetime.timedelta(hours=8)
            df_recent = df[df['time_obj'] > cutoff].sort_values(by='time_obj', ascending=False)
            if not df_recent.empty:
                st.dataframe(df_recent.drop(columns=['time_obj']), use_container_width=True)
            else:
                st.write("目前無 8 小時內紀錄。")
    except:
        st.write("連線紀錄載入中...")

# --- Tab 2: 數據統計分析 (完全鎖定 2026-02-26 順序) ---
# 1. 雙週案件類別對比分析 2. 當前區間案件分佈 3. 場站排名 (Top 10) 
# 4. 場站 vs. 異常類別分析 5. 類別精確統計
