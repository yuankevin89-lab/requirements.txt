import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import datetime
import pandas as pd
import pytz
import plotly.express as px
import base64
import os

# --- 1. 頁面基本設定 ---
st.set_page_config(page_title="應安客服雲端登記系統", page_icon="📝", layout="wide")

# 強制讀取並轉碼您的原始 Logo (公司LOGO-02.png)
def get_original_logo():
    logo_path = "公司LOGO-02.png"
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
            return f'''
            <div style="position: absolute; top: -60px; right: 10px;">
                <img src="data:image/png;base64,{data}" width="280">
            </div>
            '''
    return '<div style="text-align:right; color:red;">[請確認 Logo 檔案已在資料夾中]</div>'

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    /* 4K 投影增強：文字維持經典比例但純黑加粗 */
    * { color: #000000 !important; font-family: "Microsoft JhengHei", sans-serif !important; }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { font-weight: 900 !important; }
    /* 調整表單輸入框大小 */
    .stTextInput input, .stSelectbox div { font-size: 20px !important; font-weight: bold !important; }
    /* 歷史紀錄列樣式 - 回歸 2/17 舒適感 */
    .record-row { border-bottom: 1px solid #ddd; padding: 10px 0; align-items: center; }
    </style>
    """, unsafe_allow_html=True)

st.markdown(get_original_logo(), unsafe_allow_html=True)
tw_tz = pytz.timezone('Asia/Taipei')

# --- 2. 鎖定清單 (維持 2/24 最新) ---
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

# --- 3. 連線設定 ---
def init_conn():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["google_sheets"], scope)
    return gspread.authorize(creds)

client = init_conn()
sheet = client.open("客服作業表").sheet1

if "edit_m" not in st.session_state:
    st.session_state.edit_m = False
    st.session_state.edit_idx = None
    st.session_state.edit_d = [""] * 8

# --- 4. 功能分頁 ---
t1, t2 = st.tabs(["📝 案件登記", "📊 數據統計分析"])

with t1:
    st.title("📝 應安客服線上登記系統")
    now = datetime.datetime.now(tw_tz)
    
    with st.form("reg_form"):
        d = st.session_state.edit_d if st.session_state.edit_m else [""]*8
        dt_str = d[0] if st.session_state.edit_m else now.strftime("%Y-%m-%d %H:%M")
        st.markdown(f"### 🕒 案件時間：{dt_str}")
        
        c1, c2 = st.columns(2)
        station = c1.selectbox("場站名稱", STATION_LIST, index=STATION_LIST.index(d[1]) if d[1] in STATION_LIST else 0)
        staff = c2.selectbox("填單人", STAFF_LIST, index=STAFF_LIST.index(d[7]) if d[7] in STAFF_LIST else 0)
        caller = c1.text_input("姓名", d[2])
        phone = c2.text_input("電話", d[3])
        cat = c1.selectbox("類別", CAT_LIST, index=CAT_LIST.index(d[5]) if d[5] in CAT_LIST else 6)
        car = c2.text_input("車號", d[4])
        desc = st.text_area("描述內容", d[6])
        
        b1, b2, b3, _ = st.columns([1,1,1,3])
        sub = b1.form_submit_button("更新紀錄" if st.session_state.edit_m else "確認送出")
        if st.session_state.edit_m:
            if b2.form_submit_button("❌ 取消"):
                st.session_state.edit_m = False
                st.rerun()
        else:
            b2.link_button("多元支付", "http://219.85.163.90:5010/")
        b3.link_button("簡訊系統", "https://umc.fetnet.net/#/menu/login")

        if sub:
            if staff != "請選擇填單人" and station != "請選擇或輸入關鍵字搜尋":
                new_row = [dt_str, station, caller, phone, car.upper(), cat, desc, staff]
                if st.session_state.edit_m:
                    sheet.update(f"A{st.session_state.edit_idx}:H{st.session_state.edit_idx}", [new_row])
                    st.session_state.edit_m = False
                else:
                    sheet.append_row(new_row)
                st.rerun()

    # --- 歷史紀錄：回歸 2/17 舒適佈局 + 4K 加粗 ---
    st.markdown("---")
    st.subheader("🔍 最近紀錄 (8小時智慧輪動)")
    raw = sheet.get_all_values()
    if len(raw) > 1:
        df = pd.DataFrame(raw[1:], columns=raw[0])
        sq = st.text_input("搜尋紀錄 (車號/場站/姓名)").strip().lower()
        df['dt_obj'] = pd.to_datetime(df.iloc[:,0], errors='coerce')
        
        if sq:
            disp = df[df.apply(lambda r: r.astype(str).str.lower().str.contains(sq).any(), axis=1)]
        else:
            limit = now.replace(tzinfo=None) - datetime.timedelta(hours=8)
            disp = df[df['dt_obj'] >= limit]
            if disp.empty: disp = df.tail(3)
            
        # 建立舒適的欄位標題列
        h = st.columns([1.5, 1, 0.8, 1, 0.8, 2.5, 0.8, 0.4, 0.4])
        h[0].write("**日期/時間**"); h[1].write("**場站**"); h[2].write("**姓名**")
        h[3].write("**電話**"); h[4].write("**車號**"); h[5].write("**摘要描述**")
        h[6].write("**填單**")

        for i, r in disp.iloc[::-1].iterrows():
            idx = i + 2
            cols = st.columns([1.5, 1, 0.8, 1, 0.8, 2.5, 0.8, 0.4, 0.4])
            # 使用 iloc 確保絕對位置讀取，解決 KeyError
            cols[0].write(f"**{r.iloc[0]}**"); cols[1].write(r.iloc[1]); cols[2].write(r.iloc[2])
            cols[3].write(r.iloc[3]); cols[4].write(r.iloc[4]); cols[5].write(r.iloc[6])
            cols[6].write(r.iloc[7])
            if cols[7].button("📝", key=f"ed_{idx}"):
                st.session_state.edit_m = True
                st.session_state.edit_idx = idx
                st.session_state.edit_d = list(r.iloc[:8])
                st.rerun()
            cols[8].checkbox(" ", key=f"ck_{idx}")

with t2:
    st.title("📊 數據統計分析")
    if st.text_input("管理密碼", type="password") == "kevin198":
        raw = sheet.get_all_values()
        df_st = pd.DataFrame(raw[1:], columns=raw[0])
        df_st['date'] = pd.to_datetime(df_st.iloc[:,0]).dt.date
        
        # 雙週對比柱狀圖 (2/24 核心)
        st.subheader("⏳ 雙週案件類別成長對比")
        td = datetime.date.today()
        def get_c(s, e, l):
            tmp = df_st[(df_st['date']>=s) & (df_st['date']<=e)]
            c = tmp.iloc[:,5].value_counts().reindex(CAT_LIST, fill_value=0).reset_index()
            c.columns=['類別','件數']; c['週期']=l
            return c
        comp = pd.concat([get_c(td-datetime.timedelta(days=13), td-datetime.timedelta(days=7), "上週"),
                         get_c(td-datetime.timedelta(days=6), td, "本週")])
        
        fig = px.bar(comp, x='類別', y='件數', color='週期', barmode='group', 
                     color_discrete_map={"本週":"#000000","上週":"#777777"})
        fig.update_layout(font=dict(size=20, color="black", family="Arial Black"), 
                          title_font_size=28, paper_bgcolor='white', plot_bgcolor='white')
        fig.update_traces(texttemplate='%{y}', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)

st.caption("© 2026 應安停車 | 2/25 基準鎖定版")
