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
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)
tw_timezone = pytz.timezone('Asia/Taipei')

# --- 2. 資料清單 (省略以簡化) ---
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
    # (此部分保持登記功能正常運作，略過細節)
    st.title("📝 應安客服線上登記系統")
    now_ts = datetime.datetime.now(tw_timezone)
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
        if st.form_submit_button("確認送出"):
            if user_name != "請選擇填單人" and station_name != "請選擇或輸入關鍵字搜尋":
                row = [f_dt, station_name, caller_name, caller_phone, car_num.upper(), category, description, user_name]
                sheet.append_row(row)
                st.rerun()

# --- 📊 Tab 2: 數據統計 (暴力偵測修正版) ---
with tab2:
    st.title("📊 數據統計分析")
    if st.text_input("管理員密碼", type="password") == "kevin198":
        if sheet:
            # 獲取所有原始資料
            raw_data = sheet.get_all_values()
            if len(raw_data) > 1:
                # 1. 暴力搜尋標題列 (防止第一列不是標題的情況)
                header_idx = 0
                for i, row in enumerate(raw_data):
                    if "場站名稱" in row or "類別" in row:
                        header_idx = i
                        break
                
                # 2. 建立 DataFrame 並修剪標題空格
                cols = [str(c).strip() for c in raw_data[header_idx]]
                full_df = pd.DataFrame(raw_data[header_idx+1:], columns=cols)
                
                # 3. 排除全空行並動態對應欄位
                full_df = full_df.loc[:, ~full_df.columns.duplicated()] # 防止重複標題
                
                # 偵測關鍵欄位名稱 (模糊匹配)
                col_date = next((c for c in full_df.columns if "時間" in c or "日期" in c), full_df.columns[0])
                col_st = next((c for c in full_df.columns if "場站" in c), "場站名稱")
                col_cat = next((c for c in full_df.columns if "類別" in c), "類別")

                # 4. 日期處理
                full_df[col_date] = pd.to_datetime(full_df[col_date], errors='coerce')
                full_df = full_df.dropna(subset=[col_date])

                # 5. 週期過濾 (上週一至週日)
                today = datetime.datetime.now(tw_timezone).date()
                last_monday = today - datetime.timedelta(days=today.weekday() + 7)
                last_sunday = last_monday + datetime.timedelta(days=6)
                mask = (full_df[col_date].dt.date >= last_monday) & (full_df[col_date].dt.date <= last_sunday)
                df = full_df.loc[mask].copy()

                st.success(f"📅 統計週期：{last_monday} ~ {last_sunday}")
                
                if not df.empty:
                    st.markdown("---")
                    c1, c2 = st.columns(2)
                    with c1:
                        st.subheader("📂 類別佔比")
                        # 再次確認該欄位數據不為空
                        df_cat = df[df[col_cat] != ""].copy()
                        fig1 = px.pie(df_cat, names=col_cat, hole=0.4, color_discrete_sequence=px.colors.qualitative.Safe)
                        st.plotly_chart(fig1, use_container_width=True)
                    with c2:
                        st.subheader("🏢 場站佔比")
                        df_st = df[df[col_st] != ""].copy()
                        fig2 = px.pie(df_st, names=col_st, hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                        st.plotly_chart(fig2, use_container_width=True)
                    
                    st.markdown("---")
                    st.subheader(f"📊 數據明細 (共 {len(df)} 筆)")
                    st.dataframe(df[[col_date, col_st, col_cat, full_df.columns[4]]].sort_values(by=col_date, ascending=False), use_container_width=True)
                else:
                    st.warning("⚠️ 此週期內無資料，請確認 Google Sheets 中的日期格式。")
