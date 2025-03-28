# Installation Guide

## Prerequisites
Ensure you have Python installed (recommended version: 3.8+).

## Install Required Libraries
Run the following command to install all necessary dependencies:
```sh
pip install requests beautifulsoup4 pillow numpy opencv-python pandas pymongo pytesseract
```

## Install Tesseract OCR
Tesseract OCR is required for captcha solving. Follow these steps to install it:

### Windows:
1. Download the installer from [Tesseract OCR GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
2. Install and note the installation path (e.g., `C:\Program Files\Tesseract-OCR\tesseract.exe`)
3. Add the installation path to the system environment variables

### Linux (Ubuntu/Debian):
```sh
sudo apt update
sudo apt install tesseract-ocr -y
```

### macOS:
```sh
brew install tesseract
```

## MongoDB Setup
Ensure MongoDB is installed and running:

### Windows:
1. Download MongoDB from [MongoDB official site](https://www.mongodb.com/try/download/community)
2. Install and start the MongoDB service

### Linux:
```sh
sudo apt update
sudo apt install -y mongodb
sudo systemctl start mongodb
sudo systemctl enable mongodb
```

### macOS:
```sh
brew tap mongodb/brew
brew install mongodb-community@6.0
brew services start mongodb/brew/mongodb-community
```

## Running the Script
After installing all dependencies, execute the script:
```sh
python Scrapper.py
```

