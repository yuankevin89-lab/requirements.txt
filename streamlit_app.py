import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import datetime
import pandas as pd
import pytz
import plotly.express as px
import plotly.graph_objects as go
import re
import io
import requests

# --- 1. 頁面基本設定與專業樣式 ---
st.set_page_config(page_title="應安客服雲端登記系統", page_icon="📝", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display: none;}
    .block-container {padding-top: 2rem; padding-bottom: 1rem;}
    
    /* 全域純黑加粗樣式 (投影機清晰度強化) */
    * { color: #000000 !important; font-family: "Microsoft JhengHei", "Arial Black", sans-serif !important; font-weight: 800 !important; }
    
    [data-testid="stElementContainer"]:has(input[type="checkbox"]:checked) {
        background-color: #e8f5e9 !important;
        border-radius: 8px;
        padding: 10px;
        transition: background-color 0.3s ease;
        border: 1px solid #c8e6c9;
    }
    
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

    /* 跑馬燈專用容器樣式 */
    .weather-marquee-box {
        background: #FFFFFF; 
        border: 3px solid #000000; 
        border-radius: 5px; 
        padding: 5px; 
        margin-top: 10px;
        height: 50px;
        display: flex;
        align-items: center;
        overflow: hidden;
    }
    </style>
    """, unsafe_allow_html=True)

tw_timezone = pytz.timezone('Asia/Taipei')

# --- [新功能] 特定場站後台網址字典 ---
STATION_BACKENDS = {
    "文湖場": "https://114.35.111.230/systemSetting/deviceManagement/deviceList",
    "龍江場": "https://114.34.172.191/systemSetting/deviceManagement/deviceList",
    "和平東路場": "https://114.32.2.144/systemSetting/deviceManagement/device",
    "木柵路三段77巷場": "https://111.70.11.228/systemSetting/deviceManagement/device",
    "大龍場": "https://218.161.19.23/systemSetting/deviceManagement/device",
    "興岩社福大樓": "https://114.34.59.201/systemSetting/deviceManagement/device",
    "木柵社宅": "https://220.135.37.120/systemSetting/deviceManagement/device",
    "西園國宅": "https://1.34.190.66/systemSetting/deviceManagement/device",
    "士林場": "https://114.32.150.245/systemSetting/deviceManagement/deviceList",
    "大龍峒社宅": "https://211.21.156.151/systemSetting/deviceManagement/device",
    "環山": "https://111.70.4.51/systemSetting/deviceManagement/deviceList",
    "舊宗社宅": "https://220.135.96.128/systemSetting/deviceManagement/device",
    "景平": "https://114.34.235.247/systemSetting/deviceManagement/device",
    "青潭國小": "https://111.70.23.175/systemSetting/deviceManagement/deviceList",
    "水源市場": "https://220.132.13.220/systemSetting/deviceManagement/deviceList",
    "紅毛城": "https://118.163.137.193/systemSetting/deviceManagement/device"
}

# --- [優化] 快取資料讀取函式 ---
@st.cache_data(ttl=600)  # 快取 10 分鐘，或手動重新整理
def get_cloud_data(_sheet):
    """從 Google Sheets 抓取所有原始資料並快取"""
    return _sheet.get_all_values()

# --- [優化] 獲取台北即時天氣邏輯 ---
def get_taipei_weather():
    try:
        url = "https://api.open-meteo.com/v1/forecast?latitude=25.03&longitude=121.56&current_weather=true"
        response = requests.get(url, timeout=5)
        data = response.json()
        temp = round(data['current_weather']['temperature'])
        code = data['current_weather']['weathercode']
        weather_map = {
            0: "晴朗", 1: "晴間多雲", 2: "多雲", 3: "陰天",
            45: "霧", 48: "霧", 51: "毛毛細雨", 53: "毛毛細雨", 55: "毛毛細雨",
            61: "小雨", 63: "中雨", 65: "大雨", 71: "小雪", 73: "中雪", 75: "大雪",
            77: "雪花", 80: "陣雨", 81: "強陣雨", 82: "極端陣雨",
            95: "雷陣雨", 96: "雷雨伴隨冰雹", 99: "雷雨伴隨重度冰雹"
        }
        desc = weather_map.get(code, f"代碼:{code}") 
        return f"🌡️ 台北：{temp}°C | {desc}"
    except Exception as e:
        return "🌡️ 台北：連線中..."

# --- 2. 初始資料與連線 ---
def init_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds_dict = st.secrets["google_sheets"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        return gspread.authorize(creds)
    except: return None

client = init_connection()

# --- 3. 核心邏輯：場站清單與快取管理 ---
if client:
    main_spreadsheet = client.open("客服作業表")
    sheet = main_spreadsheet.sheet1
    try:
        station_ws = main_spreadsheet.worksheet("Station_Settings")
    except:
        station_ws = main_spreadsheet.add_worksheet(title="Station_Settings", rows="100", cols="5")
        station_ws.append_row(["場站名稱"])

    # 這裡也對場站清單做簡單快取
    @st.cache_data(ttl=3600)
    def get_stations(_ws):
        return _ws.col_values(1)[1:]

    cloud_stations = get_stations(station_ws)
    if not cloud_stations:
        STATION_LIST = ["請選擇或輸入關鍵字搜尋", "華視光復", "其他(未登入場站)"]
    else:
        STATION_LIST = ["請選擇或輸入關鍵字搜尋"] + sorted(list(set(cloud_stations))) + ["其他(未登入場站)"]
else:
    sheet = None
    STATION_LIST = ["連線失敗"]

STAFF_LIST = ["請選擇填單人", "宗哲", "美妞", "政宏", "文輝", "恩佳", "新人","志榮", "阿錨", "子毅", "浚"]
CATEGORY_LIST = ["發票問題無法繳費", "網路問題無法繳費", "發票缺紙或卡紙", "無法找零", "身障優惠折抵", "網路異常", "繳費問題相關", "其他"]
STAT_CATEGORY_LIST = [c for c in CATEGORY_LIST if c != "其他"]

CATEGORY_COLOR_MAP = {
    "身障優惠折抵": "blue",
    "發票問題無法繳費": "green",
    "網路問題無法繳費": "#FF4B4B",
    "發票缺紙或卡紙": px.colors.qualitative.Safe[1],
    "無法找零": px.colors.qualitative.Safe[2],
    "網路異常": px.colors.qualitative.Safe[4],
    "繳費問題相關": "#8DB600"
}

def format_car_number(car_str):
    if not car_str: return ""
    clean_s = car_str.replace("-", "").strip().upper()
    match = re.match(r"([A-Z]+)([0-9]+)", clean_s)
    if match: return f"{match.group(1)}-{match.group(2)}"
    match_reverse = re.match(r"([0-9]+)([A-Z]+)", clean_s)
    if match_reverse: return f"{match_reverse.group(1)}-{match_reverse.group(2)}"
    return clean_s

if "edit_mode" not in st.session_state: st.session_state.edit_mode = False
if "edit_row_idx" not in st.session_state: st.session_state.edit_row_idx = None
if "edit_data" not in st.session_state: st.session_state.edit_data = [""] * 8
if "form_id" not in st.session_state: st.session_state.form_id = 0

tab1, tab2 = st.tabs(["📝 案件登記", "📊 數據統計分析"])

# --- Tab 1: 案件登記 ---
with tab1:
    h_c1, h_c2 = st.columns([3, 1])
    with h_c1:
        st.title("📝 應安客服線上登記系統")
    with h_c2:
        weather_text = get_taipei_weather()
        st.markdown(f"""
            <div class="weather-marquee-box">
                <marquee scrollamount="3" style="font-size: 18px; font-weight: 800; color: #000000;">
                    {weather_text} 　　　 {weather_text}
                </marquee>
            </div>
            """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown("### 🏢 場站管理")
        c_new1, c_new2, c_refresh = st.columns([4, 1, 1.2])
        new_st_name = c_new1.text_input("新增場站名稱", placeholder="輸入名稱後點擊右側新增...")
        
        if c_new2.button("➕ 確認新增", use_container_width=True):
            if new_st_name.strip():
                station_ws.append_row([new_st_name.strip()])
                st.cache_data.clear() # 清除快取以顯示新場站
                st.success(f"已成功新增場站：{new_st_name}")
                st.rerun()
        
        # 新增手動刷新按鈕
        if c_refresh.button("🔄 刷新雲端資料", use_container_width=True):
            st.cache_data.clear()
            st.toast("已同步最新雲端資料！")
            st.rerun()
    
    st.divider()
    
    now_ts = datetime.datetime.now(tw_timezone)
    if st.session_state.edit_mode:
        st.warning(f"⚠️ 【編輯模式】- 正在更新第 {st.session_state.edit_row_idx} 列紀錄")

    d = st.session_state.edit_data if st.session_state.edit_mode else [""]*8
    
    col_st_1, col_st_2 = st.columns(2)
    with col_st_1:
        station_name = st.selectbox("🏢 選擇場站名稱", options=STATION_LIST, 
                                     index=STATION_LIST.index(d[1]) if d[1] in STATION_LIST else 0)

    with st.form(key=f"my_form_{st.session_state.form_id}", clear_on_submit=False):
        f_dt = d[0] if st.session_state.edit_mode else now_ts.strftime("%Y-%m-%d %H:%M")
        st.info(f"🕒 案件時間：{f_dt}")
        
        c1, c2 = st.columns(2)
        with c1:
            caller_name = st.text_input("姓名", value=d[2])
        with c2:
            user_name = st.selectbox("填單人", options=STAFF_LIST, 
                                     index=STAFF_LIST.index(d[7]) if d[7] in STAFF_LIST else 0, 
                                     disabled=st.session_state.edit_mode)
        
        c3, c4 = st.columns(2)
        with c3:
            caller_phone = st.text_input("電話", value=d[3])
            d_cat = d[5]
            if d_cat == "繳費機異常" or d_cat == "繳費機故障": d_cat = "發票問題無法繳費"
            category = st.selectbox("類別", options=CATEGORY_LIST, index=CATEGORY_LIST.index(d_cat) if d_cat in CATEGORY_LIST else 7)
        with c4: 
            car_num = st.text_input("車號", value=d[4])
            description = st.text_area("描述內容", value=d[6], height=110)

        # 按鈕佈局
        btn_c1, btn_c2, btn_c3, btn_c4, _ = st.columns([1, 1, 1, 1.8, 1.2])
        submit_btn = btn_c1.form_submit_button("確認送出" if not st.session_state.edit_mode else "更新紀錄")
        
        if st.session_state.edit_mode:
            if btn_c2.form_submit_button("❌ 取消編輯"):
                st.session_state.edit_mode, st.session_state.edit_row_idx, st.session_state.edit_data = False, None, [""] * 8
                st.session_state.form_id += 1
                st.rerun()
        else: 
            btn_c2.link_button("多元支付", "http://219.85.163.90:5010/")
        
        btn_c3.link_button("簡訊系統", "https://umc.fetnet.net/#/menu/login")

        # --- 專屬後台按鈕觸發邏輯 ---
        if station_name in STATION_BACKENDS:
            btn_c4.link_button(f"🔗 {station_name}後台", STATION_BACKENDS[station_name])

        if submit_btn:
            if user_name != "請選擇填單人" and station_name != "請選擇或輸入關鍵字搜尋":
                final_car_num = format_car_number(car_num)
                row = [f_dt, station_name, caller_name, caller_phone, final_car_num, category, description, user_name]
                if st.session_state.edit_mode:
                    sheet.update(f"A{st.session_state.edit_row_idx}:H{st.session_state.edit_row_idx}", [row])
                    st.session_state.edit_mode, st.session_state.edit_row_idx, st.session_state.edit_data = False, None, [""] * 8
                else: 
                    sheet.append_row(row)
                
                st.cache_data.clear() # 提交後清除快取，確保列表更新
                st.session_state.form_id += 1 
                st.rerun()
            else: st.error("請正確選擇填單人與場站")

    # --- 最近紀錄 (使用快取優化) ---
    st.markdown("---")
    st.subheader("🔍 最近紀錄 (交班動態)")
    if sheet:
        # 改用快取函式讀取資料
        all_raw = get_cloud_data(sheet)
        if len(all_raw) > 1:
            valid_rows = [(i+2, r) for i, r in enumerate(all_raw[1:]) if any(str(c).strip() for c in r)]
            search_q = st.text_input("🔍 搜尋歷史紀錄 (全欄位)", placeholder="輸入關鍵字...").strip().lower()
            eight_hrs_ago = (now_ts.replace(tzinfo=None)) - datetime.timedelta(hours=8)
            display_list = []
            
            if search_q: 
                display_list = [(idx, r) for idx, r in valid_rows if any(search_q in str(cell).lower() for cell in r)]
            else:
                for idx, r in valid_rows:
                    try:
                        dt = pd.to_datetime(r[0]).replace(tzinfo=None)
                        if dt >= eight_hrs_ago: display_list.append((idx, r))
                    except: continue
                if not display_list: display_list = valid_rows[-3:]

            if display_list:
                col_widths = [0.9, 0.6, 0.9, 1.2, 1.0, 1.5, 5.1, 0.8, 0.6, 0.6]
                cols = st.columns(col_widths)
                headers = ["日期/時間", "場站", "姓名", "電話", "車號", "類別", "描述摘要", "填單人", "編輯", "標記"]
                for col, t in zip(cols, headers): col.markdown(f"**{t}**")
                
                for r_idx, r_val in reversed(display_list):
                    c = st.columns(col_widths)
                    c[0].write(f"**{r_val[0]}**") 
                    c[1].write(r_val[1]); c[2].write(r_val[2]); c[3].write(r_val[3]); c[4].write(r_val[4]); c[5].write(r_val[5])
                    clean_d = r_val[6].replace('\n', ' ').replace('"', '&quot;')
                    short_d = f"{clean_d[:35]}..." if len(clean_d) > 35 else clean_d
                    c[6].markdown(f'<div class="hover-text" title="{clean_d}">{short_d}</div>', unsafe_allow_html=True)
                    c[7].write(r_val[7])
                    if c[8].button("📝", key=f"ed_{r_idx}"):
                        st.session_state.edit_mode, st.session_state.edit_row_idx, st.session_state.edit_data = True, r_idx, r_val
                        st.rerun()
                    c[9].checkbox(" ", key=f"chk_{r_idx}", label_visibility="collapsed")
                    st.markdown("<hr style='margin: 2px 0; border-top: 1px solid #ddd;'>", unsafe_allow_html=True)

# --- Tab 2: 數據統計 ---
with tab2:
    st.title("📊 數據統計與分析")
    if st.text_input("管理員密碼", type="password", key="stat_pwd") == "kevin198":
        if sheet:
            raw_stat = get_cloud_data(sheet)
            if len(raw_stat) > 1:
                hdr = raw_stat[0]
                df_s = pd.DataFrame(raw_stat[1:], columns=hdr)
                df_s[hdr[0]] = pd.to_datetime(df_s[hdr[0]], errors='coerce')
                df_s = df_s.dropna(subset=[hdr[0]])
                df_filtered = df_s[df_s[hdr[5]] != "其他"]
                
                c_range = st.date_input("📅 選擇統計週期", value=[])
                wk_df = df_filtered.loc[(df_filtered[hdr[0]].dt.date >= c_range[0]) & (df_filtered[hdr[0]].dt.date <= c_range[1])] if len(c_range) == 2 else df_filtered.tail(300)

                if not wk_df.empty:
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        wk_df.to_excel(writer, index=False, sheet_name='客服報表')
                    excel_data = output.getvalue()
                    
                    st.download_button(
                        label="📥 下載 Excel (.xlsx)",
                        data=excel_data,
                        file_name=f"應安報表_{datetime.date.today()}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
                    st.divider()
                    config_4k = {'toImageButtonOptions': {'format': 'png', 'height': 1080, 'width': 1920, 'scale': 2}}

                    def apply_bold_style(fig, title_text, is_stacked=False, is_h=False, is_line=False):
                        leg = dict(font=dict(size=18, color="#000000"), orientation="v", yanchor="top", y=1, xanchor="left", x=1.02) if (is_stacked or "對比" in title_text) else None
                        fig.update_layout(
                            font=dict(family="Microsoft JhengHei, Arial Black", size=20, color="#000000"),
                            title=dict(text=f"<b>{title_text}</b>", font=dict(size=34), y=0.96, x=0.5, xanchor='center'),
                            paper_bgcolor='white', plot_bgcolor='white',
                            margin=dict(t=130, b=160, l=150 if is_h else 120, r=200 if (is_stacked or "對比" in title_text) else 120),
                            showlegend=True if (is_stacked or "對比" in title_text) else False, legend=leg
                        )
                        fig.update_xaxes(tickfont=dict(size=20, color="#000000", weight="bold"), linecolor='#000000', linewidth=3)
                        fig.update_yaxes(tickfont=dict(size=20, color="#000000", weight="bold"), linecolor='#000000', linewidth=3, gridcolor='#F0F0F0')
                        fig.update_traces(textfont=dict(size=20, color="#000000", weight="bold"))
                        return fig

                    # 1. ⏳ 雙週案件類別對比分析
                    t_data = df_filtered.copy(); t_data['D'] = t_data[hdr[0]].dt.date
                    td = datetime.date.today()
                    tw_s, lw_s, lw_e = td-datetime.timedelta(days=6), td-datetime.timedelta(days=13), td-datetime.timedelta(days=7)
                    def get_c(s, e, l):
                        m = (t_data['D'] >= s) & (t_data['D'] <= e)
                        r = t_data.loc[m][hdr[5]].value_counts().reindex(STAT_CATEGORY_LIST, fill_value=0).reset_index(name='件數')
                        r.columns = ['類別', '件數']; r['週期'] = l; return r
                    df_c = pd.concat([get_c(lw_s, lw_e, "上週 (前7日)"), get_c(tw_s, td, "本週 (最近7日)")])
                    fig_c = px.bar(df_c, x='類別', y='件數', color='週期', barmode='group', text='件數', color_discrete_map={"本週 (最近7日)": "#1f77b4", "上週 (前7日)": "#ff7f0e"})
                    st.plotly_chart(apply_bold_style(fig_c, "⏳ 雙週案件類別對比分析"), use_container_width=True, config=config_4k)

                    st.divider()
                    g1, g2 = st.columns(2)
                    with g1:
                        cat_c = wk_df[hdr[5]].value_counts().reset_index(); cat_c.columns=['類別','件數']
                        fig1 = px.bar(cat_c, x='類別', y='件數', text='件數', color='類別', color_discrete_map=CATEGORY_COLOR_MAP)
                        st.plotly_chart(apply_bold_style(fig1, "📂 當前區間案件分佈"), use_container_width=True, config=config_4k)
                    with g2:
                        st_counts = wk_df[hdr[1]].value_counts().reset_index()
                        st_counts.columns = ['場站', '件數']; top10_df = st_counts.head(10)
                        fig2 = px.bar(top10_df, x='場站', y='件數', text='件數', color='場站', color_discrete_sequence=px.colors.qualitative.Pastel)
                        st.plotly_chart(apply_bold_style(fig2, "🏢 場站排名 (Top 10)"), use_container_width=True, config=config_4k)

                    st.divider()
                    top10_names = top10_df['場站'].tolist()
                    cross = wk_df[wk_df[hdr[1]].isin(top10_names)].groupby([hdr[1], hdr[5]]).size().reset_index(name='件數')
                    cross.columns = ['場站', '異常類別', '件數']
                    fig3 = px.bar(cross, x='場站', y='件數', color='異常類別', text='件數', color_discrete_map=CATEGORY_COLOR_MAP)
                    st.plotly_chart(apply_bold_style(fig3, "🔍 場站 vs. 異常類別分析 (Top 10)", is_stacked=True), use_container_width=True, config=config_4k)

                    st.divider()
                    fig4 = px.bar(cat_c, y='類別', x='件數', orientation='h', text='件數', color='類別', color_discrete_map=CATEGORY_COLOR_MAP)
                    st.plotly_chart(apply_bold_style(fig4, "📈 類別精確統計", is_h=True), use_container_width=True, config=config_4k)

                    st.divider()
                    daily_counts = wk_df.groupby(wk_df[hdr[0]].dt.date).size().reset_index(name='件數')
                    daily_counts.columns = ['日期', '件數']
                    fig5 = px.line(daily_counts, x='日期', y='件數', text='件數', markers=True)
                    fig5.update_traces(textposition="top center", line=dict(width=4), marker=dict(size=12))
                    st.plotly_chart(apply_bold_style(fig5, "📈 每日案件量趨勢圖"), use_container_width=True, config=config_4k)

st.caption("© 2026 應安客服系統 ")
