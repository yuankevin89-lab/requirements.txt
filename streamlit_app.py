import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import datetime
import pandas as pd
import pytz
import plotly.express as px
import base64
from io import BytesIO
from PIL import Image

# --- 1. 頁面基本設定與 Base64 Logo 內嵌技術 ---
st.set_page_config(page_title="應安客服雲端登記系統", page_icon="📝", layout="wide")

# 將您上傳的 Logo 轉換為 Base64 (避免檔案遺失報錯)
def get_base64_logo():
    try:
        # 直接讀取您提供的公司LOGO-02.png
        img = Image.open("公司LOGO-02.png")
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()
    except:
        return None

logo_base64 = get_base64_logo()

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display: none;}
    .block-container {padding-top: 1rem; padding-bottom: 1rem;}
    
    /* 右上角 Logo 定位區 */
    .logo-container {
        position: absolute;
        top: 0px;
        right: 0px;
        text-align: right;
        z-index: 1000;
    }
    
    /* 4K 投影增強：表格勾選變色 */
    [data-testid="stElementContainer"]:has(input[type="checkbox"]:checked) {
        background-color: #e8f5e9 !important;
        border-radius: 8px;
        padding: 10px;
        transition: background-color 0.3s ease;
        border: 1px solid #c8e6c9;
    }
    </style>
    """, unsafe_allow_html=True)

# 顯示右上角 Logo 或保底文字
with st.container():
    c1, c2 = st.columns([8.2, 1.8])
    with c2:
        if logo_base64:
            st.markdown(f'<div class="logo-container"><img src="data:image/png;base64,{logo_base64}" width="200"></div>', unsafe_allow_html=True)
        else:
            st.markdown("<h2 style='text-align:right; color:#1f77b4; margin:0;'>應安停車</h2><p style='text-align:right; color:gray; font-size:14px; margin:0;'>客服管理系統</p>", unsafe_allow_html=True)

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
    "身障優惠折抵": "blue", "繳費機異常": "green", "其他": "saddlebrown",
    "發票缺紙或卡紙": px.colors.qualitative.Safe[1], "無法找零": px.colors.qualitative.Safe[2],
    "網路異常": px.colors.qualitative.Safe[4], "繳費問題相關": px.colors.qualitative.Safe[5]
}

def init_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds_dict = st.secrets["google_sheets"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        return gspread.authorize(creds)
    except: return None

client = init_connection()
sheet = client.open("客服作業表").sheet1 if client else None

if "edit_mode" not in st.session_state:
    st.session_state.edit_mode, st.session_state.edit_row_idx, st.session_state.edit_data = False, None, [""]*8
if "form_id" not in st.session_state:
    st.session_state.form_id = 0

tab1, tab2 = st.tabs(["📝 案件登記", "📊 數據統計分析"])

# --- Tab 1: 案件登記 (包含保底機制與編輯模式) ---
with tab1:
    st.title("📝 應安客服線上登記系統")
    now_ts = datetime.datetime.now(tw_timezone)
    if st.session_state.edit_mode:
        st.warning(f"⚠️ 【編輯模式】- 正在更新第 {st.session_state.edit_row_idx} 列紀錄")

    with st.form(key=f"my_form_{st.session_state.form_id}", clear_on_submit=False):
        d = st.session_state.edit_data if st.session_state.edit_mode else [""]*8
        f_dt = d[0] if st.session_state.edit_mode else now_ts.strftime("%Y-%m-%d %H:%M")
        st.info(f"🕒 案件時間：{f_dt}")
        c1, c2 = st.columns(2)
        with c1:
            station_name = st.selectbox("場站名稱", options=STATION_LIST, index=STATION_LIST.index(d[1]) if d[1] in STATION_LIST else 0)
            caller_name = st.text_input("姓名", value=d[2])
        with c2:
            user_name = st.selectbox("填單人", options=STAFF_LIST, index=STAFF_LIST.index(d[7]) if d[7] in STAFF_LIST else 0, disabled=st.session_state.edit_mode)
            caller_phone = st.text_input("電話", value=d[3])
        c3, c4 = st.columns(2)
        with c3:
            d_cat = d[5]
            if d_cat == "繳費機故障": d_cat = "繳費機異常"
            category = st.selectbox("類別", options=CATEGORY_LIST, index=CATEGORY_LIST.index(d_cat) if d_cat in CATEGORY_LIST else 6)
        with c4: car_num = st.text_input("車號", value=d[4])
        description = st.text_area("描述內容", value=d[6])
        
        b1, b2, b3, _ = st.columns([1, 1, 1, 3])
        submit_btn = b1.form_submit_button("更新紀錄" if st.session_state.edit_mode else "確認送出")
        if st.session_state.edit_mode:
            if b2.form_submit_button("❌ 取消編輯"):
                st.session_state.edit_mode, st.session_state.edit_data = False, [""]*8
                st.session_state.form_id += 1
                st.rerun()
        else: b2.link_button("多元支付", "http://219.85.163.90:5010/")
        b3.link_button("簡訊系統", "https://umc.fetnet.net/#/menu/login")

        if submit_btn:
            if user_name != "請選擇填單人" and station_name != "請選擇或輸入關鍵字搜尋":
                row = [f_dt, station_name, caller_name, caller_phone, car_num.upper(), category, description, user_name]
                if st.session_state.edit_mode:
                    sheet.update(f"A{st.session_state.edit_row_idx}:H{st.session_state.edit_row_idx}", [row])
                    st.session_state.edit_mode, st.session_state.edit_row_idx, st.session_state.edit_data = False, [""]*8
                else: sheet.append_row(row)
                st.session_state.form_id += 1 
                st.rerun()
            else: st.error("請正確選擇填單人與場站")

    st.markdown("---")
    st.subheader("🔍 最近紀錄 (交班動態)")
    if sheet:
        all_raw = sheet.get_all_values()
        if len(all_raw) > 1:
            v_rows = [(i+2, r) for i, r in enumerate(all_raw[1:]) if any(str(c).strip() for c in r)]
            sq = st.text_input("🔍 搜尋歷史紀錄", placeholder="輸入關鍵字...").strip().lower()
            limit_dt = (now_ts.replace(tzinfo=None)) - datetime.timedelta(hours=8)
            d_list = []
            if sq: d_list = [(idx, r) for idx, r in v_rows if any(sq in str(cell).lower() for cell in r)]
            else:
                for idx, r in v_rows:
                    try:
                        dt = pd.to_datetime(r[0]).replace(tzinfo=None)
                        if dt >= limit_dt: d_list.append((idx, r))
                    except: continue
                if not d_list: d_list = v_rows[-3:] # 2/24 智慧保底機制

            if d_list:
                cols = st.columns([1.8, 1.2, 0.8, 1.2, 1.0, 2.2, 0.8, 0.6, 0.6])
                headers = ["日期/時間", "場站", "姓名", "電話", "車號", "描述摘要", "填單人", "編輯", "標記"]
                for col, t in zip(cols, headers): col.markdown(f"**{t}**")
                for r_idx, r_val in reversed(d_list):
                    c = st.columns([1.8, 1.2, 0.8, 1.2, 1.0, 2.2, 0.8, 0.6, 0.6])
                    c[0].write(r_val[0]); c[1].write(r_val[1]); c[2].write(r_val[2]); c[3].write(r_val[3]); c[4].write(r_val[4])
                    c[5].write(r_val[6][:15]+"..." if len(r_val[6])>15 else r_val[6])
                    c[6].write(r_val[7])
                    if c[7].button("📝", key=f"ed_{r_idx}"):
                        st.session_state.edit_mode, st.session_state.edit_row_idx, st.session_state.edit_data = True, r_idx, r_val
                        st.rerun()
                    c[8].checkbox(" ", key=f"chk_{r_idx}", label_visibility="collapsed")

# --- Tab 2: 數據統計 (完整繼承 2/24 規格) ---
with tab2:
    st.title("📊 數據統計與分析")
    if st.text_input("管理員密碼", type="password", key="stat_pwd") == "kevin198":
        if sheet:
            raw_stat = [r for r in sheet.get_all_values() if any(f.strip() for f in r)]
            if len(raw_stat) > 1:
                hdr = raw_stat[0]
                df_s = pd.DataFrame(raw_stat[1:], columns=hdr)
                df_s[hdr[0]] = pd.to_datetime(df_s[hdr[0]], errors='coerce')
                df_s = df_s.dropna(subset=[hdr[0]])
                
                c_range = st.date_input("📅 選擇指定統計週期", value=[])
                wk_df = df_s.loc[(df_s[hdr[0]].dt.date >= c_range[0]) & (df_s[hdr[0]].dt.date <= c_range[1])] if len(c_range) == 2 else df_s.tail(300)

                if not wk_df.empty:
                    # CSV 下載按鈕 (2/24 補齊)
                    csv = wk_df.to_csv(index=False).encode('utf-8-sig')
                    st.download_button("📥 下載統計報表 (CSV)", csv, f"應安報表_{datetime.date.today()}.csv", "text/csv")
                    
                    st.divider()
                    config_4k = {'toImageButtonOptions': {'format': 'png', 'height': 1080, 'width': 1920, 'scale': 2}}

                    def apply_4k_style(fig, title_text, is_stacked=False, is_h=False):
                        leg = dict(font=dict(size=18, color="#000000"), orientation="v", yanchor="top", y=1, xanchor="left", x=1.02) if (is_stacked or "對比" in title_text) else None
                        fig.update_layout(
                            font=dict(family="Arial Black", size=20, color="#000000"),
                            title=dict(text=f"<b>{title_text}</b>", font=dict(size=34), y=0.96, x=0.5, xanchor='center'),
                            paper_bgcolor='white', plot_bgcolor='white',
                            margin=dict(t=130, b=160, l=150 if is_h else 120, r=200 if (is_stacked or "對比" in title_text) else 120),
                            showlegend=True if (is_stacked or "對比" in title_text) else False, legend=leg
                        )
                        fig.update_xaxes(tickfont=dict(size=20, weight="bold", color="#000000"), linecolor='#000000', linewidth=3)
                        fig.update_yaxes(tickfont=dict(size=20, weight="bold", color="#000000"), linecolor='#000000', linewidth=3, gridcolor='#F0F0F0')
                        fig.update_traces(textfont=dict(size=20, weight="bold", color="#000000"))
                        return fig

                    # 1. 雙週成長對比 (2/24 核心功能：類別對齊 + 數字直顯)
                    st.subheader("⏳ 雙週案件類別成長對比")
                    t_data = df_s.copy(); t_data['D'] = t_data[hdr[0]].dt.date
                    td = datetime.date.today()
                    tw_s, lw_s, lw_e = td-datetime.timedelta(days=6), td-datetime.timedelta(days=13), td-datetime.timedelta(days=7)
                    def get_c(s, e, l):
                        m = (t_data['D'] >= s) & (t_data['D'] <= e)
                        r = t_data.loc[m][hdr[5]].value_counts().reindex(CATEGORY_LIST, fill_value=0).reset_index(name='件數')
                        r.columns = ['類別', '件數']; r['週期'] = l; return r
                    df_c = pd.concat([get_c(lw_s, lw_e, "上週"), get_c(tw_s, td, "本週")])
                    fig_c = px.bar(df_c, x='類別', y='件數', color='週期', barmode='group', text='件數', color_discrete_map={"本週": "#1f77b4", "上週": "#ff7f0e"})
                    st.plotly_chart(apply_4k_style(fig_c, "⏳ 案件類別：本週 vs 上週 對比"), use_container_width=True, config=config_4k)

                    # 其他 4K 統計圖表 (場站排行、類別分佈、堆疊分析)
                    st.divider()
                    g1, g2 = st.columns(2)
                    with g1:
                        cat_c = wk_df[hdr[5]].value_counts().reset_index(); cat_c.columns=['類別','件數']
                        fig1 = px.bar(cat_c, x='類別', y='件數', text='件數', color='類別', color_discrete_map=CATEGORY_COLOR_MAP)
                        st.plotly_chart(apply_4k_style(fig1, "📂 當前區間案件分佈"), use_container_width=True, config=config_4k)
                    with g2:
                        top10 = wk_df[hdr[1]].value_counts().head(10).index.tolist()
                        st_c = wk_df[wk_df[hdr[1]].isin(top10)][hdr[1]].value_counts().reset_index(); st_c.columns=['場站','件數']
                        fig2 = px.bar(st_c, x='場站', y='件數', text='件數', color='場站', color_discrete_sequence=px.colors.qualitative.Pastel)
                        st.plotly_chart(apply_4k_style(fig2, "🏢 場站排名 (Top 10)"), use_container_width=True, config=config_4k)

                    st.divider()
                    cross = wk_df[wk_df[hdr[1]].isin(top10)].groupby([hdr[1], hdr[5]]).size().reset_index(name='件數')
                    fig3 = px.bar(cross, x=hdr[1], y='件數', color=hdr[5], text='件數', color_discrete_map=CATEGORY_COLOR_MAP)
                    st.plotly_chart(apply_4k_style(fig3, "🔍 場站 vs. 異常類別 (Top 10)", is_stacked=True), use_container_width=True, config=config_4k)

                    st.divider()
                    fig4 = px.bar(cat_c, y='類別', x='件數', orientation='h', text='件數', color='類別', color_discrete_map=CATEGORY_COLOR_MAP)
                    st.plotly_chart(apply_4k_style(fig4, "📈 類別精確統計 (橫向)", is_h=True), use_container_width=True, config=config_4k)

st.caption("© 2026 應安客服系統 - 2/25 企業品牌最終基準版")
