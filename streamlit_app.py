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
    st.session_state.edit_data = {}

# --- 5. UI 邏輯 ---
tab1, tab2 = st.tabs(["📝 案件登記", "📊 數據統計"])

with tab1:
    st.title("📝 應安客服線上登記系統")
    now_ts = datetime.datetime.now(tw_timezone)
    
    # 編輯模式提示
    if st.session_state.edit_mode:
        st.warning(f"⚠️ 正在編輯紀錄 - 原時間: {st.session_state.edit_data.get('日期/時間', '未知')}")

    with st.form("my_form", clear_on_submit=True):
        d = st.session_state.edit_data
        # 保持原本的時間，不因為編輯而變動
        f_dt = d.get("日期/時間", now_ts.strftime("%Y-%m-%d %H:%M:%S"))
        
        st.info(f"🕒 案件時間：{f_dt}")
        col1, col2 = st.columns(2)
        with col1:
            station_name = st.selectbox("場站名稱", options=STATION_LIST, index=STATION_LIST.index(d["場站名稱"]) if d.get("場站名稱") in STATION_LIST else 0)
            caller_name = st.text_input("姓名 (來電人)", value=d.get("姓名 (來電人)", ""))
        with col2:
            user_name = st.selectbox("填單人", options=STAFF_LIST, index=STAFF_LIST.index(d["填單人 (員工姓名)"]) if d.get("填單人 (員工姓名)") in STAFF_LIST else 0)
            caller_phone = st.text_input("電話", value=d.get("電話", ""))
        
        col3, col4 = st.columns(2)
        with col3:
            cat_list = ["繳費機故障", "發票缺紙或卡紙", "無法找零", "身障優惠折抵", "其他"]
            category = st.selectbox("來電類別", options=cat_list, index=cat_list.index(d["來電類別"]) if d.get("來電類別") in cat_list else 0)
        with col4:
            car_num = st.text_input("車號", value=d.get("車號", ""))
        
        # 這裡從編輯資料中取出描述，若標題不對則嘗試 '描述'
        orig_desc = d.get("描述 (詳細過程)", d.get("描述", ""))
        description = st.text_area("描述 (詳細過程)", value=orig_desc)
        
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
                        sheet.update(f"A{st.session_state.edit_row_idx + 1}:H{st.session_state.edit_row_idx + 1}", [row_content])
                        st.success("✅ 紀錄更新成功！")
                        st.session_state.edit_mode = False
                        st.session_state.edit_data = {}
                    else:
                        sheet.append_row(row_content)
                        st.success("✅ 資料已成功送出！")
                    st.rerun()
                except Exception as e:
                    st.error(f"儲存失敗：{e}")

    if st.session_state.edit_mode:
        if st.button("❌ 取消編輯"):
            st.session_state.edit_mode = False
            st.session_state.edit_data = {}
            st.rerun()

    # --- 🔍 歷史紀錄與交班動態 ---
    st.markdown("---")
    st.subheader("🔍 歷史紀錄與交班動態")
    
    try:
        raw_data = sheet.get_all_values()
        if len(raw_data) > 1:
            df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
            df['row_idx'] = df.index + 1
            # 確保有 dt_temp 進行 8H 比對
            df['dt_temp'] = pd.to_datetime(df.iloc[:, 0], format='mixed', errors='coerce').dt.tz_localize(None).dt.floor('s')
            
            search_query = st.text_input("🔍 查詢紀錄 (搜尋車號、姓名、場站)", placeholder="留空顯示 8 小時動態")
            
            if search_query:
                mask = df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)
                display_df = df[mask]
            else:
                eight_hours_ago = (now_ts.replace(tzinfo=None) - datetime.timedelta(hours=8)).replace(microsecond=0)
                display_df = df[df['dt_temp'] >= eight_hours_ago]

            if not display_df.empty:
                display_df = display_df.iloc[::-1]
                
                # 遍歷顯示，並對欄位名稱做防錯處理
                for _, row in display_df.iterrows():
                    # 擷取描述文字 (防止標題名稱不一導致報錯)
                    desc_text = row.get("描述 (詳細過程)", row.get("描述", "無描述內容"))
                    
                    with st.container():
                        c1, c2, c3, c4, c5 = st.columns([2, 1.5, 1.5, 4, 1])
                        with c1: st.write(f"📅 {row.iloc[0]}") # 使用位置讀取日期
                        with c2: st.write(f"🏢 {row.get('場站名稱', '未知')}")
                        with c3: st.write(f"🚗 {row.get('車號', '---')}")
                        with c4: st.write(f"📝 {str(desc_text)[:40]}...")
                        with c5:
                            if st.button("📝 編輯", key=f"edit_{row['row_idx']}"):
                                st.session_state.edit_mode = True
                                st.session_state.edit_row_idx = row['row_idx']
                                st.session_state.edit_data = row.to_dict()
                                st.rerun()
                        st.markdown("<hr style='margin: 5px 0;'>", unsafe_allow_html=True)
            else:
                st.info("查無符合條件的紀錄。")
    except Exception as e:
        st.error(f"表格載入錯誤，請確認試算表欄位標題。錯誤原因: {e}")

# (Tab 2 數據統計部分保持不變)
