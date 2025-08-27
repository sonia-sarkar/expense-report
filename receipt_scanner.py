# receipt_scanner.py
import pytesseract
import cv2
import pandas as pd
import re
from datetime import datetime
from pathlib import Path

RECEIPT_DIR = Path("./receipts")
REPORT_CSV = Path("./expense_report.csv")

pytesseract.pytesseract.tesseract_cmd = "/opt/homebrew/bin/tesseract"  # Adjust this path if needed

def extract_text(image_path):
    image = cv2.imread(str(image_path))
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray)
    return text

def parse_fields(text):
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    vendor = lines[0] if lines else "Unknown"
    date_match = re.search(r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b', text)
    try:
        date = datetime.strptime(date_match.group(1), "%m/%d/%Y").date()
    except:
        date = None
    amount_match = re.search(r'\$\s?(\d+\.\d{2})', text)
    amount = float(amount_match.group(1)) if amount_match else None
    return {
        "Vendor": vendor,
        "Date": date,
        "Amount": amount,
        "Raw Text": text[:100] + "..."
    }

def update_expense_report(data):
    df = pd.DataFrame([data])
    if REPORT_CSV.exists() and REPORT_CSV.stat().st_size > 0:
        # Only read if file is not empty
        df_existing = pd.read_csv(REPORT_CSV)
        df = pd.concat([df_existing, df], ignore_index=True)
    # Always write back out with headers
    df.to_csv(REPORT_CSV, index=False)

def process_receipts():
    for receipt in RECEIPT_DIR.glob("*.jpg"):
        print(f"Processing {receipt.name}")
        text = extract_text(receipt)
        data = parse_fields(text)
        update_expense_report(data)
        print(f"Added: {data}")

if __name__ == "__main__":
    process_receipts()
