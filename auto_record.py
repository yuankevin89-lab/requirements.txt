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
    url = "https://www.parkinginfo.ntpc.gov.tw/parkingrealInfo/?parkinglotname=%E7%A2%A7%E8%8F%AF%E5%9C%8B%E5%B0%8F"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        spots_element = soup.find("span", {"id": "ContentPlaceHolder1_lblAvailableCar"})
        return spots_element.text.strip() if spots_element else "無法解析數字"
    except Exception as e:
        return f"抓取失敗: {str(e)}"

def update_google_sheet(spots):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        # GitHub Actions 會從 Secrets 動態產生此檔案
        creds = ServiceAccountCredentials.from_json_keyfile_name(JSON_FILE, scope)
        client = gspread.authorize(creds)
        
        # --- 關鍵修正：指定開啟「車位紀錄」分頁 ---
        sheet = client.open(SHEET_NAME).worksheet(WORKSHEET_NAME)
        
        now = datetime.datetime.now(TW_TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([now, spots])
        print(f"✅ [{now}] 成功紀錄至 {WORKSHEET_NAME}：{spots}")
    except Exception as e:
        print(f"❌ 寫入失敗: {e}")

if __name__ == "__main__":
    current_spots = get_realtime_spots()
    update_google_sheet(current_spots)
