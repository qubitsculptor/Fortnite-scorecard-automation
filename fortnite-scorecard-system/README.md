# Fortnite Ballistic Scorecard Automation

Automated system to extract player statistics from Fortnite Ballistic scorecard screenshots using Gemini AI and export to Google Sheets.

## Features

-  **High Accuracy**: Uses Google Gemini AI for superior OCR accuracy
-  **Auto Google Sheets**: Direct integration with Google Sheets
-  **Mobile Friendly**: Streamlit web interface works on iPad/mobile
- **Batch Processing**: Upload multiple screenshots at once
- **Duplicate Detection**: Automatically ignores duplicate entries
-  **Multiple Formats**: Export to CSV, Excel, or Google Sheets

## Quick Start

1. **Clone and Setup**
```bash
git clone <your-repo>
cd fortnite-scorecard
pip install -r requirements.txt
```

2. **Configure APIs**
- Get Gemini API key from Google AI Studio
- Setup Google Sheets API credentials
- Copy `.env.example` to `.env` and fill in your keys

3. **Run the App**
```bash
streamlit run app.py
```

## Setup Guide

### 1. Gemini API Setup
1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Create API key
3. Add to `.env` file

### 2. Google Sheets Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable Google Sheets API
3. Create service account and download JSON
4. Share your Google Sheet with the service account email

## Usage

1. **Upload Screenshots**: Drag and drop Fortnite scorecard images
2. **Process**: Click "Process Images" 
3. **Review**: Check extracted data
4. **Export**: Send to Google Sheets or download CSV

## Cost Estimate

- **Gemini API**: ~$0.001 per image (very cheap!)
- **Google Sheets**: Free
- **Hosting**: Free (Streamlit Cloud)

## Technical Details

- **AI Model**: Google Gemini 1.5 Flash (optimized for images)
- **Framework**: Python + Streamlit
- **Storage**: Google Sheets API
- **Image Processing**: PIL + Gemini Vision

---

Built for accuracy and ease of use! 🚀
