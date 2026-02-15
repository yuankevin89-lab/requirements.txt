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

# --- 3. 初始化 Google Sheets 連線 ---
def init_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        if "google_sheets" in st.secrets:
            creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["google_sheets"], scope)
        else:
            creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
        return gspread.authorize(creds)
    except:
        return None

client = init_connection()
if client:
    sh = client.open("客服作業表")
    sheet_kf = sh.worksheet("客服紀錄")
    sheet_cw = sh.worksheet("車位紀錄")
else:
    st.error("⚠️ 無法連線至 Google 試算表，請檢查授權檔案。")
    st.stop()

# --- 4. UI 介面設定 ---
tab1, tab2, tab3 = st.tabs(["📝 案件登記", "📊 數據統計", "🚗 車位紀錄趨勢"])

# --- Tab 1: 案件登記 ---
with tab1:
    st.title("應安客服線上登記系統")
    
    # 顯示最新車位 (從試算表讀取，不直接爬蟲避免被封)
    cw_history = sheet_cw.get_all_values()
    if len(cw_history) > 1:
        st.success(f"🚗 碧華國小最新剩餘車位：{cw_history[-1][1]} (更新時間：{cw_history[-1][0]})")
    
    with st.form("main_form", clear_on_submit=True):
        now_dt = datetime.datetime.now(tw_timezone).strftime("%Y-%m-%d %H:%M:%S")
        st.write(f"🕒 登記時間：{now_dt}")
        
        col1, col2 = st.columns(2)
        with col1:
            station = st.selectbox("場站名稱", options=STATION_LIST)
            c_name = st.text_input("姓名 (來電人)")
        with col2:
            staff = st.selectbox("填單人", options=STAFF_LIST)
            c_phone = st.text_input("電話")
            
        col3, col4 = st.columns(2)
        with col3:
            cat = st.selectbox("來電類別", ["繳費機故障", "發票缺紙或卡紙", "無法找零", "身障優惠折抵", "其他"])
        with col4:
            car_no = st.text_input("車號")
            
        desc = st.text_area("描述 (詳細過程)", height=150)
        
        # 按鈕列
        b1, b2, b3, b4 = st.columns([1, 1, 1, 2])
        with b1:
            if st.form_submit_button("確認送出"):
                if staff != "請選擇填單人" and station != "請選擇或輸入關鍵字搜尋" and desc:
                    h_code = f"REC-{datetime.datetime.now().strftime('%m%d%H%M%S')}"
                    sheet_kf.append_row([now_dt, station, c_name, c_phone, car_no.upper(), cat, desc, staff, h_code])
                    st.toast("資料上傳成功！")
                    st.rerun()
                else:
                    st.error("❌ 請填寫必填欄位 (填單人、場站、描述)")
        with b2:
            st.link_button("多元支付", "http://219.85.163.90:5010/")
        with b3:
            st.link_button("簡訊系統", "https://umc.fetnet.net/#/menu/login")

    # 查詢與檢索
    st.markdown("---")
    st.subheader("🔍 關鍵字查詢 (搜尋車號、內容、電話)")
    search_q = st.text_input("請輸入關鍵字")
    all_kf = sheet_kf.get_all_values()
    if len(all_kf) > 1:
        df_kf = pd.DataFrame(all_kf[1:], columns=all_kf[0])
        if search_q:
            mask = df_kf.apply(lambda row: row.astype(str).str.contains(search_q, case=False).any(), axis=1)
            st.dataframe(df_kf[mask].iloc[::-1], use_container_width=True)
        else:
            st.write("🕒 最近 3 筆登記：")
            st.table(df_kf.tail(3).iloc[::-1])

# --- Tab 2: 數據統計 ---
with tab2:
    st.title("📊 數據統計")
    if st.text_input("管理密碼", type="password") == "kevin198":
        if len(all_kf) > 1:
            df_s = pd.DataFrame(all_kf[1:], columns=all_kf[0])
            st.subheader("客服人員處理量")
            st.bar_chart(df_s['填單人 (員工姓名)'].value_counts())
            st.subheader("原始資料庫")
            st.dataframe(df_s, use_container_width=True)

# --- Tab 3: 車位趨勢 ---
with tab3:
    st.title("🚗 碧華國小車位趨勢")
    if len(cw_history) > 1:
        df_cw = pd.DataFrame(cw_history[1:], columns=["時間", "剩餘車位"])
        df_cw["剩餘車位"] = pd.to_numeric(df_cw["剩餘車位"], errors='coerce')
        st.line_chart(df_cw.set_index("時間").tail(100))
        st.write("📋 歷史變動明細：")
        st.dataframe(df_cw.iloc[::-1], use_container_width=True)
    else:
        st.info("尚無歷史數據，請確保 Apps Script 腳本已開始運作。")

st.caption("© 2026 應安客服線上登記系統 (2/15 終極整合版)")
