# --- 最近三筆紀錄：改用 st.table 徹底鎖定，無法拉扯 ---
        st.markdown("---")
        st.subheader("🕒 最近三筆登記紀錄 (完全鎖定版)")
        try:
            raw_data = sheet.get_all_values()
            if len(raw_data) > 1:
                # 轉成 DataFrame 處理邏輯
                df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
                recent_df = df.tail(3).iloc[::-1]
                
                # 使用 st.table 呈現，這會移除所有拉伸、排序功能，達到完全鎖定
                st.table(recent_df)
            else:
                st.caption("目前尚無歷史紀錄")
        except Exception:
            st.caption("表格刷新中...")
