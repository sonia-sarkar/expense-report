import re
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
from openpyxl import Workbook, load_workbook
import os

def preprocess_image(path):
    img = Image.open(path)
    img = img.convert("L")  # grayscale
    img = img.filter(ImageFilter.SHARPEN)
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2)  # increase contrast
    return img

def extract_text(path):
    img = preprocess_image(path)
    return pytesseract.image_to_string(img, config="--psm 6 --oem 3")

def extract_amount(text):
    # require $ in front to avoid false numbers
    match = re.search(r"\$?\s*([0-9]+\.[0-9]{2})", text)
    return match.group(1) if match else ""

def extract_vendor(text):
    # crude: first non-numeric line is often vendor
    for line in text.splitlines():
        if line.strip() and not re.search(r"\d", line):  
            return line.strip()
    return "Unknown"

def extract_date(text):
    # mm/dd/yy or mm-dd-yy patterns
    match = re.search(r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", text)
    return match.group(1) if match else ""

def save_to_excel(date, vendor, amount, notes, filename="expenses.xlsx"):
    if os.path.exists(filename):
        wb = load_workbook(filename)
        ws = wb.active
    else:
        wb = Workbook()
        ws = wb.active
        ws.append(["Date", "Vendor", "Amount", "Notes"])  # header

    ws.append([date, vendor, amount, notes])
    wb.save(filename)

if __name__ == "__main__":
    receipt = "receipts/receipt1.jpg"

    text = extract_text(receipt)

    date = extract_date(text)
    vendor = extract_vendor(text)
    amount = extract_amount(text)
    notes = "Receipt scanned automatically"

    save_to_excel(date, vendor, amount, notes)
    print(f"Added: Date={date}, Vendor={vendor}, Amount={amount}")
