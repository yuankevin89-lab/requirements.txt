import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import datetime
import pandas as pd
import pytz
import plotly.express as px

# --- 1. 頁面基本設定與樣式 ---
st.set_page_config(page_title="應安客服雲端登記系統", page_icon="📝", layout="wide")

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            .stAppDeployButton {display: none;}
            .block-container {padding-top: 2rem; padding-bottom: 1rem;}
            
            /* 精確標記變色 */
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
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

tw_timezone = pytz.timezone('Asia/Taipei')

# --- 2. 資料清單設定 (略，維持原樣) ---
STATION_LIST = ["請選擇或輸入關鍵字搜尋", "華視光復", "華視電視台", "其他(未登入場站)"]
STAFF_LIST = ["請選擇填單人", "宗哲", "美妞", "政宏", "文輝", "恩佳", "志榮", "阿錨", "子毅", "浚"]

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

tab1, tab2 = st.tabs(["📝 案件登記", "📊 數據統計分析"])

with tab1:
    # ... (案件登記代碼維持不變，包含懸停預覽功能)
    st.title("📝 應安客服線上登記系統")
    # 此處省略 Tab 1 中間代碼以節省篇幅，內容與前一版本完全相同

# --- 📊 Tab 2: 數據統計分析 (圖表修正重點區) ---
with tab2:
    st.title("📊 數據統計與分析 (自動週報)")
    if st.text_input("管理員密碼", type="password", key="stat_pwd") == "kevin198":
        if sheet:
            all_raw = sheet.get_all_values()
            if len(all_raw) > 1:
                # 建立 DataFrame 並清理時間格式
                df_all = pd.DataFrame(all_raw[1:], columns=all_raw[0])
                time_col = df_all.columns[0]
                df_all[time_col] = pd.to_datetime(df_all[time_col], errors='coerce')
                df_all = df_all.dropna(subset=[time_col])

                # 設定統計週期：上週一至週日
                today = datetime.datetime.now(tw_timezone).date()
                last_monday = today - datetime.timedelta(days=today.weekday() + 7)
                last_sunday = last_monday + datetime.timedelta(days=6)
                
                mask = (df_all[time_col].dt.date >= last_monday) & (df_all[time_col].dt.date <= last_sunday)
                df = df_all.loc[mask].copy()

                st.success(f"📅 **統計週期：{last_monday} (一) ~ {last_sunday} (日)**")
                
                if not df.empty:
                    st.markdown("---")
                    g1, g2 = st.columns(2)
                    
                    # 精確定義欄位名稱 (避免抓錯欄位)
                    target_cat_col = "類別"
                    target_st_col = "場站名稱"
                    
                    with g1:
                        st.subheader("📂 類別佔比分析")
                        if target_cat_col in df.columns:
                            # 修正：加上 labels 與 title，確保圖例顯示「類別名稱」
                            fig1 = px.pie(df, names=target_cat_col, 
                                          title=f"各類別案件比例 ({last_monday} ~ {last_sunday})",
                                          hole=0.4, 
                                          color_discrete_sequence=px.colors.qualitative.Safe)
                            fig1.update_traces(textposition='inside', textinfo='percent+label')
                            st.plotly_chart(fig1, use_container_width=True)
                        else:
                            st.error(f"找不到『{target_cat_col}』欄位，請檢查試算表標題")

                    with g2:
                        st.subheader("🏢 場站佔比分析")
                        if target_st_col in df.columns:
                            # 修正：加上 labels 與 title，確保圖例顯示「場站名稱」
                            fig2 = px.pie(df, names=target_st_col, 
                                          title=f"各場站案件比例 ({last_monday} ~ {last_sunday})",
                                          hole=0.4, 
                                          color_discrete_sequence=px.colors.qualitative.Pastel)
                            fig2.update_traces(textposition='inside', textinfo='percent+label')
                            st.plotly_chart(fig2, use_container_width=True)
                        else:
                            st.error(f"找不到『{target_st_col}』欄位，請檢查試算表標題")
                    
                    st.markdown("---")
                    st.write("📋 **當週原始資料明細**")
                    st.dataframe(df.sort_values(by=time_col, ascending=False), use_container_width=True)
                else:
                    st.warning(f"⚠️ 在 {last_monday} 至 {last_sunday} 期間尚無任何登記資料。")

st.caption("© 2026 應安客服系統 - 2/16 數據分析圖表修正版")
