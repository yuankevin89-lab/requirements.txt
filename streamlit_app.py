import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import datetime
import pandas as pd
import pytz
import plotly.express as px

# --- 1. 頁面基本設定與專業樣式 ---
st.set_page_config(page_title="應安客服雲端登記系統", page_icon="📝", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display: none;}
    .block-container {padding-top: 2rem; padding-bottom: 1rem;}
    
    /* [功能] 標記變色樣式 */
    [data-testid="stElementContainer"]:has(input[type="checkbox"]:checked) {
        background-color: #e8f5e9 !important;
        border-radius: 8px;
        padding: 10px;
        transition: background-color 0.3s ease;
        border: 1px solid #c8e6c9;
    }
    
    /* [功能] 懸停預覽樣式 */
    .hover-text {
        cursor: help;
        color: #1f77b4;
        text-decoration: underline dotted;
        display: inline-block;
        width: 100%;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    </style>
    """, unsafe_allow_html=True)

tw_timezone = pytz.timezone('Asia/Taipei')

# --- 2. 初始設定與資料庫連線 ---
STATION_LIST = ["請選擇或輸入關鍵字搜尋", "華視光復", "華視電視台", "華視二", "華視三", "華視五", "文教一", "文教二", "文教三", "文教五", "文教六", "延吉場", "大安場", "信義大安", "樂業場", "四維場", "仁愛場", "濟南一", "濟南二", "松智場", "松勇二", "六合場", "統領場", "信義安和", "僑信場", "台北民生", "美麗華場", "基湖場", "北安場", "龍江場", "農安場", "民權西場", "承德場", "承德三", "大龍場", "延平北場", "雙連", "中山機車", "中山場", "南昌", "博愛", "金山", "金華", "詔安", "通化", "杭南一", "復興南", "逸仙", "興岩", "木柵", "泉州", "汀洲", "福州", "北平東", "水源", "重慶南", "西寧市場", "西園國宅", "復興北", "宏泰民生", "福善一", "石牌二", "中央北", "紅毛城", "三玉", "士林", "永平", "大龍峒社宅", "昆陽一", "洲子場", "環山", "文湖場", "民善場", "新明場", "德明研推", "東湖場", "東大門場", "其他(未登入場站)"]
STAFF_LIST = ["請選擇填單人", "宗哲", "美妞", "政宏", "文輝", "恩佳", "志榮", "阿錨", "子毅", "浚"]

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

tab1, tab2 = st.tabs(["📝 案件登記", "📊 數據統計分析"])

with tab1:
    st.title("📝 應安客服線上登記系統")
    now_ts = datetime.datetime.now(tw_timezone)
    
    if st.session_state.edit_mode:
        st.warning(f"⚠️ 【編輯模式】- 正在更新第 {st.session_state.edit_row_idx} 列紀錄")

    with st.form("my_form", clear_on_submit=True):
        d = st.session_state.edit_data if st.session_state.edit_mode else [""]*8
        f_dt = d[0] if st.session_state.edit_mode else now_ts.strftime("%Y-%m-%d %H:%M:%S")
        st.info(f"🕒 案件時間：{f_dt}")
        
        c1, c2 = st.columns(2)
        with c1:
            station_name = st.selectbox("場站名稱", options=STATION_LIST, index=STATION_LIST.index(d[1]) if d[1] in STATION_LIST else 0)
            caller_name = st.text_input("姓名", value=d[2])
        with c2:
            user_name = st.selectbox("填單人", options=STAFF_LIST, index=STAFF_LIST.index(d[7]) if d[7] in STAFF_LIST else 0, disabled=st.session_state.edit_mode)
            caller_phone = st.text_input("電話", value=d[3])
        
        c3, c4 = st.columns(2)
        with c3:
            category = st.selectbox("類別", options=["繳費機故障", "發票缺紙或卡紙", "無法找零", "身障優惠折抵", "其他"], index=["繳費機故障", "發票缺紙或卡紙", "無法找零", "身障優惠折抵", "其他"].index(d[5]) if d[5] in ["繳費機故障", "發票缺紙或卡紙", "無法找零", "身障優惠折抵", "其他"] else 4)
        with c4:
            car_num = st.text_input("車號", value=d[4])
        
        description = st.text_area("描述內容", value=d[6])
        
        btn_c1, btn_c2, btn_c3, _ = st.columns([1, 1, 1, 3])
        submit_btn = btn_c1.form_submit_button("更新紀錄" if st.session_state.edit_mode else "確認送出")
        if st.session_state.edit_mode:
            if btn_c2.form_submit_button("❌ 取消編輯"):
                st.session_state.edit_mode = False
                st.session_state.edit_data = [""]*8
                st.rerun()
        else:
            btn_c2.link_button("多元支付", "http://219.85.163.90:5010/")
        btn_c3.link_button("簡訊系統", "https://umc.fetnet.net/#/menu/login")

        if submit_btn:
            if user_name != "請選擇填單人" and station_name != "請選擇或輸入關鍵字搜尋":
                row = [f_dt, station_name, caller_name, caller_phone, car_num.upper(), category, description, user_name]
                if st.session_state.edit_mode:
                    sheet.update(f"A{st.session_state.edit_row_idx}:H{st.session_state.edit_row_idx}", [row])
                    st.session_state.edit_mode = False
                else:
                    sheet.append_row(row)
                st.rerun()
            else:
                st.error("請正確選擇填單人與場站")

    # --- 最近紀錄 (精確搜尋 + 8小時輪動) ---
    st.markdown("---")
    st.subheader("🔍 最近紀錄 (交班動態)")
    if sheet:
        all_raw = sheet.get_all_values()
        if len(all_raw) > 1:
            # 建立有效資料清單，排除空白列並記錄行索引
            valid_rows = []
            for i, r in enumerate(all_raw[1:]):
                if any(str(c).strip() for c in r):
                    valid_rows.append((i+2, r))
            
            search_q = st.text_input("🔍 搜尋歷史紀錄 (全欄位)", placeholder="輸入關鍵字...").strip().lower()
            
            eight_hrs_ago = (now_ts.replace(tzinfo=None)) - datetime.timedelta(hours=8)
            display_list = []
            
            if search_q:
                # 只有當欄位內容「真正」包含關鍵字時才加入，排除空格誤判
                for idx, r in valid_rows:
                    if any(search_q in str(cell).lower().strip() for cell in r if str(cell).strip()):
                        display_list.append((idx, r))
            else:
                for idx, r in valid_rows:
                    try:
                        dt = pd.to_datetime(r[0]).replace(tzinfo=None)
                        if dt >= eight_hrs_ago: display_list.append((idx, r))
                    except: continue
                if not display_list: display_list = valid_rows[-3:]

            if display_list:
                cols = st.columns([2, 1.5, 1.2, 2.5, 1, 0.8, 0.8])
                for col, t in zip(cols, ["日期/時間", "場站", "車號", "描述摘要", "填單人", "編輯", "標記"]):
                    col.markdown(f"**{t}**")
                st.markdown("<hr style='margin: 2px 0;'>", unsafe_allow_html=True)
                
                for r_idx, r_val in reversed(display_list):
                    with st.container():
                        c = st.columns([2, 1.5, 1.2, 2.5, 1, 0.8, 0.8])
                        c[0].write(r_val[0]); c[1].write(r_val[1]); c[2].write(r_val[4])
                        clean_d = r_val[6].replace('\n', ' ').replace('"', '&quot;').replace("'", "&apos;")
                        short_d = f"{clean_d[:12]}..." if len(clean_d) > 12 else clean_d
                        c[3].markdown(f'<div class="hover-text" title="{clean_d}">{short_d}</div>', unsafe_allow_html=True)
                        c[4].write(r_val[7])
                        if c[5].button("📝", key=f"ed_{r_idx}"):
                            st.session_state.edit_mode, st.session_state.edit_row_idx, st.session_state.edit_data = True, r_idx, r_val
                            st.rerun()
                        c[6].checkbox(" ", key=f"chk_{r_idx}", label_visibility="collapsed")
                        st.markdown("<hr style='margin: 2px 0;'>", unsafe_allow_html=True)
            else:
                st.info("查無符合資料")

# --- Tab 2: 數據統計 (已修正 NameError) ---
with tab2:
    st.title("📊 數據統計與分析 (自動週報)")
    if st.text_input("管理員密碼", type="password", key="stat_pwd") == "kevin198":
        if sheet:
            raw_stat = [r for r in sheet.get_all_values() if any(f.strip() for f in r)]
            if len(raw_stat) > 1:
                hdr = raw_stat[0]
                df_s = pd.DataFrame(raw_stat[1:], columns=hdr)
                df_s[hdr[0]] = pd.to_datetime(df_s[hdr[0]], errors='coerce')
                df_s = df_s.dropna(subset=[hdr[0]])
                
                today = datetime.datetime.now(tw_timezone).date()
                mon = today - datetime.timedelta(days=today.weekday() + 7)
                sun = mon + datetime.timedelta(days=6) # 修正: 原本是 Mon+6
                
                wk_df = df_s.loc[(df_s[hdr[0]].dt.date >= mon) & (df_s[hdr[0]].dt.date <= sun)]

                if not wk_df.empty:
                    st.success(f"📅 統計週期：{mon} ~ {sun}")
                    g1, g2 = st.columns(2)
                    with g1:
                        fig1 = px.pie(wk_df, names=hdr[5], title="📂 類別佔比分析", hole=0.4)
                        fig1.update_traces(textinfo='label+percent', textposition='outside')
                        st.plotly_chart(fig1, use_container_width=True)
                    with g2:
                        fig2 = px.pie(wk_df, names=hdr[1], title="🏢 場站佔比分析", hole=0.4)
                        fig2.update_traces(textinfo='label+percent', textposition='outside')
                        st.plotly_chart(fig2, use_container_width=True)
                else: st.info("本週期內尚無資料。")

st.caption("© 2026 應安客服系統 - 2/16 全功能鎖定穩定版")
