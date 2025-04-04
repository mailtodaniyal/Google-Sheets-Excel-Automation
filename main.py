import requests
import pandas as pd
import os
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

API_URL = "https://api.example.com/stock_data"  
REPORTS_FOLDER = "reports/" 
GOOGLE_SHEET_NAME = "Dealership Stock Tracker"  

GOOGLE_CREDENTIALS_FILE = "google_credentials.json"

STOCK_LIMIT = 500

def fetch_stock_data():
    print("Fetching stock data from API...")

    try:
        response = requests.get(API_URL)
        response.raise_for_status()  
        data = response.json()

        if not data or "stocks" not in data:
            print(" ERROR: API response is empty or missing required data.")
            return None

        df = pd.DataFrame(data["stocks"])  

        required_columns = ["Technician", "Stock Number", "Date", "Key Status", "Priority"]
        for col in required_columns:
            if col not in df.columns:
                print(f" ERROR: Missing column '{col}' in API data.")
                return None

        df["Date"] = pd.to_datetime(df["Date"])  
        print(" Stock data fetched successfully!")
        return df

    except requests.exceptions.RequestException as e:
        print(f" ERROR: Failed to fetch data from API - {e}")
        return None

def generate_reports(df):
    today = datetime.date.today()

    if not os.path.exists(REPORTS_FOLDER):
        os.makedirs(REPORTS_FOLDER)

    daily_report = df[df["Date"].dt.date == today]
    daily_report.to_csv(f"{REPORTS_FOLDER}daily_report_{today}.csv", index=False)

    start_of_week = today - datetime.timedelta(days=today.weekday())  
    weekly_report = df[df["Date"].dt.date >= start_of_week]
    weekly_report.to_csv(f"{REPORTS_FOLDER}weekly_report_{today}.csv", index=False)

    start_of_month = today.replace(day=1)
    monthly_report = df[df["Date"].dt.date >= start_of_month]
    monthly_report.to_csv(f"{REPORTS_FOLDER}monthly_report_{today}.csv", index=False)

    print(" Reports Generated Successfully!")

def check_stock_limit(df):
    total_stock = len(df)
    if total_stock >= 0.9 * STOCK_LIMIT:
        print(f" WARNING: 90% of stock limit reached! ({total_stock}/{STOCK_LIMIT})")
    if total_stock > STOCK_LIMIT:
        print(f" ALERT: Stock limit exceeded! ({total_stock}/{STOCK_LIMIT}) - Extra stocks will be billed.")
    return total_stock

def upload_to_google_sheets(df):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDENTIALS_FILE, scope)
        client = gspread.authorize(creds)

        sheet = client.open(GOOGLE_SHEET_NAME).sheet1
        sheet.clear()  

        sheet.append_row(df.columns.tolist())

        sheet.append_rows(df.values.tolist())

        print(f" Data uploaded to Google Sheets: {GOOGLE_SHEET_NAME}")

    except Exception as e:
        print(f" ERROR: Google Sheets upload failed - {e}")

def main():
    print(" Running Dealership Stock Tracker...")

    df = fetch_stock_data()
    if df is None:
        return

    total_stock = check_stock_limit(df)
    print(f" Total stock processed: {total_stock}")

    generate_reports(df)
    upload_to_google_sheets(df)

    print(" All tasks completed!")

if __name__ == "__main__":
    main()
