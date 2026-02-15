import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import datetime
import pandas as pd
import pytz
import requests
import json

# --- 1. 頁面基本設定 ---
st.set_page_config(page_title="應安客服線上登記系統", page_icon="📝", layout="wide")
tw_timezone = pytz.timezone('Asia/Taipei')

# --- 2. 名單設定 (場站與人員) ---
STATION_LIST = [
    "請選擇或輸入關鍵字搜尋", "華視光復", "華視電視台", "華視二", "華視三", "華視五", "文教一", "文教二", "文教三", "文教五", "文教六", 
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
    "金財神", "蘭井", "友愛場", "佳音西園", "中華信義", "敦南場", "中華北門場", "東大門場", "其他(未登入場站)" 
]
STAFF_LIST = ["請選擇填單人", "宗哲", "美妞", "政宏", "文輝", "恩佳", "志榮", "阿錨", "子毅", "浚"]

# --- 3. Google Sheets 連線 ---
def init_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        if "google_sheets" in st.secrets:
            creds_dict = st.secrets["google_sheets"]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        else:
            creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Google 試算表授權失敗: {e}")
        return None

# --- 4. 強化版 Open Data 抓取 ---
def auto_log_parking(sheet_cw):
    """嘗試從多個途徑抓取碧華國小車位"""
    # 這是新北市公共停車場即時資料的 JSON API
    api_url = "https://data.ntpc.gov.tw/api/datasets/02170387-9A39-4E61-9A6F-088825227702/json?size=1000"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
    }

    try:
        # verify=False 繞過 SSL 憑證檢查 (有時政府網站憑證會過期或不被雲端主機信任)
        resp = requests.get(api_url, headers=headers, timeout=15, verify=False)
        
        if resp.status_code != 200:
            return f"⚠️ 政府 API 拒絕連線 (錯誤碼: {resp.status_code})"
        
        data = resp.json()
        spots = None
        for lot in data:
            # 增加名稱匹配的模糊度
            name = lot.get('NAME', '')
            if "碧華國小" in name:
                spots = lot.get('AVAILABLECAR', '')
                break
        
        if spots is not None and str(spots).lstrip('-').isdigit():
            now_str = datetime.datetime.now(tw_timezone).strftime("%Y-%m-%d %H:%M")
            last_record = sheet_cw.get_all_values()
            
            # 若與上一筆時間不同則寫入
            if not last_record or last_record[-1][0] != now_str:
                sheet_cw.append_row([now_str, str(spots)])
                return f"✅ 車位自動同步成功：{spots}"
            return f"📊 目前碧華國小車位：{spots}"
        
        return "⚠️ 資料庫中找不到碧華國小場站"
    
    except Exception as e:
        # 將具體錯誤印出，方便排查
        return f"⚠️ API 解析失敗: {type(e).__name__}"

# --- 5. 初始化與執行 ---
client = init_connection()
if client:
    try:
        spreadsheet = client.open("客服作業表")
        sheet_kf = spreadsheet.worksheet("客服紀錄")
        sheet_cw = spreadsheet.worksheet("車位紀錄")
        parking_msg = auto_log_parking(sheet_cw)
    except Exception as e:
        st.error(f"分頁讀取失敗，請確認分頁名稱是否正確: {e}")
        st.stop()
else:
    st.stop()

# --- 6. 分頁設定 ---
tab1, tab2, tab3 = st.tabs(["📝 案件登記", "📊 數據統計", "🚗 車位趨勢"])

with tab1:
    st.title("📝 應安客服線上登記系統")
    st.info(parking_msg)
    
    with st.form("my_form", clear_on_submit=True):
        st.write(f"🕒 當前時間：{datetime.datetime.now(tw_timezone).strftime('%Y-%m-%d %H:%M:%S')}")
        col1, col2 = st.columns(2)
        with col1:
            station_name = st.selectbox("場站名稱", options=STATION_LIST)
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
        
        c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
        with c1:
            submit = st.form_submit_button("確認送出")
        with c2:
            st.link_button("多元支付", "http://219.85.163.90:5010/")
        with c3:
            st.link_button("簡訊系統", "https://umc.fetnet.net/#/menu/login")

        if submit:
            if user_name != "請選擇填單人" and station_name != "請選擇或輸入關鍵字搜尋":
                try:
                    ts = datetime.datetime.now(tw_timezone).strftime("%Y-%m-%d %H:%M:%S")
                    code = f"REC-{datetime.datetime.now().strftime('%m%d%H%M%S')}"
                    sheet_kf.append_row([ts, station_name, caller_name, caller_phone, car_num.upper(), category, description, user_name, code])
                    st.success("✅ 送出成功！")
                    st.rerun()
                except Exception as e:
                    st.error(f"寫入失敗: {e}")

    # 查詢區塊
    st.markdown("---")
    search_input = st.text_input("🔍 關鍵字查詢歷史紀錄")
    all_kf = sheet_kf.get_all_values()
    if len(all_kf) > 1:
        df_kf = pd.DataFrame(all_kf[1:], columns=all_kf[0])
        if search_input:
            match_df = df_kf[df_kf.apply(lambda r: r.astype(str).str.contains(search_input, case=False).any(), axis=1)]
            st.dataframe(match_df.iloc[::-1], use_container_width=True)
        else:
            st.write("🕒 最近 3 筆：")
            st.table(df_kf.tail(3).iloc[::-1])

with tab2:
    if st.text_input("管理員密碼", type="password") == "kevin198":
        st.subheader("處理量統計")
        if len(all_kf) > 1:
            df_s = pd.DataFrame(all_kf[1:], columns=all_kf[0])
            st.bar_chart(df_s['填單人 (員工姓名)'].value_counts())

with tab3:
    st.header("🚗 碧華國小車位歷史")
    all_cw = sheet_cw.get_all_values()
    if
