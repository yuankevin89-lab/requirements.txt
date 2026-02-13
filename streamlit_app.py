import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import datetime
import pandas as pd

# --- 1. 頁面基本設定 ---
st.set_page_config(page_title="應安客服雲端登記系統", page_icon="📝", layout="wide")

# --- 2. Google Sheets 連線函式 ---
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

# --- 3. 建立分頁 ---
tab1, tab2 = st.tabs(["📝 案件登記", "📊 當日報表統計"])

# --- Tab 1: 案件登記 ---
with tab1:
    st.title("📝 應安客服雲端登記系統")
    if conn_success:
        with st.form("my_form", clear_on_submit=True):
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.info(f"🕒 登記時間：{now} (系統自動偵測)")
            
            col1, col2 = st.columns(2)
            with col1:
                station_name = st.text_input("場站名稱 (必填)", placeholder="例如：華視光復場")
                caller_name = st.text_input("來電人 (選填)", placeholder="可留空")
            with col2:
                user_name = st.text_input("填單人姓名 (必填)", placeholder="請輸入姓名")
                caller_phone = st.text_input("電話 (選填)", placeholder="可留空")
            
            col3, col4 = st.columns(2)
            with col3:
                category = st.selectbox("案件類別", ["繳費機故障", "發票缺紙或卡紙", "無法找零", "身障優惠折抵", "其他"])
            with col4:
                car_number = st.text_input("車號 (選填)", placeholder="可留空")
                
            description = st.text_area("詳細描述 (必填)", placeholder="請具體說明需求內容...")
            submit = st.form_submit_button("確認提交並同步雲端")

            if submit:
                if user_name and station_name and description:
                    try:
                        row_to_add = [now, station_name, user_name, category, caller_name, caller_phone, car_number, description]
                        sheet.append_row(row_to_add)
                        st.success("✅ 資料已成功上傳！")
                        st.rerun()
                    except Exception as upload_error:
                        st.error(f"上傳錯誤：{upload_error}")
                else:
                    st.warning("⚠️ 請填寫必填欄位。")

        # --- 最近三筆紀錄 (保持寬度優化) ---
        st.markdown("---")
        st.subheader("🕒 最近三筆登記紀錄")
        try:
            all_records = sheet.get_all_records()
            if all_records:
                recent_df = pd.DataFrame(all_records).tail(3).iloc[::-1]
                st.dataframe(
                    recent_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "時間": st.column_config.TextColumn("時間", width="small"),
                        "場站名稱": st.column_config.TextColumn("場站名稱", width="small"),
                        "填單人姓名": st.column_config.TextColumn("填單人姓名", width="small"),
                        "案件類別": st.column_config.TextColumn("案件類別", width="small"),
                        "來電人": st.column_config.TextColumn("來電人", width="small"),
                        "電話": st.column_config.TextColumn("電話", width="small"),
                        "車號": st.column_config.TextColumn("車號", width="small"),
                        "詳細描述": st.column_config.TextColumn("詳細描述", width="large"),
                    }
                )
            else:
                st.caption("目前尚無歷史紀錄")
        except Exception:
            st.caption("暫時無法讀取最近紀錄")

# --- Tab 2: 數據統計 (加入密碼保護) ---
with tab2:
    st.title("📊 當日報表摘要")
    
    # 設定密碼 (你可以自行修改 '8888' 為你想要的密碼)
    PASSWORD = "8888"
    
    # 建立密碼輸入框
    input_password = st.text_input("請輸入管理員密碼以查看統計內容", type="password")
    
    if input_password == PASSWORD:
        st.success("密碼正確，正在讀取數據...")
        if conn_success:
            if st.button("更新統計數據"):
                all_data = sheet.get_all_records()
                if all_data:
                    df = pd.DataFrame(all_data)
                    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
                    df_today = df[df.iloc[:, 0].astype(str).str.contains(today_str)]
                    
                    if not df_today.empty:
                        c1, c2, c3 = st.columns(3)
                        c1.metric("今日總案件數", len(df_today))
                        c2.metric("最常發生場站", df_today.iloc[:, 1].mode()[0] if not df_today.iloc[:, 1].mode().empty else "無")
                        c3.metric("主要故障類型", df_today.iloc[:, 3].mode()[0] if not df_today.iloc[:, 3].mode().empty else "無")
                        
                        st.subheader("案件類別分布")
                        chart_data = df_today.iloc[:, 3].value_counts()
                        st.bar_chart(chart_data)
                        
                        st.subheader("今日詳細紀錄")
                        st.dataframe(df_today, use_container_width=True)
                    else:
                        st.info("今日尚無登記資料。")
                else:
                    st.info("目前雲端無資料。")
    elif input_password != "":
        st.error("密碼錯誤，請重新輸入。")
