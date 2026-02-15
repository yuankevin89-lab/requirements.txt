name: Hourly Parking Record

on:
  schedule:
    - cron: '0 * * * *' # 每小時執行一次
  workflow_dispatch:      # 讓您可以手動點擊測試

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python_version: '3.9'

      - name: Install dependencies
        run: |
          pip install requests gspread oauth2client beautifulsoup4 pytz

      - name: Create JSON Key File
        run: |
          echo '${{ secrets.GCP_SA_JSON }}' > service_account.json

      - name: Run script
        run: python auto_record.py
