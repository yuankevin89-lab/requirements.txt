import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import datetime
import pandas as pd
import pytz
import plotly.express as px
import base64

# --- 1. 頁面基本設定與 4K 投影增強樣式 ---
st.set_page_config(page_title="應安客服雲端登記系統", page_icon="📝", layout="wide")

# 解決 MediaFileStorageError：直接將 Logo 內嵌為 Base64 字串 (此為簡化示意，實務上請確保此字串完整)
# 註：此處已為您保留 Logo 顯示位置的 HTML 結構
def get_logo_html():
    # 若您有實體圖檔在同目錄，程式會讀取；若無，則顯示品牌文字保底
    try:
        with open("公司LOGO-02.png", "rb") as f:
            data = base64.b64encode(f.read()).decode()
            return f'<div style="position: absolute; top: -50px; right: 0px;"><img src="data:image/png;base64,{data}" width="220"></div>'
    except:
        return '<div style="position: absolute; top: -10px; right: 0px; text-align:right;"><h2 style="color:#1f77b4; margin:0;">應安停車</h2><p style="color:gray; margin:0;">客服管理系統</p></div>'

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display: none;}
    .block-container {padding-top: 2rem;}
    
    /* 4K 投影增強：表格勾選變色 */
    [data-testid="stElementContainer"]:has(input[type="checkbox"]:checked) {
        background-color: #e8f5e9 !important;
        border-radius: 8px;
        padding: 5px;
        border: 1px solid #c8e6c9;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown(get_logo_html(), unsafe_allow_html=True)

tw_timezone = pytz.timezone('Asia/Taipei')

# --- 2. 初始資料與 2/24 鎖定名單 ---
STATION_LIST = [
    "請選擇或輸入關鍵字搜尋", "華視光復","電視台","華視二","文教五","華視五","文教一","文教二","文教六","文教三",
    "延吉場","大安場","信義大安","樂業場","仁愛場","四維場","濟南一場","濟南二場","松智場","松勇二","六合市場",
    "統領場","信義安和","僑信場","台北民生場","美麗華場","基湖場","北安場","龍江場","農安場","明倫社宅",
    "民權西場","承德場","承德三","大龍場","延平北場","雙連","中山市場","助安中山場","南昌場","博愛場","金山場",
    "金華場","通化","杭南一","復興南","仁愛逸仙","興岩社福大樓","木柵社宅","泉州場","汀州場",
    "北平東場","福州場","水源市場","重慶南","西寧市場","西園國宅","復興北","宏泰民生","新洲美福善場","福善一",
    "石牌二","中央北","紅毛城","三玉","士林場","永平社宅","涼州場","大龍峒社宅","成功場","洲子場","環山",
    "文湖場","民善場","行愛場","新明場","德明研推","東湖場","舊宗社宅","行善五","秀山機車","景平","環狀A機車",
    "樹林水源","土城中華場","光正","合宜A2","合宜A3","昆陽一","合宜A6東","合宜A6西","裕民","中央二","中央三","陶都場",
    "板橋文化1F","板橋文化B1","佳音-同安","佳音-竹林","青潭國小","林口文化","秀峰","興南場","中和莊敬",
    "三重永福","徐匯場","蘆洲保和","蘆洲三民","榮華場","富貴場","鄉長二","汐止忠孝","新台五路","蘆竹場",
    "龜山興富","竹東長春","竹南中山","銅鑼停一","台中黎明場","後龍","台中復興","台中復興二","文心場",
    "台中大和屋","一銀北港","西螺","虎尾","民德","衛民","衛民二場","台南北門","台南永福","台南國華",
    "台南民權","善化","仁德","台南中華場","致穩","台南康樂場","金財神","蘭井","友愛場","佳音西園",
    "中華信義","敦南場","中華北門場","東大門場", "其他(未登入場站)"
]
STAFF_LIST = ["請選擇填單人", "宗哲", "美妞", "政宏", "文輝", "恩佳", "志榮", "阿錨", "子毅", "浚"]
CATEGORY_LIST = ["繳費機異常", "發票缺紙或卡紙", "無法找零", "身障優惠折抵", "網路異常", "繳費問題相關", "其他"]
CATEGORY_COLOR_MAP = {
    "身障優惠折抵": "#1f77b4", "繳費機異常": "#2ca02c", "其他": "#8c564b",
    "發票缺紙或卡紙": "#d62728", "無法找零": "#ff7f0e",
    "網路異常": "#9467bd", "繳費問題相關": "#17becf"
}

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
sheet = client.open("客服作業表").sheet1 if client else None

# --- 4. 狀態管理 ---
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False
    st.session_state.edit_row_idx = None
    st.session_state.edit_data = [""] * 8

# --- 5. 介面佈局 ---
tab1, tab2 = st.tabs(["📝 案件登記", "📊 數據統計分析"])

with tab1:
    st.title("📝 應安客服線上登記系統")
    now_ts = datetime.datetime.now(tw_timezone)
    
    with st.form(key="reg_form", clear_on_submit=False):
        d = st.session_state.edit_data if st.session_state.edit_mode else [""]*8
        f_dt = d[0] if st.session_state.edit_mode else now_ts.strftime("%Y-%m-%d %H:%M")
        
        st.info(f"🕒 案件時間：{f_dt}")
        col1, col2 = st.columns(2)
        with col1:
            station = st.selectbox("場站名稱", options=STATION_LIST, index=STATION_LIST.index(d[1]) if d[1] in STATION_LIST else 0)
            caller = st.text_input("姓名", value=d[2])
        with col2:
            staff = st.selectbox("填單人", options=STAFF_LIST, index=STAFF_LIST.index(d[7]) if d[7] in STAFF_LIST else 0)
            phone = st.text_input("電話", value=d[3])
            
        col3, col4 = st.columns(2)
        with col3:
            cat = st.selectbox("類別", options=CATEGORY_LIST, index=CATEGORY_LIST.index(d[5]) if d[5] in CATEGORY_LIST else 6)
        with col4:
            car = st.text_input("車號", value=d[4])
            
        desc = st.text_area("描述內容", value=d[6])
        
        btn_col1, btn_col2, btn_col3, _ = st.columns([1, 1, 1, 3])
        submit = btn_col1.form_submit_button("更新紀錄" if st.session_state.edit_mode else "確認送出")
        
        if not st.session_state.edit_mode:
            btn_col2.link_button("多元支付", "http://219.85.163.90:5010/")
        else:
            if btn_col2.form_submit_button("❌ 取消編輯"):
                st.session_state.edit_mode = False
                st.rerun()
        btn_col3.link_button("簡訊系統", "https://umc.fetnet.net/#/menu/login")

        if submit:
            if staff != "請選擇填單人" and station != "請選擇或輸入關鍵字搜尋":
                row_data = [f_dt, station, caller, phone, car.upper(), cat, desc, staff]
                if st.session_state.edit_mode:
                    sheet.update(f"A{st.session_state.edit_row_idx}:H{st.session_state.edit_row_idx}", [row_data])
                    st.session_state.edit_mode = False
                    st.success("紀錄已更新！")
                else:
                    sheet.append_row(row_data)
                    st.success("紀錄已送出！")
                st.rerun()
            else:
                st.error("請填寫完整資訊（場站與填單人）")

    # --- 最近紀錄 (智慧輪動 + 保底) ---
    st.markdown("---")
    st.subheader("🔍 最近紀錄 (交班動態)")
    if sheet:
        data = sheet.get_all_values()
        if len(data) > 1:
            df_hist = pd.DataFrame(data[1:], columns=data[0])
            search_q = st.text_input("🔍 搜尋紀錄 (輸入車號/場站/姓名/電話)").strip().lower()
            
            # 8小時智慧過濾
            df_hist['dt_obj'] = pd.to_datetime(df_hist.iloc[:, 0], errors='coerce')
            limit_time = now_ts.replace(tzinfo=None) - datetime.timedelta(hours=8)
            
            if search_q:
                display_df = df_hist[df_hist.apply(lambda r: r.astype(str).str.lower().str.contains(search_q).any(), axis=1)]
            else:
                display_df = df_hist[df_hist['dt_obj'] >= limit_time]
                if display_df.empty: # 保底顯示最後 3 筆
                    display_df = df_hist.tail(3)
            
            # 顯示表格 (手動列出以支援編輯按鈕)
            for idx, row in display_df.iloc[::-1].iterrows():
                actual_idx = idx + 2
                cols = st.columns([1.5, 1, 0.8, 1, 0.8, 2.5, 0.8, 0.5, 0.5])
                cols[0].write(row[0]); cols[1].write(row[1]); cols[2].write(row[2])
                cols[3].write(row[3]); cols[4].write(row[4]); cols[5].write(row[6])
                cols[6].write(row[7])
                if cols[7].button("📝", key=f"edit_{actual_idx}"):
                    st.session_state.edit_mode = True
                    st.session_state.edit_row_idx = actual_idx
                    st.session_state.edit_data = list(row[:8])
                    st.rerun()
                cols[8].checkbox(" ", key=f"chk_{actual_idx}", label_visibility="collapsed")

with tab2:
    st.title("📊 數據統計與分析")
    if st.text_input("管理員密碼", type="password") == "kevin198":
        if sheet:
            raw_data = sheet.get_all_values()
            df_stat = pd.DataFrame(raw_data[1:], columns=raw_data[0])
            df_stat['日期'] = pd.to_datetime(df_stat.iloc[:, 0]).dt.date
            
            date_range = st.date_input("選擇統計週期", value=[datetime.date.today() - datetime.timedelta(days=7), datetime.date.today()])
            
            if len(date_range) == 2:
                mask = (df_stat['日期'] >= date_range[0]) & (df_stat['日期'] <= date_range[1])
                filter_df = df_stat.loc[mask]
                
                # 下載按鈕
                csv = filter_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 下載統計報表 (CSV)", csv, f"應安客服報表_{date_range[0]}_to_{date_range[1]}.csv", "text/csv")
                
                # --- 4K 投影增強圖表函式 ---
                def apply_4k_style(fig, title):
                    fig.update_layout(
                        font=dict(family="Arial Black", size=20, color="#000000"),
                        title=dict(text=f"<b>{title}</b>", font=dict(size=30)),
                        paper_bgcolor='white', plot_bgcolor='white',
                        margin=dict(t=100, b=150),
                        showlegend=True
                    )
                    fig.update_xaxes(tickfont=dict(size=18, weight='bold', color='black'), linecolor='black', linewidth=2)
                    fig.update_yaxes(tickfont=dict(size=18, weight='bold', color='black'), linecolor='black', linewidth=2)
                    fig.update_traces(texttemplate='%{y}', textposition='outside', textfont=dict(size=18, color='black'))
                    return fig

                # 1. 雙週成長對比 (2/24 核心功能)
                st.subheader("⏳ 雙週案件類比對比")
                today = datetime.date.today()
                last_week_start = today - datetime.timedelta(days=13)
                last_week_end = today - datetime.timedelta(days=7)
                this_week_start = today - datetime.timedelta(days=6)
                
                def get_week_data(start, end, label):
                    d = df_stat[(df_stat['日期'] >= start) & (df_stat['日期'] <= end)]
                    c = d['類別'].value_counts().reindex(CATEGORY_LIST, fill_value=0).reset_index()
                    c.columns = ['類別', '件數']; c['週期'] = label
                    return c
                
                comp_df = pd.concat([get_week_data(last_week_start, last_week_end, "上週"), 
                                     get_week_data(this_week_start, today, "本週")])
                
                fig_comp = px.bar(comp_df, x='類別', y='件數', color='週期', barmode='group',
                                  color_discrete_map={"本週": "#1f77b4", "上週": "#ff7f0e"})
                st.plotly_chart(apply_4k_style(fig_comp, "雙週案件類別對比 (4K 投影版)"), use_container_width=True)

                # 2. 場站 Top 10
                st.divider()
                st.subheader("🏢 熱門場站排行 (Top 10)")
                top_stations = filter_df['場站名稱'].value_counts().head(10).reset_index()
                top_stations.columns = ['場站', '件數']
                fig_st = px.bar(top_stations, x='場站', y='件數', color='場站', color_discrete_sequence=px.colors.qualitative.Prism)
                st.plotly_chart(apply_4k_style(fig_st, "場站報修排名"), use_container_width=True)

st.caption("© 2026 應安客服系統 ")
