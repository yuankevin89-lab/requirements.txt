import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import datetime
import pandas as pd
import pytz
import plotly.express as px
import plotly.graph_objects as go
import re

# --- 1. 頁面基本設定與專業樣式 ---
st.set_page_config(page_title="應安客服雲端登記系統", page_icon="📝", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display: none;}
    .block-container {padding-top: 2rem; padding-bottom: 1rem;}
    * { color: #000000 !important; font-family: "Microsoft JhengHei", "Arial Black", sans-serif !important; }
    .hover-text {
        cursor: help; color: #1f77b4; text-decoration: underline dotted;
        display: inline-block; width: 100%; white-space: nowrap;
        overflow: hidden; text-overflow: ellipsis;
    }
    </style>
    """, unsafe_allow_html=True)

tw_timezone = pytz.timezone('Asia/Taipei')

# --- 2. 初始資料與連線 ---
STATION_LIST = [
    "請選擇或輸入關鍵字搜尋", "華視光復","電視台","華視二","文教五","華視五","文教一","文教二","文教六","文教三",
    "延吉場","大安場","信義大安","樂業場","仁愛場","四維場","濟南一場","濟南二場","松智場","松勇二","六合市場",
    "統領場","信義安和","僑信場","台北民生場","美麗華場","基湖場","北安場","龍江場","農安場",
    "民權西場","承德場","承德三","詔安場","大龍場","延平北場","雙連","中山市場","助安中山場","南昌場","博愛場","金山場",
    "金華場","通化","杭南一","復興南","仁愛逸仙","興岩社福大樓","木柵社宅","泉州場","汀州場",
    "北平東場","福州場","水源市場","重慶南","西寧市場","西園國宅","復興北","宏泰民生","新洲美福善場","福善一",
    "石牌二","中央北","紅毛城","三玉","士林場","永平社宅","涼州場","大龍峒社宅","成功場","洲子場","環山",
    "文湖場","民善場","行愛場","新明場","德明研推","東湖場","舊宗社宅","行善五","秀山機車","景平","環狀A機車",
    "樹林水源","土城中華場","光正","合宜A2","合宜A3","昆陽一","合宜A6東","合宜A6西","裕民","中央二","中央三","陶都場",
    "板橋文化1F","板橋文化B1","佳音-同安","佳音-竹林","青潭國小","林口文化","秀峰","興南場","中和莊敬",
    "三重永福","徐匯場","蘆洲保和","蘆洲三民","榮華場","富貴場","鄉長二","汐止忠孝","新台五路","蘆竹場",
    "龜山興富","竹東長春","竹南中山","銅鑼停一","台中黎明場","後龍","台中復興","台中復興二","文心場",
    "台中大和屋","一銀北港","西螺","虎尾","民德","衛民","衛民二場","台南北門","台南永福","台南國華",
    "台南民權","善化","仁德","台南中華場","致穩","台南康樂場","金財神","蘭井","佳音西園",
    "中華信義","敦南場","中華北門場", "其他(未登入場站)"
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

def format_car_number(car_str):
    if not car_str: return ""
    clean_s = car_str.replace("-", "").strip().upper()
    match = re.match(r"([A-Z]+)([0-9]+)", clean_s)
    if match: return f"{match.group(1)}-{match.group(2)}"
    match_reverse = re.match(r"([0-9]+)([A-Z]+)", clean_s)
    if match_reverse: return f"{match_reverse.group(1)}-{match_reverse.group(2)}"
    return clean_s

# --- 修正初始化邏輯 ---
if "edit_mode" not in st.session_state: st.session_state.edit_mode = False
if "edit_row_idx" not in st.session_state: st.session_state.edit_row_idx = None
if "edit_data" not in st.session_state: st.session_state.edit_data = [""] * 8
if "form_id" not in st.session_state: st.session_state.form_id = 0

tab1, tab2 = st.tabs(["📝 案件登記", "📊 數據統計分析"])

# --- Tab 1: 案件登記 ---
with tab1:
    st.title("📝 應安客服線上登記系統")
    now_ts = datetime.datetime.now(tw_timezone)
    
    with st.form(key=f"my_form_{st.session_state.form_id}", clear_on_submit=False):
        d = st.session_state.edit_data if st.session_state.edit_mode else [""]*8
        f_dt = d[0] if st.session_state.edit_mode else now_ts.strftime("%Y-%m-%d %H:%M")
        st.info(f"🕒 案件時間：{f_dt}" + (" (編輯模式)" if st.session_state.edit_mode else ""))
        c1, c2 = st.columns(2)
        with c1:
            station_name = st.selectbox("場站名稱", options=STATION_LIST, index=STATION_LIST.index(d[1]) if d[1] in STATION_LIST else 0)
            caller_name = st.text_input("姓名", value=d[2])
        with c2:
            user_name = st.selectbox("填單人", options=STAFF_LIST, index=STAFF_LIST.index(d[7]) if d[7] in STAFF_LIST else 0)
            caller_phone = st.text_input("電話", value=d[3])
        c3, c4 = st.columns(2)
        with c3:
            category = st.selectbox("類別", options=CATEGORY_LIST, index=CATEGORY_LIST.index(d[5]) if d[5] in CATEGORY_LIST else 6)
        with c4: car_num = st.text_input("車號", value=d[4])
        description = st.text_area("描述內容", value=d[6])
        
        btn_c1, btn_c2, _ = st.columns([1, 1, 4])
        submit_btn = btn_c1.form_submit_button("確認送出" if not st.session_state.edit_mode else "更新紀錄")
        if st.session_state.edit_mode:
            if btn_c2.form_submit_button("❌ 取消編輯"):
                st.session_state.edit_mode = False
                st.session_state.edit_row_idx = None
                st.session_state.edit_data = [""]*8
                st.session_state.form_id += 1; st.rerun()

        if submit_btn:
            if user_name != "請選擇填單人" and station_name != "請選擇或輸入關鍵字搜尋":
                final_car_num = format_car_number(car_num)
                row = [f_dt, station_name, caller_name, caller_phone, final_car_num, category, description, user_name]
                if st.session_state.edit_mode:
                    sheet.update(f"A{st.session_state.edit_row_idx}:H{st.session_state.edit_row_idx}", [row])
                    st.session_state.edit_mode = False; st.session_state.edit_row_idx = None; st.session_state.edit_data = [""]*8
                else: sheet.append_row(row)
                st.session_state.form_id += 1; st.rerun()
            else: st.error("請完整填寫場站與填單人")

    # --- 最近紀錄 ---
    st.markdown("---")
    if sheet:
        all_raw = sheet.get_all_values()
        if len(all_raw) > 1:
            valid_rows = [(i+2, r) for i, r in enumerate(all_raw[1:]) if any(str(c).strip() for c in r)]
            display_list = valid_rows[-10:]
            col_widths = [0.9, 0.6, 0.9, 1.2, 1.0, 1.5, 5.1, 0.8, 0.6, 0.6]
            cols = st.columns(col_widths)
            headers = ["時間", "場站", "姓名", "電話", "車號", "類別", "描述摘要", "填單人", "編輯", "標記"]
            for col, t in zip(cols, headers): col.markdown(f"**{t}**")
            for r_idx, r_val in reversed(display_list):
                c = st.columns(col_widths)
                c[0].write(r_val[0]); c[1].write(r_val[1]); c[2].write(r_val[2]); c[3].write(r_val[3]); c[4].write(r_val[4]); c[5].write(r_val[5])
                clean_d = r_val[6].replace('\n', ' ')
                short_d = f"{clean_d[:35]}..." if len(clean_d) > 35 else clean_d
                c[6].markdown(f'<div class="hover-text" title="{clean_d}">{short_d}</div>', unsafe_allow_html=True)
                c[7].write(r_val[7])
                if c[8].button("📝", key=f"ed_{r_idx}"):
                    st.session_state.edit_mode = True; st.session_state.edit_row_idx = r_idx; st.session_state.edit_data = r_val; st.rerun()
                c[9].checkbox(" ", key=f"chk_{r_idx}")

# --- Tab 2: 數據統計 (順序鎖定) ---
with tab2:
    st.title("📊 數據統計分析")
    if st.text_input("管理員密碼", type="password") == "kevin198":
        if sheet:
            raw_stat = [r for r in sheet.get_all_values() if any(f.strip() for f in r)]
            if len(raw_stat) > 1:
                hdr = raw_stat[0]
                df_s = pd.DataFrame(raw_stat[1:], columns=hdr)
                df_s[hdr[0]] = pd.to_datetime(df_s[hdr[0]], errors='coerce')
                df_s = df_s.dropna(subset=[hdr[0]])
                wk_df = df_s.tail(500)
                config_4k = {'toImageButtonOptions': {'format': 'png', 'height': 1080, 'width': 1920, 'scale': 2}}

                def apply_bold_style(fig, title_text, is_stacked=False):
                    fig.update_layout(
                        font=dict(family="Microsoft JhengHei, Arial Black", size=20, color="#000000"),
                        title=dict(text=f"<b>{title_text}</b>", font=dict(size=34), x=0.5, xanchor='center'),
                        paper_bgcolor='white', plot_bgcolor='white', showlegend=True if is_stacked else False
                    )
                    return fig

                # 1. 📈 每日案件量趨勢圖
                df_s['Date'] = df_s[hdr[0]].dt.date
                trend_df = df_s.groupby('Date').size().reset_index(name='件數')
                st.plotly_chart(apply_bold_style(px.line(trend_df, x='Date', y='件數', text='件數', markers=True), "📈 每日案件量趨勢圖"), use_container_width=True)
                
                # 2. ⏳ 雙週案件類別對比分析
                t_data = df_s.copy(); t_data['D'] = t_data[hdr[0]].dt.date
                td = datetime.date.today()
                tw_s, lw_s, lw_e = td-datetime.timedelta(days=6), td-datetime.timedelta(days=13), td-datetime.timedelta(days=7)
                def get_c(s, e, l):
                    m = (t_data['D'] >= s) & (t_data['D'] <= e)
                    r = t_data.loc[m][hdr[5]].value_counts().reindex(CATEGORY_LIST, fill_value=0).reset_index(name='件數')
                    r.columns = ['類別', '件數']; r['週期'] = l; return r
                df_c = pd.concat([get_c(lw_s, lw_e, "上週"), get_c(tw_s, td, "本週")])
                st.plotly_chart(apply_bold_style(px.bar(df_c, x='類別', y='件數', color='週期', barmode='group', text='件數'), "⏳ 雙週案件類別對比分析", is_stacked=True), use_container_width=True)

                g1, g2 = st.columns(2)
                with g1:
                    # 3. 📂 當前區間案件分佈
                    cat_c = wk_df[hdr[5]].value_counts().reset_index(); cat_c.columns=['類別','件數']
                    st.plotly_chart(apply_bold_style(px.bar(cat_c, x='類別', y='件數', text='件數', color='類別', color_discrete_map=CATEGORY_COLOR_MAP), "📂 當前區間案件分佈"), use_container_width=True)
                with g2:
                    # 4. 🏢 場站排名 (Top 10)
                    st_counts = wk_df[hdr[1]].value_counts().reset_index().head(10)
                    st_counts.columns = ['場站', '件數']
                    st.plotly_chart(apply_bold_style(px.bar(st_counts, x='場站', y='件數', text='件數', color='場站'), "🏢 場站排名 (Top 10)"), use_container_width=True)

                # 5. 🔍 場站 vs. 異常類別分析 (修正點)
                top10_names = st_counts['場站'].tolist()
                cross_df = wk_df[wk_df[hdr[1]].isin(top10_names)].copy()
                cross_df.rename(columns={hdr[1]: "場站", hdr[5]: "異常類別"}, inplace=True)
                cross = cross_df.groupby(["場站", "異常類別"]).size().reset_index(name='件數')
                st.plotly_chart(apply_bold_style(px.bar(cross, x='場站', y='件數', color="異常類別", text='件數', color_discrete_map=CATEGORY_COLOR_MAP), "🔍 場站 vs. 異常類別分析 (Top 10)", is_stacked=True), use_container_width=True)
                
                # 6. 📈 類別精確統計
                st.plotly_chart(apply_bold_style(px.bar(cat_c, y='類別', x='件數', orientation='h', text='件數', color='類別', color_discrete_map=CATEGORY_COLOR_MAP), "📈 類別精確統計"), use_container_width=True)

st.caption("© 2026 應安客服系統 - 2026-03-09 終極基準修正版")
