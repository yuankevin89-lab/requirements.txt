import requests
from bs4 import BeautifulSoup
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import pytz
import os

# --- 設定區域 ---
TW_TIMEZONE = pytz.timezone('Asia/Taipei')
# GitHub Actions 會在執行時動態產生這個檔案
JSON_FILE = 'service_account.json' 
SHEET_NAME = '碧華國小車位統計'

def get_realtime_spots():
    """前往新北市政府網站抓取碧華國小即時車位"""
    url = "https://www.parkinginfo.ntpc.gov.tw/parkingrealInfo/?parkinglotname=%E7%A2%A7%E8%8F%AF%E5%9C%8B%E5%B0%8F"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        # 指定解析器為 html.parser 避免環境差異
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 定位「剩餘汽車數」的 HTML 元素
        spots_element = soup.find("span", {"id": "ContentPlaceHolder1_lblAvailableCar"})
        
        if spots_element:
            return spots_element.text.strip()
        else:
            return "無法解析數字"
    except Exception as e:
        return f"抓取失敗: {str(e)}"

def update_google_sheet(spots):
    """將抓到的數字寫入 Google Sheets"""
    try:
        # 檢查金鑰檔案是否存在
        if not os.path.exists(JSON_FILE):
            print(f"錯誤：找不到金鑰檔案 {JSON_FILE}")
            return

        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(JSON_FILE, scope)
        client = gspread.authorize(creds)
        
        # 開啟試算表
        sheet = client.open(SHEET_NAME).sheet1
        
        # 取得台北時間
        now = datetime.datetime.now(TW_TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")
        
        # 寫入新的一列：[時間, 剩餘車位]
        sheet.append_row([now, spots])
        print(f"✅ [{now}] 成功紀錄車位數：{spots}")
        
    except Exception as e:
        print(f"❌ 寫入試算表失敗: {e}")

if __name__ == "__main__":
    current_spots = get_realtime_spots()
    update_google_sheet(current_spots)
