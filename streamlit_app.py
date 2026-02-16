import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import datetime
import pandas as pd
import pytz
import plotly.express as px

# --- 1. 頁面基本設定與樣式 ---
st.set_page_config(page_title="應安客服雲端登記系統", page_icon="📝", layout="wide")

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            .stAppDeployButton {display: none;}
            .block-container {padding-top: 2rem; padding-bottom: 1rem;}
            
            /* 標記變色邏輯：僅限被勾選的單一行容器 */
            [data-testid="stElementContainer"]:has(input[type="checkbox"]:checked) {
                background-color: #e8f5e9 !important;
                border-radius: 8px;
                padding: 10px;
                transition: background-color 0.3s ease;
                border: 1px solid #c8e6c9;
            }
            
            /* 懸停預覽樣式：藍色底線提示 */
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
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

tw_timezone = pytz.timezone('Asia/Taipei')

# --- 2. 資料清單設定 ---
STATION_LIST = ["請選擇或輸入關鍵字搜尋", "華視光復", "華視電視台", "華視二", "華視三", "華視五", "文教一", "文教二", "文教三", "文教五", "文教六", "延吉場", "大安場", "信義大安", "樂業場", "四維場", "仁愛場", "濟南一", "濟南二", "松智場", "松勇二", "六合場", "統領場", "信義安和", "僑信場", "台北民生", "美麗華場", "基湖場", "北安場", "龍江場", "農安場", "民權西場", "承德場", "承德三", "大龍場", "延平北場", "雙連", "中山機車", "中山場", "南昌", "博愛", "金山", "金華", "詔安", "通化", "杭南一", "復興南", "逸仙", "興岩", "木柵", "泉州", "汀洲", "福州", "北平東", "水源", "重慶南", "西寧市場", "西園國宅", "復興北", "宏泰民生", "福善一", "石牌二", "中央北", "紅毛城", "三玉", "士林", "永平", "大龍峒社宅", "昆陽一", "洲子場", "環山", "文湖場", "民善場", "新明場", "德明研推", "東湖場", "舊宗社宅", "秀山機車", "景平", "環狀A", "土城中華場", "板橋光正", "合宜場", "土城裕民", "中央二", "中央三", "板橋文化", "同安", "佳音竹林", "青潭國小", "林口文化", "秀峰場", "興南場", "中和莊敬", "三重永福", "徐匯場", "蘆洲保和場", "蘆洲三民", "榮華場", "富貴場", "鄉長二", "汐止忠孝", "新台五路", "蘆竹場", "龜山興富", "竹東長春", "竹南中山", "銅鑼停一", "台中黎明", "後龍", "台中復興", "文心場", "大和屋一場", "大和屋二場", "北港場", "西螺", "虎尾", "民德", "衛民場", "衛民二場", "台南北門場", "台南永福", "台南國華", "台南民權", "善化", "仁德", "台南中華場", "致穩", "台南康樂場", "金財神", "蘭井", "友愛場", "佳音西園", "中華信義", "敦南場", "中華北門場", "東大門場", "其他(未登入場站)"]
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
    
    # --- 表單填寫區 ---
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
        if btn_c1.form_submit_button("更新紀錄" if st.session_state.edit_mode else "確認送出"):
            if user_name != "請選擇填單人" and station_name != "請選擇或輸入關鍵字搜尋":
                row = [f_dt, station_name, caller_name, caller_phone, car_num.upper(), category, description, user_name]
                if st.session_state.edit_mode:
                    sheet.update(f"A{st.session_state.edit_row_idx}:H{st.session_state.edit_row_idx}", [row]); st.session_state.edit_mode = False
                else: sheet.append_row(row)
                st.rerun()
        btn_c2.link_button("多元支付", "http://219.85.163.90:5010/")
        btn_c3.link_button("簡訊系統", "https://umc.fetnet.net/#/menu/login")

    # --- 歷史紀錄區 (全功能智慧過濾) ---
    st.markdown("---")
    st.subheader("🔍 最近紀錄 (交班動態)")
    if sheet:
        data_raw = sheet.get_all_values()
        if len(data_raw) > 1:
            rows = data_raw[1:]
            
            # 功能 1：關鍵字搜尋框
            search_query = st.text_input("🔍 搜尋紀錄 (車號、場站、姓名、類別)", placeholder="輸入關鍵字...")
            
            # 功能 2：智慧過濾邏輯
            eight_hours_ago = (now_ts.replace(tzinfo=None)) - datetime.timedelta(hours=8)
            display_list = []
            
            if search_query:
                # 搜尋模式：顯示匹配的所有歷史紀錄
                display_list = [(i+2, r) for i, r in enumerate(rows) if any(search_query.lower() in str(x).lower() for x in r)]
            else:
                # 交班模式：顯示 8 小時內
                for i, r in enumerate(rows):
                    try:
                        dt = pd.to_datetime(r[0]).replace(tzinfo=None)
                        if dt >= eight_hours_ago:
                            display_list.append((i+2, r))
                    except: continue
                # 智慧顯示：若 8 小時內無紀錄，保底最後 3 筆
                if not display_list:
                    display_list = [(i+2, r) for i, r in list(enumerate(rows))[-3:]]

            if display_list:
                cols = st.columns([2, 1.5, 1.2, 2.5, 1, 0.8, 0.8])
                header_labels = ["日期/時間", "場站", "車號", "描述摘要", "填單人", "編輯", "標記"]
                for col, title in zip(cols, header_labels): col.markdown(f"**{title}**")
                st.markdown("<hr style='margin: 2px 0; border: 1px solid #ddd;'>", unsafe_allow_html=True)
                
                for r_idx, r_val in reversed(display_list):
                    with st.container():
                        c = st.columns([2, 1.5, 1.2, 2.5, 1, 0.8, 0.8])
                        c[0].write(r_val[0])
                        c[1].write(r_val[1])
                        c[2].write(r_val[4])
                        
                        # 功能 3：懸停預覽
                        clean_desc = r_val[6].replace('\n', ' ').replace('"', '&quot;').replace("'", "&apos;")
                        short_desc = f"{clean_desc[:12]}..." if len(clean_desc) > 12 else clean_desc
                        c[3].markdown(f'<div class="hover-text" title="{clean_desc}">{short_desc}</div>', unsafe_allow_html=True)
                        
                        c[4].write(r_val[7])
                        # 功能 4：編輯功能
                        if c[5].button("📝", key=f"edit_{r_idx}"):
                            st.session_state.edit_mode, st.session_state.edit_row_idx, st.session_state.edit_data = True, r_idx, r_val
                            st.rerun()
                        # 功能 5：標記變色
                        c[6].checkbox(" ", key=f"check_{r_idx}", label_visibility="collapsed")
                        st.markdown("<hr style='margin: 2px 0;'>", unsafe_allow_html=True)

# --- Tab 2: 數據統計分析 (圖表修正版) ---
with tab2:
    st.title("📊 數據統計與分析 (自動週報)")
    if st.text_input("管理員密碼", type="password", key="stat_pwd") == "kevin198":
        if sheet:
            all_raw = sheet.get_all_values()
            if len(all_raw) > 1:
                headers = all_raw[0]
                df_stat = pd.DataFrame(all_raw[1:], columns=headers)
                df_stat[headers[0]] = pd.to_datetime(df_stat[headers[0]], errors='coerce')
                df_stat = df_stat.dropna(subset=[headers[0]])
                
                today = datetime.datetime.now(tw_timezone).date()
                last_monday = today - datetime.timedelta(days=today.weekday() + 7)
                last_sunday = last_monday + datetime.timedelta(days=6)
                week_df = df_stat[(df_stat[headers[0]].dt.date >= last_monday) & (df_stat[headers[0]].dt.date <= last_sunday)]

                if not week_df.empty:
                    st.success(f"📅 統計週期：{last_monday} (一) ~ {last_sunday} (日)")
                    c1, c2 = st.columns(2)
                    with c1:
                        st.subheader("📂 類別佔比分析")
                        fig1 = px.pie(week_df, names=headers[5], hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                        fig1.update_traces(textinfo='label+percent', textposition='outside')
                        st.plotly_chart(fig1, use_container_width=True)
                    with c2:
                        st.subheader("🏢 場站佔比分析")
                        fig2 = px.pie(week_df, names=headers[1], hole=0.4, color_discrete_sequence=px.colors.qualitative.Safe)
                        fig2.update_traces(textinfo='label+percent', textposition='outside')
                        st.plotly_chart(fig2, use_container_width=True)
                else: st.info("此週期內尚無數據。")

st.caption("© 2026 應安客服系統 - 2/16 全功能基準版")
