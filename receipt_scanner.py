# receipt_scanner.py
import pytesseract
import cv2
import pandas as pd
import re
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageOps, ImageEnhance
import pytesseract

def preprocess_image(path):
    img = Image.open(path)

    # Convert to grayscale
    img = img.convert("L")

    # Increase contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2)   # try 1.5–3 for tuning

    # Apply threshold (binarization)
    img = img.point(lambda x: 0 if x < 140 else 255, '1')

    return img

def extract_text(path):
    img = preprocess_image(path)
    # Try different page segmentation & engine modes
    custom_config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(img, config=custom_config)
    return text




RECEIPT_DIR = Path("./receipts")
REPORT_CSV = Path("./expense_report.csv")

pytesseract.pytesseract.tesseract_cmd = "/opt/homebrew/bin/tesseract"  # Adjust this path if needed

def extract_text(image_path):
    image = cv2.imread(str(image_path))
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray)
    return text

def parse_fields(text):
    vendor = None
    date = None
    amount = None

    # --- Vendor (first line heuristic)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if lines:
        vendor = lines[0]

    # --- Date (multiple formats)
    import re, datetime
    date_pattern = re.compile(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})')
    for match in date_pattern.findall(text):
        for fmt in ("%m/%d/%Y", "%m-%d-%Y", "%m/%d/%y", "%m-%d-%y", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                date = datetime.datetime.strptime(match, fmt).date()
                break
            except ValueError:
                continue
        if date:
            break

    # --- Amount
    amount_pattern = re.compile(r'Amount[: ]*\$?\s?(\d+\.\d{2})', re.IGNORECASE)
    matches = amount_pattern.findall(text)

    if matches:
        # Heuristic: take the **largest** amount (to avoid gratuity $0.xx overwriting total)
        amount = max([float(m) for m in matches])
    else:
        # fallback: find any $xx.xx in text
        dollar_pattern = re.compile(r'\$?\s?(\d+\.\d{2})')
        dollar_matches = dollar_pattern.findall(text)
        if dollar_matches:
            amount = max([float(m) for m in dollar_matches])

    return {
        "Vendor": vendor,
        "Date": date,
        "Amount": amount,
        "Raw Text": text
    }




def update_expense_report(data):
    df = pd.DataFrame([data])
    if REPORT_CSV.exists() and REPORT_CSV.stat().st_size > 0:
        try:
            df_existing = pd.read_csv(REPORT_CSV)
            df = pd.concat([df_existing, df], ignore_index=True)
        except pd.errors.EmptyDataError:
            # start fresh if file is corrupt/empty
            pass
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
