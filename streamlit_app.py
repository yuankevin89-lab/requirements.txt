import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import datetime
import pandas as pd
import pytz
import plotly.express as px

# --- 1. 頁面基本設定與樣式 ---
st.set_page_config(page_title="應安客服雲端登記系統", page_icon="📝", layout="wide")

# 強制修正樣式，確保表格與文字換行正常
st.markdown("""
    <style>
    .block-container {padding-top: 2rem;}
    .stAppDeployButton {display: none;}
    .hover-text {
        cursor: help; color: #1f77b4; text-decoration: underline dotted;
        display: inline-block; width: 100%; white-space: nowrap;
        overflow: hidden; text-overflow: ellipsis;
    }
    /* 標記變色樣式 */
    [data-testid="stElementContainer"]:has(input[type="checkbox"]:checked) {
        background-color: #e8f5e9 !important; border-radius: 8px; padding: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

tw_timezone = pytz.timezone('Asia/Taipei')

# --- 2. 資料清單 (站點清單維持您設定的內容) ---
STATION_LIST = ["請選擇或輸入關鍵字搜尋", "華視光復", "華視電視台", "其他(未登入場站)"]
STAFF_LIST = ["請選擇填單人", "宗哲", "美妞", "政宏", "文輝", "恩佳", "志榮", "阿錨", "子毅", "浚"]

# --- 3. Google Sheets 連線與安全檢查 ---
def init_connection():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_dict = st.secrets["google_sheets"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"❌ 資料庫連線失敗: {e}")
        return None

client = init_connection()

# 核心安全檢查：如果連線失敗，後續代碼不會崩潰
if client:
    try:
        sheet = client.open("客服作業表").sheet1
    except Exception as e:
        st.error(f"❌ 找不到試算表『客服作業表』: {e}")
        sheet = None
else:
    sheet = None

# --- 4. 初始化 Session State ---
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode, st.session_state.edit_row_idx, st.session_state.edit_data = False, None, [""]*8

# --- 5. UI 主介面 ---
tab1, tab2 = st.tabs(["📝 案件登記", "📊 數據統計分析"])

# --- Tab 1: 案件登記 ---
with tab1:
    st.title("📝 應安客服線上登記系統")
    if not sheet:
        st.warning("⚠️ 系統目前無法讀取資料，請檢查後台設定。")
    else:
        now_ts = datetime.datetime.now(tw_timezone)
        
        # 編輯模式提示
        if st.session_state.edit_mode:
            st.warning(f"⚠️ 【編輯模式】- 正在更新第 {st.session_state.edit_row_idx} 列紀錄")

        # 表單邏輯
        with st.form("my_form", clear_on_submit=True):
            d = st.session_state.edit_data if st.session_state.edit_mode else [""]*8
            f_dt = d[0] if st.session_state.edit_mode else now_ts.strftime("%Y-%m-%d %H:%M:%S")
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
                category = st.selectbox("類別", options=["繳費機故障", "發票缺紙或卡紙", "無法找零", "身障優惠折抵", "其他"], index=["繳費機故障", "發票缺紙或卡紙", "無法找零", "身障優惠折抵", "其他"].index(d[5]) if d[5] in ["繳費機故障", "發票缺紙或卡紙", "無法找零", "身障優惠折抵", "其他"] else 4)
            with c4:
                car_num = st.text_input("車號", value=d[4])
            
            description = st.text_area("描述內容", value=d[6])
            
            btn_c1, btn_c2, btn_c3, _ = st.columns([1, 1, 1, 3])
            if btn_c1.form_submit_button("確認送出"):
                if user_name != "請選擇填單人" and station_name != "請選擇或輸入關鍵字搜尋":
                    row = [f_dt, station_name, caller_name, caller_phone, car_num.upper(), category, description, user_name]
                    if st.session_state.edit_mode:
                        sheet.update(f"A{st.session_state.edit_row_idx}:H{st.session_state.edit_row_idx}", [row])
                        st.session_state.edit_mode = False
                    else:
                        sheet.append_row(row)
                    st.success("✅ 送出成功！")
                    st.rerun()
                else:
                    st.error("❌ 請選擇『填單人』與『場站名稱』")

            btn_c2.link_button("多元支付", "http://219.85.163.90:5010/")
            btn_c3.link_button("簡訊系統", "https://umc.fetnet.net/#/menu/login")

        # 歷史紀錄與懸停預覽
        st.markdown("---")
        st.subheader("🔍 最近紀錄 (交班動態)")
        data_raw = sheet.get_all_values()
        if len(data_raw) > 1:
            rows = data_raw[1:]
            display_rows = [(i+2, r) for i, r in list(enumerate(rows))[-5:]] # 範例顯示最後5筆
            
            cols = st.columns([2, 1.5, 1.2, 2.5, 1, 0.8, 0.8])
            titles = ["日期/時間", "場站", "車號", "描述摘要", "填單人", "編輯", "標記"]
            for col, title in zip(cols, titles): col.markdown(f"**{title}**")
            
            for r_idx, r_val in reversed(display_rows):
                with st.container():
                    c = st.columns([2, 1.5, 1.2, 2.5, 1, 0.8, 0.8])
                    c[0].write(r_val[0]); c[1].write(r_val[1]); c[2].write(r_val[4])
                    
                    # 懸停預覽處理
                    clean_desc = r_val[6].replace('\n', ' ').replace('"', '&quot;')
                    short_desc = f"{clean_desc[:12]}..." if len(clean_desc) > 12 else clean_desc
                    c[3].markdown(f'<div class="hover-text" title="{clean_desc}">{short_desc}</div>', unsafe_allow_html=True)
                    
                    c[4].write(r_val[7])
                    if c[5].button("📝", key=f"ed_{r_idx}"):
                        st.session_state.edit_mode, st.session_state.edit_row_idx, st.session_state.edit_data = True, r_idx, r_val
                        st.rerun()
                    c[6].checkbox(" ", key=f"ck_{r_idx}", label_visibility="collapsed")

# --- Tab 2: 數據統計分析 (圖表標籤全修正版) ---
with tab2:
    st.title("📊 數據統計與分析 (自動週報)")
    pwd = st.text_input("管理員密碼", type="password")
    if pwd == "kevin198":
        if sheet:
            all_data = sheet.get_all_values()
            if len(all_data) > 1:
                df = pd.DataFrame(all_data[1:], columns=all_data[0])
                
                # 強制轉換時間
                df[df.columns[0]] = pd.to_datetime(df[df.columns[0]], errors='coerce')
                df = df.dropna(subset=[df.columns[0]])

                # 統計上週
                today = datetime.datetime.now(tw_timezone).date()
                last_monday = today - datetime.timedelta(days=today.weekday() + 7)
                last_sunday = last_monday + datetime.timedelta(days=6)
                
                week_df = df[(df[df.columns[0]].dt.date >= last_monday) & (df[df.columns[0]].dt.date <= last_sunday)]

                if not week_df.empty:
                    st.success(f"📅 統計週期：{last_monday} ~ {last_sunday}")
                    
                    # --- 圖表修正重點 ---
                    c1, c2 = st.columns(2)
                    
                    with c1:
                        # 標題 1：類別佔比
                        st.markdown("### 📂 類別佔比分析")
                        # 強制指定『類別』欄位 (假設在第 6 欄)
                        cat_col = all_data[0][5] 
                        fig1 = px.pie(week_df, names=cat_col, hole=0.4,
                                      color_discrete_sequence=px.colors.qualitative.Pastel)
                        # 強制顯示標籤與名稱
                        fig1.update_traces(textinfo='label+percent', textposition='outside')
                        fig1.update_layout(showlegend=True, legend_title="類別清單")
                        st.plotly_chart(fig1, use_container_width=True)

                    with c2:
                        # 標題 2：場站佔比
                        st.markdown("### 🏢 場站佔比分析")
                        # 強制指定『場站名稱』欄位 (假設在第 2 欄)
                        st_col = all_data[0][1]
                        fig2 = px.pie(week_df, names=st_col, hole=0.4,
                                      color_discrete_sequence=px.colors.qualitative.Safe)
                        # 強制顯示標籤與名稱
                        fig2.update_traces(textinfo='label+percent', textposition='outside')
                        fig2.update_layout(showlegend=True, legend_title="場站清單")
                        st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.info("此週期內尚無數據。")

st.caption("© 2026 應安客服系統 - 2/16 UI 與圖表穩定強化版")
