import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import datetime
import pandas as pd
import pytz

# --- 1. 頁面基本設定 ---
st.set_page_config(page_title="應安客服線上登記系統", page_icon="📝", layout="wide")
tw_timezone = pytz.timezone('Asia/Taipei')

# --- 2. 資料清單設定 ---
STATION_LIST = [
    "請選擇或輸入關鍵字搜尋", 
    "華視光復", "華視電視台", "華視二", "華視三", "華視五", "文教一", "文教二", "文教三", "文教五", "文教六", 
    "延吉場", "大安場", "信義大安", "樂業場", "四維場", "仁愛場", "濟南一", "濟南二", "松智場", "松勇二", "六合場", 
    "統領場", "信義安和", "僑信場", "台北民生", "美麗華場", "基湖場", "北安場", "龍江場", "農安場", "民權西場", 
    "承德場", "承德三", "大龍場", "延平北場", "雙連", "中山機車", "中山場", "南昌", "博愛", "金山", "金華", 
    "詔安", "通化", "杭南一", "復興南", "逸仙", "興岩", "木柵", "泉州", "汀洲", "福州", "北平東", "水源", 
    "重慶南", "西寧市場", "西園國宅", "復興北", "宏泰民生", "福善一", "石牌二", "中央北", "紅毛城", "三玉", 
    "士林", "永平", "大龍峒社宅", "昆陽一", "洲子場", "環山", "文湖場", "民善場", "新明場", "德明研推", 
    "東湖場", "舊宗社宅", "秀山機車", "景平", "環狀A", "土城中華場", "板橋光正", "合宜場", "土城裕民", 
    "中央二", "中央三", "板橋文化", "同安", "佳音竹林", "青潭國小", "林口文化", "秀峰場", "興南場", 
    "中和莊敬", "三重永福", "徐匯場", "蘆洲保和場", "蘆洲三民", "榮華場", "富貴場", "鄉長二", "汐止忠孝", 
    "新台五路", "蘆竹場", "龜山興富", "竹東長春", "竹南中山", "銅鑼停一", "台中黎明", "後龍", "台中復興", 
    "文心場", "大和屋一場", "大和屋二場", "北港場", "西螺", "虎尾", "民德", "衛民場", "衛民二場", 
    "台南北門場", "台南永福", "台南國華", "台南民權", "善化", "仁德", "台南中華場", "致穩", "台南康樂場", 
    "金財神", "蘭井", "友愛場", "佳音西園", "中華信義", "敦南場", "中華北門場", "東大門場",
    "其他(未登入場站)" 
]
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

# --- 4. UI 分頁功能 ---
tab1, tab2 = st.tabs(["📝 案件登記", "📊 數據統計"])

with tab1:
    st.title("📝 應安客服線上登記系統")
    now_ts = datetime.datetime.now(tw_timezone)
    dt_str = now_ts.strftime("%Y-%m-%d %H:%M:%S")

    if conn_success:
        # 【登記表單】
        with st.form("my_form", clear_on_submit=True):
            st.info(f"🕒 當前登記時間：{dt_str}")
            col1, col2 = st.columns(2)
            with col1:
                station_name = st.selectbox("場站名稱 (搜尋並點選)", options=STATION_LIST)
                caller_name = st.text_input("姓名 (來電人)")
            with col2:
                user_name = st.selectbox("填單人 (員工姓名)", options=STAFF_LIST)
                caller_phone = st.text_input("電話")
            
            col3, col4 = st.columns(2)
            with col3:
                category = st.selectbox("來電類別", ["繳費機故障", "發票缺紙或卡紙", "無法找零", "身障優惠折抵", "其他"])
            with col4:
                car_num = st.text_input("車號")
            
            description = st.text_area("描述 (詳細過程)")
            
            btn_col1, btn_col2, btn_col3, btn_col4 = st.columns([1, 1, 1, 3]) 
            with btn_col1:
                submit = st.form_submit_button("確認送出")
            with btn_col2:
                st.link_button("多元支付", "http://219.85.163.90:5010/")
            with btn_col3:
                st.link_button("簡訊系統", "https://umc.fetnet.net/#/menu/login")

            if submit:
                if user_name != "請選擇填單人" and station_name != "請選擇或輸入關鍵字搜尋":
                    try:
                        sheet.append_row([dt_str, station_name, caller_name, caller_phone, car_num.upper(), category, description, user_name])
                        st.success("✅ 資料已成功送出！")
                        st.rerun()
                    except Exception as e:
                        st.error(f"儲存失敗：{e}")
                else:
                    st.warning("⚠️ 請填寫必填欄位 (填單人與場站)")

        # --- 🔍 核心功能：8 小時輪動動態 + 關鍵字搜尋 ---
        st.markdown("---")
        st.subheader("🔍 歷史紀錄與交班動態")
        
        try:
            raw_data = sheet.get_all_values()
            if len(raw_data) > 1:
                df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
                
                # 時間預處理：強制轉換為不帶時區的時間格式以便比對
                df['dt_temp'] = pd.to_datetime(df.iloc[:, 0], errors='coerce').dt.tz_localize(None)
                
                search_query = st.text_input("🔍 關鍵字查詢", placeholder="輸入車號、電話、姓名... (留空顯示最近 8 小時紀錄)")
                
                if search_query:
                    # 模式 A：全域搜尋
                    mask = df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)
                    display_df = df[mask]
                    st.write(f"🔎 找到 {len(display_df)} 筆與 **{search_query}** 相關的紀錄：")
                else:
                    # 模式 B：8 小時內動態顯示
                    # 取得目前台灣時間並去除時區資訊
                    eight_hours_ago = now_ts.replace(tzinfo=None) - datetime.timedelta(hours=8)
                    display_df = df[df['dt_temp'] >= eight_hours_ago]
                    
                    if not display_df.empty:
                        st.info(f"🕒 自動顯示最近 8 小時動態 (自 {eight_hours_ago.strftime('%H:%M')} 起)")
                    else:
                        st.write("目前 8 小時內暫無新紀錄，請使用關鍵字查詢舊資料。")

                if not display_df.empty:
                    # 移除計算用欄位並倒序排列（最新在前）
                    final_df = display_df.drop(columns=['dt_temp'], errors='ignore').iloc[::-1]
                    
                    # 套用表格樣式美化
                    st.markdown("""
                        <style>
                        table { width: 100%; border-collapse: collapse; font-size: 14px; }
                        th { background-color: #f0f2f6; text-align: left; padding: 10px; border: 1px solid #ddd; }
                        td { text-align: left; padding: 10px; border: 1px solid #ddd; word-wrap: break-word; }
                        </style>
                        """, unsafe_allow_html=True)
                    st.write(final_df.to_html(index=False, justify='left', classes='table'), unsafe_allow_html=True)
        except Exception as e:
            st.error(f"紀錄載入出錯：{e}")

# --- Tab 2: 數據統計 ---
with tab2:
    st.title("📊 數據統計")
    if st.text_input("管理員密碼", type="password") == "kevin198":
        if conn_success:
            raw_data = sheet.get_all_values()
            if len(raw_data) > 1:
                df_stat = pd.DataFrame(raw_data[1:], columns=raw_data[0])
                st.metric("累積登記件數", len(df_stat))
                st.subheader("填單人統計")
                st.bar_chart(df_stat['填單人 (員工姓名)'].value_counts())
                st.dataframe(df_stat.iloc[::-1], use_container_width=True)

st.caption("© 2026 應安客服系統 - 8小時即時動態版")
