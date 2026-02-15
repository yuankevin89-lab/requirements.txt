import requests
from bs4 import BeautifulSoup
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import pytz
import os

# --- 設定區域 ---
TW_TIMEZONE = pytz.timezone('Asia/Taipei')
JSON_FILE = 'service_account.json' 
SHEET_NAME = '客服作業表'      # 試算表檔名
WORKSHEET_NAME = '車位紀錄'   # 指定存入的工作表名稱

def get_realtime_spots():
    # 碧華國小停車場資訊頁面
    url = "https://www.parkinginfo.ntpc.gov.tw/parkingrealInfo/?parkinglotname=%E7%A2%A7%E8%8F%AF%E5%9C%8B%E5%B0%8F"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'utf-8' # 強制使用 utf-8 避免亂碼
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 嘗試多種抓取方式，增加成功率
        # 1. 透過 ID 抓取
        spots_element = soup.find("span", {"id": "ContentPlaceHolder1_lblAvailableCar"})
        
        if spots_element and spots_element.text.strip():
            return spots_element.text.strip()
        
        # 2. 如果 ID 失效，嘗試抓取所有表格內的數字 (備用方案)
        all_spans = soup.find_all("span")
        for s in all_spans:
            if s.get('id') and 'lblAvailableCar' in s.get('id'):
                return s.text.strip()
                
        return "網頁改版中"
    except Exception as e:
        return f"連線錯誤"

def update_google_sheet(spots):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(JSON_FILE, scope)
        client = gspread.authorize(creds)
        
        sheet = client.open(SHEET_NAME).worksheet(WORKSHEET_NAME)
        
        # 取得台灣時間
        now = datetime.datetime.now(TW_TIMEZONE).strftime("%Y-%m-%d %H:%M")
        
        # 寫入資料
        sheet.append_row([now, spots])
        print(f"✅ [{now}] 紀錄成功：{spots}")
    except Exception as e:
        print(f"❌ 寫入失敗: {e}")

if __name__ == "__main__":
    current_spots = get_realtime_spots()
    update_google_sheet(current_spots)
