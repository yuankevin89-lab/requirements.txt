import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import datetime
import pytz

# --- 1. 樣式強化 (對齊 2/26 銳利視覺 & 解決亂碼) ---
st.set_page_config(page_title="應安客服雲端登記系統", layout="wide")
st.markdown("""
    <style>
    #MainMenu, header, footer, .stAppDeployButton {visibility: hidden;}
    p, span, label, .stMarkdown, .stSelectbox, .stTextInput, .stTextArea {
        color: #000000 !important;
        font-family: "Microsoft JhengHei", sans-serif !important;
        font-weight: 800 !important;
    }
    .record-header { border-bottom: 2px solid #000; padding: 10px 0; }
    </style>
    """, unsafe_allow_html=True)

tw_timezone = pytz.timezone('Asia/Taipei')

# 初始化編輯狀態
if 'edit_data' not in st.session_state:
    st.session_state.edit_data = None

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
station_ws = main_spreadsheet.worksheet("Station_Settings")

tab1, tab2 = st.tabs(["📝 案件登記", "📊 數據統計分析"])

with tab1:
    st.title("📝 應安客服線上登記系統")
    
    # 快速新增場站區塊
    with st.container():
        st.markdown("### 🏢 場站管理")
        c_new1, c_new2 = st.columns([4, 1])
        new_st = c_new1.text_input("新增場站名稱", key="input_new_st")
        if c_new2.button("➕ 確認新增"):
            if new_st:
                station_ws.append_row([new_st.strip()])
                st.success(f"已新增：{new_st}")
                st.rerun()

    st.markdown("---")

    # --- 案件登記表單 (編輯鎖定邏輯) ---
    stations = ["請選擇或輸入關鍵字搜尋"] + sorted([x for x in station_ws.col_values(1)[1:] if x])
    staff_list = ["請選擇填單人", "宗哲", "美妞", "政宏", "文輝", "恩佳", "志榮", "阿錨", "子毅", "敘峻"]
    cat_list = ["發票問題無法繳費", "網路問題無法繳費", "發票缺紙或卡紙", "無法找零", "身障優惠折抵", "網路異常", "繳費問題相關", "其他"]

    e = st.session_state.edit_data
    is_editing = e is not None  # 判斷是否為編輯狀態

    st.subheader("🖋️ " + ("正在編輯紀錄 (場站與填單人已鎖定)" if is_editing else "新案件登記"))
    
    with st.form("entry_form"):
        col1, col2 = st.columns(2)
        with col1:
            st_idx = stations.index(e[1]) if is_editing and e[1] in stations else 0
            # 關鍵修正：is_editing 為 True 時 disabled=True
            sel_st = st.selectbox("場站名稱", stations, index=st_idx, disabled=is_editing)
            u_name = st.text_input("姓名", value=e[2] if is_editing else "")
        with col2:
            stf_idx = staff_list.index(e[7]) if is_editing and e[7] in staff_list else 0
            # 關鍵修正：is_editing 為 True 時 disabled=True
            u_staff = st.selectbox("填單人", staff_list, index=stf_idx, disabled=is_editing)
            u_phone = st.text_input("電話", value=e[3] if is_editing else "")
        
        col3, col4 = st.columns(2)
        with col3:
            cat_idx = cat_list.index(e[5]) if is_editing and e[5] in cat_list else 0
            u_cat = st.selectbox("類別", cat_list, index=cat_idx)
        with col4:
            u_car = st.text_input("車號", value=e[4] if is_editing else "")
        
        u_desc = st.text_area("描述內容", value=e[6] if is_editing else "")
        
        c_btn1, c_btn2 = st.columns([1, 5])
        submit = c_btn1.form_submit_button("✅ 確認送出")
        cancel = c_btn2.form_submit_button("❌ 取消編輯") if is_editing else False

        if submit:
            if u_staff != "請選擇填單人" and sel_st != "請選擇或輸入關鍵字搜尋":
                now_str = datetime.datetime.now(tw_timezone).strftime("%Y-%m-%d %H:%M")
                # 編輯模式下，場站與填單人維持原值 e[1] 與 e[7]
                final_st = e[1] if is_editing else sel_st
                final_staff = e[7] if is_editing else u_staff
                
                new_row = [now_str, final_st, u_name, u_phone, u_car.upper(), u_cat, u_desc, final_staff]
                sheet.append_row(new_row)
                st.session_state.edit_data = None
                st.success("資料登記成功！")
                st.rerun()

        if cancel:
            st.session_state.edit_data = None
            st.rerun()

    # --- 最近紀錄 (對齊 211313.png 樣式) ---
    st.markdown("### 🔍 最近紀錄 (交班動態)")
    h = st.columns([1.5, 1.2, 0.8, 1.2, 1, 1.5, 3, 1, 0.6, 0.6])
    titles = ["日期/時間", "場站", "姓名", "電話", "車號", "類別", "描述摘要", "填單人", "編輯", "標記"]
    for i, t in enumerate(titles): h[i].write(t)
    st.markdown('<div class="record-header"></div>', unsafe_allow_html=True)

    try:
        data_rows = sheet.get_all_values()[1:]
        for idx, row in enumerate(reversed(data_rows[-10:])):
            r = st.columns([1.5, 1.2, 0.8, 1.2, 1, 1.5, 3, 1, 0.6, 0.6])
            for i in range(8):
                r[i].write(row[i] if i < len(row) else "")
            
            if r[8].button("📝", key=f"edit_btn_{idx}"):
                st.session_state.edit_data = row
                st.rerun()
                
            r[9].checkbox("", key=f"chk_{idx}")
    except:
        st.error("讀取紀錄失敗")

# --- Tab 2: 數據統計 (依照 2/26 規定，5 大圖表順序保持不變) ---
#
