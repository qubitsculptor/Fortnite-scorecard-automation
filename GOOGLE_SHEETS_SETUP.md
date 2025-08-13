# 🔗 Google Sheets Integration Setup

## Required for Auto-Update Feature

Since you want the system to automatically update your existing leaderboard Google Sheet, you'll need to set up Google Sheets API access.

## Step-by-Step Setup

### 1. Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click "Select a project" → "New Project"
3. Name it "Fortnite Leaderboard" 
4. Click "Create"

### 2. Enable Google Sheets API
1. In your new project, go to "APIs & Services" → "Library"
2. Search for "Google Sheets API"
3. Click on it and click "Enable"

### 3. Create Service Account
1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "Service Account"
3. Name: "Fortnite Stats Bot"
4. Description: "Automated scorecard processor"
5. Click "Create and Continue"
6. Skip roles (click "Continue")
7. Click "Done"

### 4. Download Credentials
1. In the Credentials page, find your service account
2. Click on it to open details
3. Go to "Keys" tab
4. Click "Add Key" → "Create New Key"
5. Choose "JSON" format
6. Click "Create"
7. **Save the downloaded file as `credentials.json` in your project folder**

### 5. Share Your Google Sheet
1. Open your existing leaderboard Google Sheet
2. Click "Share" button
3. **Add the service account email** (found in credentials.json as "client_email")
   - It looks like: `fortnite-stats@your-project-name.iam.gserviceaccount.com`
4. Give it "Editor" permissions
5. Click "Send"

### 6. Get Your Sheet ID
1. From your Google Sheet URL: 
   `https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit`
2. Copy the `YOUR_SHEET_ID` part
3. Add it to your `.env` file:
   ```
   GOOGLE_SHEET_ID=YOUR_SHEET_ID
   ```

## File Structure You'll Need

```
fortnite-scorecard/
├── credentials.json          ← The file you downloaded
├── .env                     ← Your API keys
├── app_new.py              ← Main application
└── fortnite_processor.py   ← Processing engine
```

## Your .env File Should Look Like:

```
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_SHEET_ID=your_actual_sheet_id_here
GOOGLE_SHEETS_CREDENTIALS_FILE=credentials.json
WORKSHEET_NAME=Sheet1
ENABLE_DUPLICATE_CHECK=true
```

## Testing the Connection

Once set up:
1. Run the app locally: `streamlit run app_new.py`
2. Upload a test screenshot
3. Click "Export to Google Sheets"
4. Check your Google Sheet - it should auto-update!

## Security Notes

- **Keep `credentials.json` secure** - it's like a password
- **Add `credentials.json` to `.gitignore`** so it's not uploaded to GitHub
- **For deployment**, upload the credentials content as environment variables

## Troubleshooting

**"Permission denied"** → Make sure you shared the sheet with the service account email
**"Sheet not found"** → Double-check your GOOGLE_SHEET_ID in the .env file
**"API not enabled"** → Make sure Google Sheets API is enabled in your project

Once this is set up, your leaderboard will update automatically every time you process scorecards! 🎯
