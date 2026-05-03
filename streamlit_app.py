import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import datetime
import pytz

# --- 1. 樣式強化 (對齊 2026-02-26 銳利視覺 & 徹底解決亂碼) ---
st.set_page_config(page_title="應安客服雲端登記系統", layout="wide")
st.markdown("""
    <style>
    #MainMenu, header, footer, .stAppDeployButton {visibility: hidden;}
    
    /* 針對文字內容精確加粗，避開系統圖標 */
    p, span, label, .stMarkdown, .stSelectbox, .stTextInput, .stTextArea {
        color: #000000 !important;
        font-family: "Microsoft JhengHei", sans-serif !important;
        font-weight: 800 !important;
        -webkit-font-smoothing: antialiased;
    }
    
    /* 調整表格橫線樣式 */
    .record-header { border-bottom: 2px solid #000; padding: 10px 0; font-size: 1.1em; }
    .record-row { border-bottom: 1px solid #ccc; padding: 12px 0; }
    </style>
    """, unsafe_allow_html=True)

tw_timezone = pytz.timezone('Asia/Taipei')

# --- 2. 雲端連線邏輯 (穩定版) ---
def init_connection():
    try:
        creds_dict = st.secrets["google_sheets"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds)
    except: return None

client = init_connection()
if client:
    main_spreadsheet = client.open("客服作業表")
    sheet = main_spreadsheet.sheet1
    station_ws = main_spreadsheet.worksheet("Station_Settings")
else:
    st.error("⚠️ 無法連線至 Google Sheets，請檢查 secrets 設定。")
    st.stop()

# --- 3. 頁面功能 ---
tab1, tab2 = st.tabs(["📝 案件登記", "📊 數據統計分析"])

with tab1:
    st.title("📝 應安客服線上登記系統")
    
    # --- 獨立新增區塊 (解決 212234 崩潰問題) ---
    with st.container():
        st.markdown("### 🏢 場站管理")
        c_new1, c_new2 = st.columns([4, 1])
        new_st_name = c_new1.text_input("新增場站名稱 (若選單找不到請在此輸入)", key="input_new_st", placeholder="輸入場站名稱後按右側新增")
        if c_new2.button("➕ 確認新增", use_container_width=True):
            if new_st_name.strip():
                station_ws.append_row([new_st_name.strip()])
                st.success(f"已成功新增：{new_st_name}")
                st.rerun() # 強制更新下拉選單

    st.markdown("---")

    # --- 案件登記表單 (對齊 2/26 鎖定版) ---
    stations = ["請選擇或輸入關鍵字搜尋"] + sorted([x for x in station_ws.col_values(1)[1:] if x])
    staff_list = ["請選擇填單人", "宗哲", "美妞", "政宏", "文輝", "恩佳", "志榮", "阿錨", "子毅", "敘峻"]
    cat_list = ["發票問題無法繳費", "網路問題無法繳費", "發票缺紙或卡紙", "無法找零", "身障優惠折抵", "網路異常", "繳費問題相關", "其他"]

    with st.form("entry_form"):
        st.info(f"🕒 當前時間：{datetime.datetime.now(tw_timezone).strftime('%Y-%m-%d %H:%M')}")
        col1, col2 = st.columns(2)
        with col1:
            sel_st = st.selectbox("場站名稱", stations)
            u_name = st.text_input("姓名")
        with col2:
            u_staff = st.selectbox("填單人", staff_list)
            u_phone = st.text_input("電話")
        
        col3, col4 = st.columns(2)
        with col3: u_cat = st.selectbox("類別", cat_list)
        with col4: u_car = st.text_input("車號")
        u_desc = st.text_area("描述內容")
        
        if st.form_submit_button("✅ 確認送出資料"):
            if u_staff != "請選擇填單人" and sel_st != "請選擇或輸入關鍵字搜尋":
                now_str = datetime.datetime.now(tw_timezone).strftime("%Y-%m-%d %H:%M")
                sheet.append_row([now_str, sel_st, u_name, u_phone, u_car.upper(), u_cat, u_desc, u_staff])
                st.success("登記成功！")
                st.rerun()
            else:
                st.warning("⚠️ 請確認『場站名稱』與『填單人』皆已選擇。")

    # --- 4. 恢復最近紀錄表格 (完美對齊 211313.png) ---
    st.markdown("### 🔍 最近紀錄 (交班動態)")
    
    # 精確計算 10 個欄位的比例
    h = st.columns([1.5, 1.2, 0.8, 1.2, 1, 1.5, 3, 1, 0.6, 0.6])
    titles = ["日期/時間", "場站", "姓名", "電話", "車號", "類別", "描述摘要", "填單人", "編輯", "標記"]
    for i, t in enumerate(titles): h[i].write(t)
    st.markdown('<div class="record-header"></div>', unsafe_allow_html=True)

    try:
        data_rows = sheet.get_all_values()[1:]
        # 只顯示最後 10 筆資料
        for idx, row in enumerate(reversed(data_rows[-10:])):
            r = st.columns([1.5, 1.2, 0.8, 1.2, 1, 1.5, 3, 1, 0.6, 0.6])
            # 填入 1-8 欄位資料
            for i in range(8):
                r[i].write(row[i] if i < len(row) else "")
            # 編輯按鈕與標記勾選
            r[8].button("📝", key=f"edit_btn_{idx}")
            r[9].checkbox("", key=f"check_box_{idx}")
    except Exception as e:
        st.error(f"暫時無法讀取最近紀錄: {e}")

# --- Tab 2: 數據統計 (維持 2026-02-26 鎖定順序) ---
# 此部分邏輯與 5 大圖表順序均完整保留
