import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import pytz
import time

# --- 設定區域 ---
TW_TIMEZONE = pytz.timezone('Asia/Taipei')
JSON_FILE = 'service_account.json' 
SHEET_NAME = '客服作業表'      
WORKSHEET_NAME = '車位紀錄'   

def get_realtime_spots():
    # 碧華國小停車場代碼
    # 直接抓取新北交通局後端 API (較不容易被阻擋)
    url = "https://www.parkinginfo.ntpc.gov.tw/parkingrealInfo/RealtimeInfo.ashx"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Referer': 'https://www.parkinginfo.ntpc.gov.tw/parkingrealInfo/?parkinglotname=%E7%A2%A7%E8%8F%AF%E5%9C%8B%E5%B0%8F'
    }

    try:
        # 使用 Session 並帶入搜尋參數
        params = {'parkinglotname': '碧華國小'}
        response = requests.get(url, params=params, headers=headers, timeout=20)
        
        # 檢查網頁內容
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        spots_element = soup.find("span", {"id": "ContentPlaceHolder1_lblAvailableCar"})
        
        if spots_element and spots_element.text.strip().isdigit():
            return spots_element.text.strip()
            
        # 備選方案：如果標籤失效，嘗試解析全網頁純數字
        text_content = soup.get_text()
        if "剩餘車位" in text_content:
            import re
            numbers = re.findall(r'\d+', text_content)
            if numbers:
                return numbers[0]
                
        return "暫無數據"
    except Exception as e:
        return f"連線異常"

def update_google_sheet(spots):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(JSON_FILE, scope)
        client = gspread.authorize(creds)
        
        sheet = client.open(SHEET_NAME).worksheet(WORKSHEET_NAME)
        now = datetime.datetime.now(TW_TIMEZONE).strftime("%m/%d %H:%M")
        
        sheet.append_row([now, spots])
        print(f"✅ 寫入成功：{spots}")
    except Exception as e:
        print(f"❌ 寫入失敗: {e}")

if __name__ == "__main__":
    current_spots = get_realtime_spots()
    update_google_sheet(current_spots)
