import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import datetime
import pandas as pd
import pytz
import plotly.express as px  # 用於更美觀的圖表

# --- 1. 頁面基本設定與樣式淨化 ---
st.set_page_config(page_title="應安客服線上登記系統", page_icon="📝", layout="wide")

# 隱藏選單並加入「勾選變色」的 CSS 邏輯
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            .stAppDeployButton {display: none;}
            .block-container {padding-top: 2rem; padding-bottom: 1rem;}
            
            /* 標記勾選後的行變色邏輯 (利用 Streamlit 的 container 結構) */
            div[data-testid="stVerticalBlock"] > div:has(input[type="checkbox"]:checked) {
                background-color: #e8f5e9; /* 淺綠色背景 */
                border-radius: 5px;
            }
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

tw_timezone = pytz.timezone('Asia/Taipei')

# --- 2. 資料清單設定 ---
STATION_LIST = ["請選擇或輸入關鍵字搜尋", "華視光復", "華視電視台", "華視二", "華視三", "華視五", "文教一", "文教二", "文教三", "文教五", "文教六", "延吉場", "大安場", "信義大安", "樂業場", "四維場", "仁愛場", "濟南一", "濟南二", "松智場", "松勇二", "六合場", "統領場", "信義安和", "僑信場", "台北民生", "美麗華場", "基湖場", "北安場", "龍江場", "農安場", "民權西場", "承德場", "承德三", "大龍場", "延平北場", "雙連", "中山機車", "中山場", "南昌", "博愛", "金山", "金華", "詔安", "通化", "杭南一", "復興南", "逸仙", "興岩", "木柵", "泉州", "汀洲", "福州", "北平東", "水源", "重慶南", "西寧市場", "西園國宅", "復興北", "宏泰民生", "福善一", "石牌二", "中央北", "紅毛城", "三玉", "士林", "永平", "大龍峒社宅", "昆陽一", "洲子場", "環山", "文湖場", "民善場", "新明場", "德明研推", "東湖場", "舊宗社宅", "秀山機車", "景平", "環狀A", "土城中華場", "板橋光正", "合宜場", "土城裕民", "中央二", "中央三", "板橋文化", "同安", "佳音竹林", "青潭國小", "林口文化", "秀峰場", "興南場", "中和莊敬", "三重永福", "徐匯場", "蘆洲保和場", "蘆洲三民", "榮華場", "富貴場", "鄉長二", "汐止忠孝", "新台五路", "蘆竹場", "龜山興富", "竹東長春", "竹南中山", "銅鑼停一", "台中黎明", "後龍", "台中復興", "文心場", "大和屋一場", "大和屋二場", "北港場", "西螺", "虎尾", "民德", "衛民場", "衛民二場", "台南北門場", "台南永福", "台南國華", "台南民權", "善化", "仁德", "台南中華場", "致穩", "台南康樂場", "金財神", "蘭井", "友愛場", "佳音西園", "中華信義", "敦南場", "中華北門場", "東大門場", "其他(未登入場站)"]
STAFF_LIST = ["請選擇填單人", "宗哲", "美妞", "政宏", "文輝", "恩佳", "志榮", "阿錨", "子毅", "浚"]

# --- 3. Google Sheets 連線 ---
def init_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds_dict = st.secrets["google_sheets"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"連線失敗: {e}")
        return None

client = init_connection()
if client:
    sheet = client.open("客服作業表").sheet1
    conn_success = True
else:
    conn_success = False

# --- 4. 初始化 Session State ---
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False
    st.session_state.edit_row_idx = None
    st.session_state.edit_data = [""] * 8

# --- 5. UI 分頁 ---
tab1, tab2 = st.tabs(["📝 案件登記", "📊 數據統計"])

with tab1:
    st.title("📝 應安客服線上登記系統")
    now_ts = datetime.datetime.now(tw_timezone)
    
    if st.session_state.edit_mode:
        st.warning(f"⚠️ 【編輯模式】- 修改第 {st.session_state.edit_row_idx} 列紀錄")

    # (案件登記表單內容保持不變，略過以節省空間，請沿用上一版)
    # ... 原本的 st.form 邏輯 ...
    with st.form("my_form", clear_on_submit=True):
        d = st.session_state.edit_data if st.session_state.edit_mode else [""]*8
        f_dt = d[0] if st.session_state.edit_mode else now_ts.strftime("%Y-%m-%d %H:%M:%S")
        st.info(f"🕒 案件時間：{f_dt}")
        col1, col2 = st.columns(2)
        with col1:
            s_val = d[1] if st.session_state.edit_mode else ""
            station_name = st.selectbox("場站名稱", options=STATION_LIST, index=STATION_LIST.index(s_val) if s_val in STATION_LIST else 0)
            caller_name = st.text_input("姓名 (來電人)", value=d[2] if st.session_state.edit_mode else "")
        with col2:
            u_val = d[7] if st.session_state.edit_mode else ""
            user_name = st.selectbox("填單人", options=STAFF_LIST, index=STAFF_LIST.index(u_val) if u_val in STAFF_LIST else 0, disabled=st.session_state.edit_mode)
            caller_phone = st.text_input("電話", value=d[3] if st.session_state.edit_mode else "")
        col3, col4 = st.columns(2)
        with col3:
            cat_list = ["繳費機故障", "發票缺紙或卡紙", "無法找零", "身障優惠折抵", "其他"]
            c_val = d[5] if st.session_state.edit_mode else "其他"
            category = st.selectbox("來電類別", options=cat_list, index=cat_list.index(c_val) if c_val in cat_list else 4)
        with col4:
            car_num = st.text_input("車號", value=d[4] if st.session_state.edit_mode else "")
        description = st.text_area("描述 (詳細過程)", value=d[6] if st.session_state.edit_mode else "")
        btn_col1, btn_col2, btn_col3, btn_col4 = st.columns([1, 1, 1, 3]) 
        with btn_col1:
            submit = st.form_submit_button("更新紀錄" if st.session_state.edit_mode else "確認送出")
        with btn_col2: st.link_button("多元支付", "http://219.85.163.90:5010/")
        with btn_col3: st.link_button("簡訊系統", "https://umc.fetnet.net/#/menu/login")

        if submit:
            if user_name != "請選擇填單人" and station_name != "請選擇或輸入關鍵字搜尋":
                row_content = [f_dt, station_name, caller_name, caller_phone, car_num.upper(), category, description, user_name]
                try:
                    if st.session_state.edit_mode:
                        sheet.update(f"A{st.session_state.edit_row_idx}:H{st.session_state.edit_row_idx}", [row_content])
                        st.session_state.edit_mode = False
                    else:
                        sheet.append_row(row_content)
                    st.rerun()
                except Exception as e: st.error(f"錯誤: {e}")

    # --- 🔍 歷史紀錄與交班動態 ---
    st.markdown("---")
    st.subheader("🔍 歷史紀錄與交班動態")
    try:
        data = sheet.get_all_values()
        if len(data) > 1:
            rows = data[1:]
            search_query = st.text_input("🔍 搜尋歷史紀錄")
            display_list = []
            now_naive = now_ts.replace(tzinfo=None)
            eight_ago = now_naive - datetime.timedelta(hours=8)

            for i, r in enumerate(rows):
                dt_val = pd.to_datetime(r[0], errors='coerce').replace(tzinfo=None)
                if search_query:
                    if any(search_query.lower() in str(cell).lower() for cell in r): display_list.append((i+2, r))
                elif dt_val and dt_val >= eight_ago: display_list.append((i+2, r))

            if display_list:
                h1, h2, h3, h4, h5, h6, h7 = st.columns([2, 1.5, 1.2, 2.5, 1, 0.8, 0.8])
                h1.write("**時間**"); h2.write("**場站**"); h3.write("**車號**"); h4.write("**描述**"); h5.write("**填單人**"); h6.write("**編輯**"); h7.write("**標記**")
                
                for r_num, r_data in reversed(display_list):
                    with st.container(): # 這個 container 會被上面的 CSS 選中，勾選時變色
                        c1, c2, c3, c4, c5, c6, c7 = st.columns([2, 1.5, 1.2, 2.5, 1, 0.8, 0.8])
                        c1.write(r_data[0]); c2.write(r_data[1]); c3.write(r_data[4]); c4.write(f"{r_data[6][:20]}..."); c5.write(r_data[7])
                        if c6.button("📝", key=f"ed_{r_num}"):
                            st.session_state.edit_mode=True; st.session_state.edit_row_idx=r_num; st.session_state.edit_data=r_data; st.rerun()
                        c7.checkbox(" ", key=f"chk_{r_num}", label_visibility="collapsed")
                        st.markdown("<hr style='margin: 2px 0;'>", unsafe_allow_html=True)
    except: st.error("載入失敗")

# --- 📊 Tab 2: 數據統計 (功能擴充) ---
with tab2:
    st.title("📊 數據統計與分析")
    if st.text_input("管理員密碼", type="password") == "kevin198":
        if conn_success:
            raw_data = sheet.get_all_values()
            if len(raw_data) > 1:
                df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
                
                # 統計指標列
                m1, m2, m3 = st.columns(3)
                m1.metric("總登記件數", len(df))
                m2.metric("今日件數", len(df[df.iloc[:,0].str.contains(now_ts.strftime("%Y-%m-%d"), na=False)]))
                m3.metric("場站總數", df.iloc[:,1].nunique())

                st.markdown("---")
                
                # 圖表列 1
                g1, g2 = st.columns(2)
                with g1:
                    st.subheader("👤 填單人員案件量")
                    st.bar_chart(df.iloc[:, 7].value_counts())
                
                with g2:
                    st.subheader("📂 來電類別佔比")
                    # 使用 Plotly 畫圓餅圖
                    cat_counts = df.iloc[:, 5].value_counts().reset_index()
                    cat_counts.columns = ['類別', '次數']
                    fig_pie = px.pie(cat_counts, values='次數', names='類別', hole=0.3)
                    st.plotly_chart(fig_pie, use_container_width=True)

                # 圖表列 2
                st.subheader("🏢 場站案件量排行 (前10名)")
                station_counts = df.iloc[:, 1].value_counts().head(10).reset_index()
                station_counts.columns = ['場站', '件數']
                fig_bar = px.bar(station_counts, x='件數', y='場站', orientation='h', color='件數', color_continuous_scale='Viridis')
                st.plotly_chart(fig_bar, use_container_width=True)
                
                st.markdown("---")
                st.subheader("📋 完整原始資料檢視")
                st.dataframe(df.iloc[::-1], use_container_width=True)

st.caption("© 2026 應安客服系統 - 2/16 數據強化版")
