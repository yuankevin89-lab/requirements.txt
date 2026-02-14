import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import datetime
import pandas as pd
import pytz

# --- 1. 頁面基本設定 ---
st.set_page_config(page_title="應安客服雲端登記系統", page_icon="📝", layout="wide")
tw_timezone = pytz.timezone('Asia/Taipei')

# --- 2. 場站清單 ---
STATION_LIST = [
    "請選擇或輸入關鍵字搜尋", "華視光復", "華視電視台", "華視二", "華視三", "華視五", "文教一", "文教二", "文教三", "文教五", "文教六", 
    "延吉場", "大安場", "信義大安", "樂業場", "四維場", "仁愛場", "濟南一", "濟南二", "松智場", "松勇二", "六合場", 
    "統領場", "信義安和", "僑信場", "台北民生", "美麗華場", "基湖場", "北安場", "龍江場", "農安場", "民權西場", 
    "承德場", "承德三", "大龍場", "延平北場", "雙連", "中山機車", "中山場", "南昌", "博愛", "金山", "金華", 
    "詔安", "通化", "杭南一", "復興南", "逸仙", "興岩", "木柵", "泉州", "汀洲", "福州", "北平東", "水源", 
    "重慶南", "西寧市場", "西園國宅", "復興北", "宏泰民生", "福善一", "石牌二", "中央北", "紅毛城", "三玉", 
    "士林", "永平", "大龍峒社宅", "昆陽一", "洲子場", "環山", "文湖場", "民善場", "新明場", "德明研推", 
    "東湖場", "舊宗社宅", "秀山機車", "景平", "環狀A", "土城中華場", "板橋光正", "合宜場", "土城裕民", 
    "中央二", "中央三", "板橋文化", "同安", "佳音-竹林", "青潭國小", "進安", "新和", "永平", "中正路", 
    "安和", "新店中華", "員山", "板橋公車", "光復二", "光復三", "宜舍", "新板", "竹圍", "淡水", "淡水老街", 
    "林口文化", "秀峰場", "興南場", "中和莊敬", "三重永福", "徐匯場", "蘆洲保和場", "蘆洲三民", "榮華場", 
    "富貴場", "鄉長二", "汐止忠孝", "新台五路", "蘆竹場", "龜山興富", "竹東長春", "竹南中山", "銅鑼停一", 
    "台中黎明", "後龍", "台中復興", "文心場", "大和屋一場", "大和屋二場", "北港場", "西螺", "虎尾", "民德", 
    "衛民場", "衛民二場", "台南北門場", "台南永福", "台南國華", "台南民權", "善化", "仁德", "台南中華場", 
    "致穩", "台南康樂場", "金財神", "蘭井", "友愛場", "佳音西園", "中華信義", "敦南場", "中華北門場", "東大門場"
]

# --- 3. Google Sheets 連線 ---
def init_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["google_sheets"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client

try:
    client = init_connection()
    sheet = client.open("客服作業表").sheet1
    conn_success = True
except Exception as e:
    st.error(f"連線失敗: {e}")
    conn_success = False

# --- 4. 分頁邏輯 ---
tab1, tab2 = st.tabs(["📝 案件登記", "📊 數據統計"])

with tab1:
    st.title("📝 應安客服雲端登記系統")
    now_obj = datetime.datetime.now(tw_timezone)
    dt_str = now_obj.strftime("%Y-%m-%d %H:%M:%S")

    if conn_success:
        with st.form("my_form", clear_on_submit=True):
            st.info(f"🕒 登記時間：{dt_str}")
            col1, col2 = st.columns(2)
            with col1:
                station_name = st.selectbox("場站名稱 (搜尋並點選)", options=STATION_LIST)
                caller_name = st.text_input("姓名 (來電人)")
            with col2:
                user_name = st.text_input("填單人 (員工姓名)")
                caller_phone = st.text_input("電話")
            col3, col4 = st.columns(2)
            with col3:
                category = st.selectbox("來電類別", ["繳費機故障", "發票缺紙或卡紙", "無法找零", "身障優惠折抵", "其他"])
            with col4:
                car_number_input = st.text_input("車號")
            description = st.text_area("描述 (詳細過程)")
            
            btn_col1, btn_col2, btn_col3, btn_col4 = st.columns([1, 1, 1, 3]) 
            with btn_col1:
                submit = st.form_submit_button("確認送出")
            with btn_col2:
                st.link_button("多元支付", "http://219.85.163.90:5010/")
            with btn_col3:
                st.link_button("簡訊", "https://umc.fetnet.net/#/menu/login")

            if submit:
                if user_name and station_name != "請選擇或輸入關鍵字搜尋" and description:
                    try:
                        with st.spinner('正在上傳...'):
                            row_to_add = [dt_str, station_name, caller_name, caller_phone, car_number_input, category, description, user_name]
                            sheet.append_row(row_to_add)
                            st.success("✅ 資料已成功上傳！")
                            st.rerun()
                    except Exception as e:
                        st.error(f"上傳錯誤：{e}")
                else:
                    st.warning("⚠️ 請完整填寫必填欄位。")

        # --- 🚗 車號紀錄快速查詢區塊 ---
        st.markdown("---")
        st.subheader("🔍 車號歷史紀錄查詢")
        search_car = st.text_input("輸入完整或部分車牌號碼進行搜尋 (例如: ABC-1234)", help="輸入完成後請按 Enter")
        
        if search_car:
            try:
                raw_data = sheet.get_all_values()
                if len(raw_data) > 1:
                    df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
                    
                    # 篩選車號：支援不分大小寫的包含式搜尋
                    result_df = df[df['車號'].str.contains(search_car, case=False, na=False)]
                    
                    if not result_df.empty:
                        st.write(f"找到 {len(result_df)} 筆與 **{search_car}** 相關的紀錄：")
                        # 最新紀錄排在最上面
                        display_df = result_df.iloc[::-1]

                        # 使用 HTML 渲染以保持「最新」版本的自動換行與鎖定特性
                        table_html = display_df.to_html(index=False, justify='left', classes='table')
                        st.markdown(
                            """
                            <style>
                            table { width: 100%; border-collapse: collapse; }
                            th { background-color: #f0f2f6; text-align: left; padding: 10px; font-size: 14px; }
                            td { text-align: left; padding: 10px; border-bottom: 1px solid #ddd; word-wrap: break-word; font-size: 14px; }
                            </style>
                            """, unsafe_allow_html=True
                        )
                        st.write(table_html, unsafe_allow_html=True)
                    else:
                        st.info(f"查無車號 **{search_car}** 的歷史紀錄。")
            except Exception as e:
                st.error(f"查詢時發生錯誤：{e}")
        else:
            st.caption("請在上方欄位輸入車號以查詢歷史紀錄。")

# --- Tab 2: 數據統計 (維持最新版本) ---
with tab2:
    st.title("📊 數據統計")
    # ... (代碼與之前相同)
