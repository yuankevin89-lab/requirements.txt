import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import datetime
import pandas as pd
import pytz
import requests
from bs4 import BeautifulSoup
import re

# --- 1. 頁面基本設定 ---
st.set_page_config(page_title="應安客服線上登記系統", page_icon="📝", layout="wide")
tw_timezone = pytz.timezone('Asia/Taipei')

# --- 2. 名單設定 (場站清單與填單人) ---
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

# --- 3. Google Sheets 連線與車位抓取函式 ---
def init_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        if "google_sheets" in st.secrets:
            creds_dict = st.secrets["google_sheets"]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        else:
            creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"連線失敗: {e}")
        return None

def auto_log_parking(sheet_cw):
    """強化版抓取邏輯：抓取碧華國小即時車位"""
    url = "https://www.parkinginfo.ntpc.gov.tw/parkingrealInfo/?parkinglotname=%E7%A2%A7%E8%8F%AF%E5%9C%8B%E5%B0%8F"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # 多重搜尋策略
        element = soup.find("span", {"id": "ContentPlaceHolder1_lblAvailableCar"})
        spots_text = element.text.strip() if element else ""
        
        # 只提取數字
        spots = "".join(re.findall(r'\d+', spots_text))
        
        if spots.isdigit():
            now_str = datetime.datetime.now(tw_timezone).strftime("%Y-%m-%d %H:%M")
            # 防止一分鐘內重複寫入
            last_record = sheet_cw.get_all_values()
            if not last_record or last_record[-1][0] != now_str:
                sheet_cw.append_row([now_str, spots])
                return f"✅ 車位自動同步成功：{spots}"
            return f"📊 目前碧華國小車位：{spots}"
        return "⚠️ 目前無法解析車位數字"
    except Exception as e:
        return f"⚠️ 車位抓取錯誤"

# --- 4. 初始化系統 ---
client = init_connection()
if client:
    sheet_kf = client.open("客服作業表").worksheet("客服紀錄")
    sheet_cw = client.open("客服作業表").worksheet("車位紀錄")
    # 開啟網頁即觸發抓取
    parking_msg = auto_log_parking(sheet_cw)
else:
    st.stop()

# --- 5. 分頁設定 ---
tab1, tab2, tab3 = st.tabs(["📝 案件登記", "📊 數據統計", "🚗 車位紀錄趨勢"])

# --- Tab 1: 案件登記 ---
with tab1:
    st.title("📝 應安客服線上登記系統")
    st.info(parking_msg) # 顯示車位抓取結果
    
    now_obj = datetime.datetime.now(tw_timezone)
    dt_str = now_obj.strftime("%Y-%m-%d %H:%M:%S")

    with st.form("my_form", clear_on_submit=True):
        st.write(f"🕒 登記時間：{dt_str}")
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
        
        description = st.text_area("描述 (詳細過程)", height=150)
        
        # 按鈕群組
        btn_col1, btn_col2, btn_col3, btn_col4 = st.columns([1, 1, 1, 2]) 
        with btn_col1:
            submit = st.form_submit_button("確認送出")
        with btn_col2:
            st.link_button("多元支付", "http://219.85.163.90:5010/")
        with btn_col3:
            st.link_button("簡訊系統", "https://umc.fetnet.net/#/menu/login")

        if submit:
            if user_name != "請選擇填單人" and station_name != "請選擇或輸入關鍵字搜尋" and description:
                try:
                    # 隱藏編碼生成
                    h_code = f"REC-{datetime.datetime.now().strftime('%m%d%H%M%S')}"
                    row_to_add = [dt_str, station_name, caller_name, caller_phone, car_num.upper(), category, description, user_name, h_code]
                    sheet_kf.append_row(row_to_add)
                    st.success("✅ 資料已成功上傳！")
                    st.rerun()
                except Exception as e:
                    st.error(f"上傳錯誤：{e}")
            else:
                st.warning("⚠️ 請填寫必填欄位 (填單人、場站及描述)。")

    # --- 🔍 全方位關鍵字查詢區塊 ---
    st.markdown("---")
    st.subheader("🔍 歷史紀錄查詢")
    search_q = st.text_input("輸入關鍵字 (車號、姓名、電話或內容)")
    
    raw_kf = sheet_kf.get_all_values()
    if len(raw_kf) > 1:
        df_kf = pd.DataFrame(raw_kf[1:], columns=raw_kf[0])
        if search_q:
            mask = df_kf.apply(lambda row: row.astype(str).str.contains(search_q, case=False).any(), axis=1)
            st.dataframe(df_kf[mask].iloc[::-1], use_container_width=True)
        else:
            st.write("🕒 最近 3 筆登記：")
            st.table(df_kf.tail(3).iloc[::-1])

# --- Tab 2: 數據統計 ---
with tab2:
    st.title("📊 數據統計")
    if st.text_input("管理員密碼", type="password") == "kevin198":
        if len(raw_kf) > 1:
            st.subheader("今日各類別來電佔比")
            df_kf['日期'] = pd.to_datetime(df_kf['日期/時間']).dt.date
            today = datetime.datetime.now(tw_timezone).date()
            today_data = df_kf[df_kf['日期'] == today]
            if not today_data.empty:
                st.bar_chart(today_data['來電類別'].value_counts())
            
            st.subheader("人員處理工作量")
            st.bar_chart(df_kf['填單人 (員工姓名)'].value_counts())
            st.subheader("完整紀錄清單")
            st.dataframe(df_kf, use_container_width=True)

# --- Tab 3: 車位紀錄趨勢 ---
with tab3:
    st.header("🚗 碧華國小車位監測趨勢")
    cw_data = sheet_cw.get_all_values()
    if len(cw_data) > 1:
        df_cw = pd.DataFrame(cw_data[1:], columns=["時間", "剩餘車位"])
        df_cw["剩餘車位"] = pd.to_numeric(df_cw["剩餘車位"], errors='coerce')
        
        # 繪製線圖
        st.line_chart(df_cw.set_index("時間").tail(30))
        
        st.subheader("歷史明細")
        st.dataframe(df_cw.iloc[::-1], use_container_width=True)
    else:
        st.info("尚無車位紀錄資料。")

st.caption("© 2026 應安客服系統 - 2/15 終極整合修正版")
