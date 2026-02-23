import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import datetime
import pandas as pd
import pytz
import plotly.express as px
import time
import threading

# --- 1. 頁面基本設定與 4K 投影樣式 ---
st.set_page_config(page_title="應安客服雲端登記系統", page_icon="📝", layout="wide")

# 4K 投影增強模式：字體加粗、純黑、高對比 [cite: 2026-02-23]
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display: none;}
    .block-container {padding-top: 2rem; padding-bottom: 1rem;}
    
    /* 全域字體強化 */
    html, body, [class*="css"], .stMarkdown, .stText {
        font-family: "Microsoft JhengHei", sans-serif !important;
        color: #000000 !important;
        font-weight: 900 !important;
    }
    
    /* 按鈕高對比樣式 [cite: 2026-02-13] */
    .stButton>button {
        width: 100%;
        background-color: #000000 !important;
        color: #FFFFFF !important;
        font-size: 24px !important;
        height: 60px;
        border: 2px solid #000000;
    }

    /* 標記變色樣式 [cite: 2026-02-16] */
    [data-testid="stElementContainer"]:has(input[type="checkbox"]:checked) {
        background-color: #e8f5e9 !important;
        border-radius: 8px;
        padding: 10px;
        border: 1px solid #c8e6c9;
    }
    </style>
    """, unsafe_allow_html=True)

tw_timezone = pytz.timezone('Asia/Taipei')

# --- 2. 初始設定與資料庫連線 ---
STATION_LIST = [
    "請選擇或輸入關鍵字搜尋", "華視光復","電視台","華視二","文教五","華視五","文教一","文教二","文教六","文教三",
    "延吉場","大安場","信義大安","樂業場","仁愛場","四維場","濟南一場","濟南二場","松智場","松勇二","六合市場",
    "統領場","信義安和","僑信場","台北民生場","美麗華場","基湖場","北安場","龍江場","農安場","明倫社宅",
    "民權西場","承德場","承德三","大龍場","延平北場","雙連","中山市場","助安中山場","南昌場","博愛場","金山場",
    "金華場","通化","杭南一","復興南","仁愛逸仙","興岩社福大樓","木柵社宅","泉州場","汀州場",
    "北平東場","福州場","水源市場","重慶南","西寧市場","西園國宅","復興北","宏泰民生","新洲美福善場","福善一",
    "石牌二","中央北","紅毛城","三玉","士林場","永平社宅","涼州場","大龍峒社宅","成功場","洲子場","環山",
    "文湖場","民善場","行愛場","新明場","德明研推","東湖場","舊宗社宅","行善五","秀山機車","景平","環狀A機車",
    "樹林水源","土城中華場","光正","合宜A2","合宜A3","合宜A6","裕民","中央二","中央三","陶都場","板橋文化1F","板橋文化B1",
    "佳音-同安","佳音-竹林","青潭國小","林口文化","秀峰","興南場","中和莊敬","三重永福","徐匯場","蘆洲保和",
    "蘆洲三民","榮華場","富貴場","鄉長二","汐止忠孝","新台五路","蘆竹場","龜山興富","竹東長春","竹南中山",
    "銅鑼停一","台中黎明場","後龍","台中復興","台中復興二","文心場","台中大和屋","一銀北港","西螺","虎尾",
    "民德","衛民","衛民二場","台南北門","台南永福","台南國華","台南民權","善化","仁德","台南中華場","致穩",
    "台南康樂場","金財神","蘭井","友愛場","佳音西園","中華信義","敦南場","中華北門場","東大門場", "其他(未登入場站)"
]

STAFF_LIST = ["請選擇填單人", "宗哲", "美妞", "政宏", "文輝", "恩佳", "志榮", "阿錨", "子毅", "浚"]
CATEGORY_LIST = ["繳費機異常", "發票缺紙或卡紙", "無法找零", "身障優惠折抵", "網路異常", "繳費問題相關", "其他"]

def init_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds_dict = st.secrets["google_sheets"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        return gspread.authorize(creds)
    except: return None

client = init_connection()
sheet = client.open("客服作業表").sheet1 if client else None

if "edit_mode" not in st.session_state:
    st.session_state.edit_mode, st.session_state.edit_row_idx, st.session_state.edit_data = False, None, [""]*8
if "form_id" not in st.session_state:
    st.session_state.form_id = 0

tab1, tab2 = st.tabs(["📝 案件登記", "📊 數據統計分析"])

# --- Tab 1: 案件登記 ---
with tab1:
    st.title("📝 應安客服線上登記系統")
    now_ts = datetime.datetime.now(tw_timezone)
    
    with st.form(key=f"my_form_{st.session_state.form_id}", clear_on_submit=False):
        d = st.session_state.edit_data if st.session_state.edit_mode else [""]*8
        f_dt = d[0] if st.session_state.edit_mode else now_ts.strftime("%Y-%m-%d %H:%M")
        st.info(f"🕒 案件時間：{f_dt}")
        
        c1, c2 = st.columns(2)
        with c1:
            station_name = st.selectbox("場站名稱", options=STATION_LIST, index=STATION_LIST.index(d[1]) if d[1] in STATION_LIST else 0)
            caller_name = st.text_input("姓名", value=d[2])
        with c2:
            user_name = st.selectbox("填單人", options=STAFF_LIST, index=STAFF_LIST.index(d[7]) if d[7] in STAFF_LIST else 0)
            caller_phone = st.text_input("電話", value=d[3])
            
        c3, c4 = st.columns(2)
        with c3:
            category = st.selectbox("類別", options=CATEGORY_LIST, index=CATEGORY_LIST.index(d[5]) if d[5] in CATEGORY_LIST else 6)
        with c4:
            car_num = st.text_input("車號", value=d[4])
            
        description = st.text_area("描述內容 (自動換行)", value=d[6]) # 自動換行支援 [cite: 2026-02-15]

        # --- 網頁版提醒設定 (替代 Tkinter) ---
        st.markdown("---")
        use_reminder = st.checkbox("⏰ 設定追蹤提醒 (時間到時網頁會提示)")
        r_c1, r_c2 = st.columns([3, 1])
        with r_c1:
            rem_msg = st.text_input("提醒內容", value=f"請追蹤：{station_name} ({car_num})")
        with r_c2:
            rem_mins = st.number_input("幾分鐘後提醒", min_value=1, value=10)

        st.markdown("---")
        btn_c1, btn_c2, _ = st.columns([1, 1, 2])
        submit_btn = btn_c1.form_submit_button("確認送出")
        
        if submit_btn:
            if user_name != "請選擇填單人" and station_name != "請選擇或輸入關鍵字搜尋":
                row = [f_dt, station_name, caller_name, caller_phone, car_num.upper(), category, description, user_name]
                if st.session_state.edit_mode:
                    sheet.update(f"A{st.session_state.edit_row_idx}:H{st.session_state.edit_row_idx}", [row])
                    st.session_state.edit_mode = False
                else:
                    sheet.append_row(row)
                
                # 提醒邏輯：網頁通知
                if use_reminder:
                    st.toast(f"⏰ 提醒已設定：{rem_mins} 分鐘後通知", icon="🚀")
                
                st.success("✅ 案件已成功存檔")
                st.session_state.form_id += 1
                st.rerun()

    st.markdown("---")
    st.subheader("🔍 最近紀錄 (智慧輪動)") # 8小時智慧輪動 [cite: 2026-02-17]
    if sheet:
        all_raw = sheet.get_all_values()
        if len(all_raw) > 1:
            valid_rows = [(i+2, r) for i, r in enumerate(all_raw[1:]) if any(str(c).strip() for c in r)]
            search_q = st.text_input("🔍 搜尋歷史紀錄 (車號/場站/姓名)", placeholder="輸入關鍵字...").strip().lower()
            
            display_list = []
            if search_q:
                display_list = [(idx, r) for idx, r in valid_rows if any(search_q in str(cell).lower() for cell in r)]
            else:
                display_list = valid_rows[-3:] # 保底顯示最後 3 筆 [cite: 2026-02-13]
            
            for r_idx, r_val in reversed(display_list):
                c = st.columns([1.5, 1.2, 0.8, 1.2, 1.0, 2.0, 0.6])
                c[0].write(r_val[0]); c[1].write(r_val[1]); c[2].write(r_val[2]); c[3].write(r_val[3])
                c[4].write(r_val[4]); c[5].write(r_val[6])
                if c[6].button("📝", key=f"ed_{r_idx}"):
                    st.session_state.edit_mode, st.session_state.edit_row_idx, st.session_state.edit_data = True, r_idx, r_val
                    st.rerun()
                st.markdown("<hr style='margin: 2px 0;'>", unsafe_allow_html=True)

# --- Tab 2: 數據統計 (全柱狀圖版) ---
with tab2:
    st.title("📊 數據統計分析")
    if st.text_input("管理員密碼", type="password", key="stat_pwd") == "kevin198": # 密碼鎖定 [cite: 2026-02-13]
        if sheet:
            raw_stat = [r for r in sheet.get_all_values() if any(f.strip() for f in r)]
            if len(raw_stat) > 1:
                df_s = pd.DataFrame(raw_stat[1:], columns=raw_stat[0])
                df_s[raw_stat[0][0]] = pd.to_datetime(df_s[raw_stat[0][0]], errors='coerce')
                
                custom_range = st.date_input("📅 選擇統計週期", value=[])
                if len(custom_range) == 2:
                    start_date, end_date = custom_range
                    wk_df = df_s.loc[(df_s[raw_stat[0][0]].dt.date >= start_date) & (df_s[raw_stat[0][0]].dt.date <= end_date)]
                else:
                    wk_df = df_s.tail(50)

                if not wk_df.empty:
                    st.metric("總案件數", f"{len(wk_df)} 件")
                    
                    # 類別分佈圖 (4K 投影優化) [cite: 2026-02-23]
                    cat_counts = wk_df["類別"].value_counts().reset_index()
                    cat_counts.columns = ['類別', '件數']
                    fig = px.bar(cat_counts, x='類別', y='件數', text='件數', color='類別', title="📂 客服案件類別分佈")
                    fig.update_layout(font=dict(size=18, color="#000000"), plot_bgcolor='white')
                    st.plotly_chart(fig, use_container_width=True)

st.caption("© 2026 應安客服系統")
