import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import datetime
import pandas as pd
import pytz
import plotly.express as px

# --- 1. 頁面基本設定 ---
st.set_page_config(page_title="應安客服線上登記系統", page_icon="📝", layout="wide")

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            .stAppDeployButton {display: none;}
            .block-container {padding-top: 2rem; padding-bottom: 1rem;}
            div[data-testid="stVerticalBlock"] > div:has(input[type="checkbox"]:checked) {
                background-color: #e8f5e9 !important;
                border-radius: 8px;
                padding: 10px;
                transition: background-color 0.3s ease;
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

# --- Tab 1 登記功能 (邏輯不變) ---
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
        description = st.text_area("描述", value=d[6])
        btn_c1, btn_c2, btn_c3, _ = st.columns([1, 1, 1, 3])
        if btn_c1.form_submit_button("更新紀錄" if st.session_state.edit_mode else "確認送出"):
            if user_name != "請選擇填單人" and station_name != "請選擇或輸入關鍵字搜尋":
                row = [f_dt, station_name, caller_name, caller_phone, car_num.upper(), category, description, user_name]
                if st.session_state.edit_mode:
                    sheet.update(f"A{st.session_state.edit_row_idx}:H{st.session_state.edit_row_idx}", [row])
                    st.session_state.edit_mode = False
                else: sheet.append_row(row)
                st.rerun()
        btn_c2.link_button("多元支付", "http://219.85.163.90:5010/")
        btn_c3.link_button("簡訊系統", "https://umc.fetnet.net/#/menu/login")

    # 歷史紀錄略過... (程式碼中包含搜尋與標記功能)
    st.markdown("---")
    st.subheader("🔍 歷史紀錄與交班動態")
    if sheet:
        data = sheet.get_all_values()
        if len(data) > 1:
            rows = data[1:]
            search = st.text_input("🔍 搜尋歷史紀錄")
            eight_ago = (now_ts.replace(tzinfo=None)) - datetime.timedelta(hours=8)
            display = []
            for i, r in enumerate(rows):
                dt = pd.to_datetime(r[0], errors='coerce').replace(tzinfo=None)
                if search:
                    if any(search.lower() in str(x).lower() for x in r): display.append((i+2, r))
                elif dt and dt >= eight_ago: display.append((i+2, r))
            if display:
                cols = st.columns([2, 1.5, 1.2, 2.5, 1, 0.8, 0.8])
                for col, title in zip(cols, ["日期/時間", "場站", "車號", "描述摘要", "填單人", "編輯", "標記"]): col.markdown(f"**{title}**")
                for r_idx, r_val in reversed(display):
                    with st.container():
                        c = st.columns([2, 1.5, 1.2, 2.5, 1, 0.8, 0.8])
                        c[0].write(r_val[0]); c[1].write(r_val[1]); c[2].write(r_val[4]); c[3].write(f"{r_val[6][:20]}..."); c[4].write(r_val[7])
                        if c[5].button("📝", key=f"btn_{r_idx}"):
                            st.session_state.edit_mode, st.session_state.edit_row_idx, st.session_state.edit_data = True, r_idx, r_val
                            st.rerun()
                        c[6].checkbox(" ", key=f"chk_{r_idx}", label_visibility="collapsed")
                        st.markdown("<hr style='margin: 2px 0;'>", unsafe_allow_html=True)

# --- 📊 Tab 2: 數據統計分析 (修正欄位匹配問題) ---
with tab2:
    st.title("📊 數據統計與分析 (週報)")
    if st.text_input("管理員密碼", type="password") == "kevin198":
        if sheet:
            all_raw = sheet.get_all_values()
            if len(all_raw) > 1:
                # 建立 DataFrame，明確指定第一行為欄位標題
                full_df = pd.DataFrame(all_raw[1:], columns=all_raw[0])
                
                # 清洗第一欄「日期/時間」，並剔除無效資料
                date_col_name = full_df.columns[0]
                full_df[date_col_name] = pd.to_datetime(full_df[date_col_name], errors='coerce')
                full_df = full_df.dropna(subset=[date_col_name])

                # --- 關鍵修正：確保抓取正確標題名稱的數據 ---
                col_category = "類別" if "類別" in full_df.columns else full_df.columns[5]
                col_station = "場站名稱" if "場站名稱" in full_df.columns else full_df.columns[1]

                # 計算上一週週期 (週一至週日)
                today = datetime.datetime.now(tw_timezone).date()
                last_monday = today - datetime.timedelta(days=today.weekday() + 7)
                last_sunday = last_monday + datetime.timedelta(days=6)
                mask = (full_df[date_col_name].dt.date >= last_monday) & (full_df[date_col_name].dt.date <= last_sunday)
                df = full_df.loc[mask].copy()

                st.success(f"📅 **統計週期：{last_monday} (一) ~ {last_sunday} (日)**")
                
                chart_config = {'displaylogo': False, 'modeBarButtonsToAdd': ['downloadImage'], 
                                'toImageButtonOptions': {'format': 'png', 'filename': f'應安統計_{last_monday}', 'scale': 2}}

                if not df.empty:
                    st.markdown("---")
                    g1, g2 = st.columns(2)
                    with g1:
                        st.subheader("📂 類別佔比")
                        # 使用變數鎖定標題名稱為「類別」的數據
                        fig1 = px.pie(df, names=col_category, hole=0.4, color_discrete_sequence=px.colors.qualitative.Safe)
                        st.plotly_chart(fig1, use_container_width=True, config=chart_config)
                    with g2:
                        st.subheader("🏢 場站佔比")
                        # 使用變數鎖定標題名稱為「場站名稱」的數據
                        fig2 = px.pie(df, names=col_station, hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                        st.plotly_chart(fig2, use_container_width=True, config=chart_config)
                    
                    st.markdown("---")
                    r1, r2 = st.columns(2)
                    with r1:
                        st.subheader("📊 類別排行 (Top 10)")
                        cat_top = df[col_category].value_counts().head(10).reset_index()
                        cat_top.columns = ['類別', '件數']
                        fig3 = px.bar(cat_top, x='件數', y='類別', orientation='h', color='件數', color_continuous_scale='Reds')
                        st.plotly_chart(fig3, use_container_width=True, config=chart_config)
                    with r2:
                        st.subheader("🏢 場站排行 (Top 10)")
                        st_top = df[col_station].value_counts().head(10).reset_index()
                        st_top.columns = ['場站名稱', '件數']
                        fig4 = px.bar(st_top, x='件數', y='場站名稱', orientation='h', color='件數', color_continuous_scale='Blues')
                        st.plotly_chart(fig4, use_container_width=True, config=chart_config)
                    
                    st.write("📋 **本週期明細**")
                    st.dataframe(df.sort_values(by=date_col_name, ascending=False), use_container_width=True)
                else:
                    st.warning("⚠️ 此週期內尚無登記資料。")

st.caption("© 2026 應安客服系統 - 2/16 標題鎖定精準版")
