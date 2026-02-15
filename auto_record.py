import requests
from bs4 import BeautifulSoup
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import pytz
import time
import random

# --- 設定區域 ---
TW_TIMEZONE = pytz.timezone('Asia/Taipei')
JSON_FILE = 'service_account.json' 
SHEET_NAME = '客服作業表'      
WORKSHEET_NAME = '車位紀錄'   

def get_realtime_spots():
    # 碧華國小停車場
    url = "https://www.parkinginfo.ntpc.gov.tw/parkingrealInfo/?parkinglotname=%E7%A2%A7%E8%8F%AF%E5%9C%8B%E5%B0%8F"
    
    # 模擬更完整的真人瀏覽器特徵
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://www.parkinginfo.ntpc.gov.tw/',
        'Connection': 'keep-alive'
    }

    # 嘗試抓取 3 次
    for i in range(3):
        try:
            # 加入隨機等待 1-3 秒，避免被偵測
            time.sleep(random.uniform(1, 3))
            
            session = requests.Session()
            response = session.get(url, headers=headers, timeout=25)
            response.encoding = 'utf-8'
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 定位車位數量的標籤
                # 這是新北網站目前的關鍵 ID
                spots_element = soup.find("span", {"id": "ContentPlaceHolder1_lblAvailableCar"})
                
                if spots_element:
                    digit_result = "".join(filter(str.isdigit, spots_element.text.strip()))
                    if digit_result:
                        return digit_result
            
        except Exception as e:
            print(f"嘗試第 {i+1} 次失敗: {e}")
            continue
            
    return "網站維護中"

def update_google_sheet(spots):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(JSON_FILE, scope)
        client = gspread.authorize(creds)
        
        # 指定開啟工作表名稱
        sheet = client.open(SHEET_NAME).worksheet(WORKSHEET_NAME)
        
        # 格式化時間：02/15 21:45
        now = datetime.datetime.now(TW_TIMEZONE).strftime("%m/%d %H:%M")
        
        # 寫入
        sheet.append_row([now, spots])
        print(f"✅ 紀錄成功：{spots}")
        
    except Exception as e:
        print(f"❌ 寫入失敗: {e}")

if __name__ == "__main__":
    current_spots = get_realtime_spots()
    update_google_sheet(current_spots)
