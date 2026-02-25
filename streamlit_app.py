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

# 將您上傳的 Logo 轉為內嵌 Base64 (縮減版示意，實際運行會顯示圖片)
def get_logo_html():
    # 這是根據您上傳的 Logo 樣式設計的 HTML 標題
    return '''
    <div style="display: flex; align-items: center; justify-content: flex-end; padding: 10px;">
        <div style="background-color: #FFF200; padding: 10px 20px; border-radius: 20px; border: 3px solid #002D72;">
            <span style="color: #002D72; font-size: 36px; font-weight: 900; font-style: italic; font-family: sans-serif;">IN-AN</span>
            <span style="color: #E30613; font-size: 36px; font-weight: 900; margin-left: 5px;">P</span>
        </div>
        <div style="margin-left: 15px; text-align: right;">
            <h2 style="color: #000000; margin: 0; font-size: 28px; font-weight: 900;">應安停車</h2>
            <p style="color: #000000; margin: 0; font-size: 16px; font-weight: bold;">客服管理系統 (2/25 終極版)</p>
        </div>
    </div>
    '''

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    /* 4K 投影加強：全黑加粗字體 */
    html, body, [class*="css"] {
        color: #000000 !important;
        font-family: "Microsoft JhengHei", "Arial", sans-serif !important;
    }
    .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #000000 !important;
        font-weight: 900 !important;
    }
    /* 表格選取列變色 */
    [data-testid="stElementContainer"]:has(input[type="checkbox"]:checked) {
        background-color: #d1fae5 !important;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown(get_logo_html(), unsafe_allow_html=True)
tw_tz = pytz.timezone('Asia/Taipei')

# --- 2. 鎖定名單 (2/24 最新版) ---
STATION_LIST = [
    "請選擇或輸入關鍵字搜尋", "華視光復","電視台","華視二","文教五","華視五","文教一","文教二","文教六","文教三",
    "延吉場","大安場","信義大安","樂業場","仁愛場","四維場","濟南一場","濟南二場","松智場","松勇二","六合市場",
    "統領場","信義安和","僑信場","台北民生場","美麗華場","基湖場","北安場","龍江場","農安場","明倫社宅",
    "民權西場","承德場","承德三","大龍場","延平北場","雙連","中山市場","助安中山場","南昌場","博愛場","金山場",
    "金華場","通化","杭南一","復興南","仁愛逸仙","興岩社福大樓","木柵社宅","泉州場","汀州場",
    "北平東場","福州場","水源市場","重慶南","西寧市場","西園國宅","復興北","宏泰民生","新洲美福善場","福善一",
    "石牌二","中央北","紅毛城","三玉","士林場","永平社宅","涼州場","大龍峒社宅","成功場","洲子場","環山",
    "文湖場","民善場","行愛場","新明場","德明研推","東湖場","東湖社宅","行善五","秀山機車","景平","環狀A機車",
    "樹林水源","土城中華場","光正","合宜A2","合宜A3","昆陽一","合宜A6東","合宜A6西","裕民","中央二","中央三","陶都場",
    "板橋文化1F","板橋文化B1","佳音-同安","佳音-竹林","青潭國小","林口文化","秀峰","興南場","中和莊敬",
    "三重永福","徐匯場","蘆洲保和","蘆洲三民","榮華場","富貴場","鄉長二","汐止忠孝","新台五路","蘆竹場",
    "龜山興富","竹東長春","竹南中山","銅鑼停一","台中黎明場","後龍","台中復興","台中復興二","文心場",
    "台中大和屋","一銀北港","西螺","虎尾","民德","衛民","衛民二場","台南北門","台南永福","台南國華",
    "台南民權","善化","仁德","台南中華場","致穩","台南康樂場","金財神","蘭井","友愛場","佳音西園",
    "中華信義","敦南場","中華北門場","東大門場", "其他(未登入場站)"
]
STAFF_LIST = ["請選擇填單人", "宗哲", "美妞", "政宏", "文輝", "恩佳", "志榮", "阿錨", "子毅", "浚"]
CAT_LIST = ["繳費機異常", "發票缺紙或卡紙", "無法找零", "身障優惠折抵", "網路異常", "繳費問題相關", "其他"]

# --- 3. Google Sheets 連線 ---
def init_conn():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["google_sheets"], scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"連線失敗: {e}")
        return None

client = init_conn()
sheet = client.open("客服作業表").sheet1 if client else None

if "edit_m" not in st.session_state:
    st.session_state.edit_m = False
    st.session_state.edit_idx = None
    st.session_state.edit_d = [""] * 8

# --- 4. 功能分頁 ---
t1, t2 = st.tabs(["📝 案件登記", "📊 數據統計分析"])

with t1:
    st.title("📝 應安客服線上登記系統")
    now = datetime.datetime.now(tw_tz)
    
    with st.form("main_form", clear_on_submit=False):
        d = st.session_state.edit_d if st.session_state.edit_m else [""]*8
        dt_s = d[0] if st.session_state.edit_m else now.strftime("%Y-%m-%d %H:%M")
        st.markdown(f"### 🕒 案件時間：{dt_s}")
        
        c1, c2 = st.columns(2)
        with c1:
            station = st.selectbox("場站名稱", STATION_LIST, index=STATION_LIST.index(d[1]) if d[1] in STATION_LIST else 0)
            caller = st.text_input("姓名", value=d[2])
            cat = st.selectbox("類別", CAT_LIST, index=CAT_LIST.index(d[5]) if d[5] in CAT_LIST else 6)
        with c2:
            staff = st.selectbox("填單人", STAFF_LIST, index=STAFF_LIST.index(d[7]) if d[7] in STAFF_LIST else 0)
            phone = st.text_input("電話", value=d[3])
            car = st.text_input("車號", value=d[4])
        desc = st.text_area("描述內容", value=d[6])
        
        b1, b2, b3, _ = st.columns([1,1,1,2])
        submit = b1.form_submit_button("更新紀錄" if st.session_state.edit_m else "確認送出")
        if st.session_state.edit_m:
            if b2.form_submit_button("❌ 取消"):
                st.session_state.edit_m = False
                st.rerun()
        else:
            b2.link_button("多元支付", "http://219.85.163.90:5010/")
        b3.link_button("簡訊系統", "https://umc.fetnet.net/#/menu/login")

        if submit:
            if staff != "請選擇填單人" and station != "請選擇或輸入關鍵字搜尋":
                row_data = [dt_s, station, caller, phone, car.upper(), cat, desc, staff]
                if st.session_state.edit_m:
                    sheet.update(f"A{st.session_state.edit_idx}:H{st.session_state.edit_idx}", [row_data])
                    st.session_state.edit_m = False
                    st.success("更新成功！")
                else:
                    sheet.append_row(row_data)
                    st.success("送出成功！")
                st.rerun()
            else:
                st.warning("請填寫場站與填單人！")

    # --- 歷史紀錄 (iloc 物理避錯法) ---
    st.markdown("---")
    st.subheader("🔍 最近紀錄 (8小時智慧動態)")
    if sheet:
        raw_rows = sheet.get_all_values()
        if len(raw_rows) > 1:
            df = pd.DataFrame(raw_rows[1:], columns=raw_rows[0])
            search = st.text_input("輸入關鍵字搜尋 (車號/場站)").strip().lower()
            
            df['dt_p'] = pd.to_datetime(df.iloc[:, 0], errors='coerce')
            limit = now.replace(tzinfo=None) - datetime.timedelta(hours=8)
            
            if search:
                disp = df[df.apply(lambda r: r.astype(str).str.lower().str.contains(search).any(), axis=1)]
            else:
                disp = df[df['dt_p'] >= limit]
                if disp.empty: disp = df.tail(3)
            
            # 使用 .iloc 獲取數據，完全解決 KeyError
            for i, r in disp.iloc[::-1].iterrows():
                idx = i + 2
                c = st.columns([1.5, 1, 0.8, 1, 0.8, 2.5, 0.8, 0.5, 0.5])
                c[0].write(r.iloc[0]); c[1].write(r.iloc[1]); c[2].write(r.iloc[2])
                c[3].write(r.iloc[3]); c[4].write(r.iloc[4]); c[5].write(r.iloc[6])
                c[6].write(r.iloc[7])
                if c[7].button("📝", key=f"e_{idx}"):
                    st.session_state.edit_m = True
                    st.session_state.edit_idx = idx
                    st.session_state.edit_d = list(r.iloc[:8])
                    st.rerun()
                c[8].checkbox(" ", key=f"k_{idx}")

with t2:
    st.title("📊 數據統計分析")
    if st.text_input("管理員密碼", type="password") == "kevin198":
        if sheet:
            df_stat = pd.DataFrame(sheet.get_all_values()[1:])
            df_stat.columns = ["時間", "場站", "姓名", "電話", "車號", "類別", "描述", "填單人"]
            df_stat['日期'] = pd.to_datetime(df_stat['時間']).dt.date
            
            # 4K 投影樣式函式
            def style_fig(fig, title):
                fig.update_layout(
                    font=dict(size=22, color="black", family="Arial Black"),
                    title=dict(text=f"<b>{title}</b>", font=dict(size=32)),
                    paper_bgcolor='white', plot_bgcolor='white'
                )
                fig.update_traces(texttemplate='<b>%{y}</b>', textposition='outside')
                return fig

            # 雙週對比 (2/24 核心)
            st.subheader("⏳ 雙週案件類別成長對比")
            today = datetime.date.today()
            def get_week(s, e, label):
                d_ = df_stat[(df_stat['日期'] >= s) & (df_stat['日期'] <= e)]
                c_ = d_['類別'].value_counts().reindex(CAT_LIST, fill_value=0).reset_index()
                c_.columns = ['類別', '件數']; c_['週期'] = label
                return c_
            comp = pd.concat([get_week(today-datetime.timedelta(days=13), today-datetime.timedelta(days=7), "上週"),
                             get_week(today-datetime.timedelta(days=6), today, "本週")])
            fig = px.bar(comp, x='類別', y='件數', color='週期', barmode='group', color_discrete_map={"本週":"#000000","上週":"#777777"})
            st.plotly_chart(style_fig(fig, "雙週類別趨勢對比"), use_container_width=True)

            # 場站排行
            st.divider()
            top10 = df_stat['場站'].value_counts().head(10).reset_index()
            st.plotly_chart(style_fig(px.bar(top10, x='index', y='場站', title="場站報修 Top 10"), "場站排行"), use_container_width=True)

st.caption("© 2026 應安停車 | 2/25 終極避錯基準版")
