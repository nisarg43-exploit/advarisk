import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import pytesseract
import re
import os
import urllib.parse
import numpy as np
import cv2
import pandas as pd
from pymongo import MongoClient

# Set Tesseract OCR path (Update this as per your system installation)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Define URLs
BASE_URL = "https://epanjiyan.rajasthan.gov.in/e-search-page.aspx"
CAPTCHA_URL = "https://epanjiyan.rajasthan.gov.in/CImage.aspx"

# MongoDB Configuration
MONGO_URI = "mongodb://localhost:27017/"  # Change if using a remote server
DB_NAME = "mydatabase"  # Change to your database name
COLLECTION_NAME = "mycollection"  # Change to your collection name
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# Read remaining body data from file
with open("body.txt", "r") as file:
    remaining_body = file.read()

def extract_table_csv():
    """Extracts table data from the HTML response and saves it in a structured format to MongoDB and CSV."""
    with open("search_result.html", "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, "html.parser")
    
    table = soup.find("table", {"id": "ContentPlaceHolder1_gridsummary"})
    if not table:
        print("No table found.")
        return
    
    headers = [th.text.strip() for th in table.find_all("th")]
    rows = []
    
    for row in table.find_all("tr")[1:]:  # Skip header row
        cols = [td.text.strip() for td in row.find_all("td")]
        if len(cols) == len(headers):
            rows.append(dict(zip(headers, cols)))
    
    # Remove last two rows
    rows = rows[:-2] if len(rows) > 2 else rows
    
    # Save data to CSV
    df = pd.DataFrame(rows)
    df.to_csv("extracted_table.csv", index=False)
    
    # Save structured data to MongoDB
    if rows:
        collection.insert_many(rows)
    print("Data saved to MongoDB and CSV.")


def solve_captcha():
    """Solves captcha by processing the image."""
    try:
        image_path = "captcha.png"
        img = cv2.imread(image_path)
        
        if img is None:
            raise ValueError("Error: Could not load image.")
        
        # Convert image to HSV and apply threshold
        hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv_img, np.array([0, 0, 149]), np.array([86, 177, 255]))
        output = img.copy()
        output[mask > 0] = [255, 255, 255]
        
        # Save processed image
        processed_path = "processed_img.png"
        cv2.imwrite(processed_path, output)
        
        # Extract text using OCR
        text = pytesseract.image_to_string(output).strip()
        text = re.sub(r'\W+', '', text)  # Remove non-alphanumeric characters
        print(f"Captcha Text: {text}")
        return text
    except Exception as e:
        print(f"Error solving captcha: {e}")
        return ""

def get_hidden_fields_and_captcha(session):
    """Extracts hidden form fields and downloads captcha image."""
    response = session.get(BASE_URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    viewstate = soup.find("input", {"name": "__VIEWSTATE"})["value"]
    viewstate_generator = soup.find("input", {"name": "__VIEWSTATEGENERATOR"})["value"]
    event_validation = soup.find("input", {"name": "__EVENTVALIDATION"})["value"]
    
    # Download captcha image
    captcha_img_tag = soup.find("img", {"id": "ContentPlaceHolder1_Image1"})
    if captcha_img_tag:
        captcha_url = "https://epanjiyan.rajasthan.gov.in/" + captcha_img_tag["src"]
        captcha_response = session.get(captcha_url)
        img = Image.open(BytesIO(captcha_response.content))
        img.save("captcha.png")
        print("Captcha saved as captcha.png")
    
    return viewstate, viewstate_generator, event_validation

def extract_table():
    """Extracts table data from the HTML response and saves it in a structured format to MongoDB."""
    with open("search_result.html", "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, "html.parser")
    
    table = soup.find("table", {"id": "ContentPlaceHolder1_gridsummary"})
    if not table:
        print("No table found.")
        return
    
    headers = [th.text.strip() for th in table.find_all("th")]
    rows = []
    
    for row in table.find_all("tr")[1:]:  # Skip header row
        cols = [td.text.strip() for td in row.find_all("td")]
        if len(cols) == len(headers):
            rows.append(dict(zip(headers, cols)))
    
    # Remove last two rows
    rows = rows[:-2] if len(rows) > 2 else rows
    
    # Format data
    formatted_data = {
        "Scrape_data": [
            {
                "location_type": "rural",
                "district_name": row.get("District Name", ""),
                "district_code": row.get("District Code", ""),
                "tehsil_name": row.get("Tehsil Name", ""),
                "tehsil_code": row.get("Tehsil Code", ""),
                "sro_name": row.get("SRO Name", ""),
                "sro_code": row.get("SRO Code", ""),
                "document_type": row.get("Document Type", ""),
                "document_number": row.get("Document Number", ""),
                "document_details": [],
                "location_details": {
                    "khasra_number": row.get("Khasra Number", ""),
                    "plot_number": row.get("Plot Number", ""),
                    "landmark": {
                        "village": row.get("Village", ""),
                        "tehsil": row.get("Tehsil", ""),
                        "district": row.get("District", ""),
                        "property_address": row.get("Property Address", "")
                    }
                }
            } for row in rows
        ]
    }
    
    # Save structured data to MongoDB
    collection.insert_one(formatted_data)
    print("data saved to MongoDB.")

# Initialize session
session = requests.Session()
viewstate, viewstate_generator, event_validation = get_hidden_fields_and_captcha(session)

# solved_captcha = solve_captcha()

headers = {
    "Host": "epanjiyan.rajasthan.gov.in",
    "Cookie": "ASP.NET_SessionId=ioqh4d5i4o5v1jqffrsnjunv",
    "Sec-Ch-Ua-Platform": "\"Windows\"",
    "Cache-Control": "no-cache",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Ch-Ua": "\"Chromium\";v=\"133\", \"Not(A:Brand\";v=\"99\"",
    "Sec-Ch-Ua-Mobile": "?0",
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "X-Microsoftajax": "Delta=true",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Accept": "*/*",
    "Origin": "https://epanjiyan.rajasthan.gov.in",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Referer": "https://epanjiyan.rajasthan.gov.in/e-search-page.aspx",
    "Accept-Encoding": "gzip, deflate, br",
    "Priority": "u=1, i",
    "Connection": "keep-alive"
}


solved_Captcha = solve_captcha()
solved_Captcha =str(solved_Captcha).replace('/','')

district_code="1"
tehsil_code="1"
sro_code="1"
doc_type="17"
doc_number="5"
# encoded_view_state, encoded_VIEWSTATEGENERATOR, encoded_EVENTVALIDATION = get_hidden_fields_and_captcha()
# Body (Paste your raw body data here)
body = f"ctl00%24ScriptManager1=ctl00%24upContent%7Cctl00%24ContentPlaceHolder1%24btnsummary&ScriptManager1_HiddenField=&ctl00%24ContentPlaceHolder1%24a=rbtrural&ctl00%24ContentPlaceHolder1%24ddlDistrict={district_code}&ctl00%24ContentPlaceHolder1%24ddlTehsil={tehsil_code}&ctl00%24ContentPlaceHolder1%24ddlSRO={sro_code}&ctl00%24ContentPlaceHolder1%24ddlcolony=-Select-&ctl00%24ContentPlaceHolder1%24ddldocument={doc_type}&ctl00%24ContentPlaceHolder1%24txtexcutent=&ctl00%24ContentPlaceHolder1%24txtclaiment={doc_number}{remaining_body}"


# Send POST request
response = requests.post(BASE_URL, headers=headers, data=body)
with open("search_result.html", "w", encoding="utf-8") as f:
    f.write(response.text)

print(f"Status Code: {response.status_code}")

# Extract and save structured table data
extract_table()
# extract_table_csv()
