import requests
from bs4 import BeautifulSoup
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
    # 碧華國小停車場
    url = "https://www.parkinginfo.ntpc.gov.tw/parkingrealInfo/?parkinglotname=%E7%A2%A7%E8%8F%AF%E5%9C%8B%E5%B0%8F"
    
    # 模擬真人瀏覽器的 Header
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7'
    }

    # 嘗試抓取 3 次，避免網頁載入失敗
    for i in range(3):
        try:
            response = requests.get(url, headers=headers, timeout=20)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 定位車位數量的標籤
            spots_element = soup.find("span", {"id": "ContentPlaceHolder1_lblAvailableCar"})
            
            if spots_element and spots_element.text.strip().isdigit():
                return spots_element.text.strip()
            
            # 如果沒抓到，休息 2 秒再試一次
            time.sleep(2)
        except Exception:
            continue
            
    return "讀取逾時"

def update_google_sheet(spots):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(JSON_FILE, scope)
        client = gspread.authorize(creds)
        
        sheet = client.open(SHEET_NAME).worksheet(WORKSHEET_NAME)
        now = datetime.datetime.now(TW_TIMEZONE).strftime("%m/%d %H:%M")
        
        sheet.append_row([now, spots])
        print(f"✅ 紀錄成功：{spots}")
    except Exception as e:
        print(f"❌ 寫入失敗: {e}")

if __name__ == "__main__":
    current_spots = get_realtime_spots()
    update_google_sheet(current_spots)
