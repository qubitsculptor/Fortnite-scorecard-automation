# 🌐 Website Deployment Instructions

## Your Situation
You have an **existing leaderboard website** that displays data from a **Google Sheet**. You want to add this Fortnite scorecard processor as a **separate admin tool** that only you can access.

## Perfect Setup for You

### What You'll Have:
1. **Your Current Website** - Public leaderboard (unchanged)
2. **Admin Tool** - Separate secure website for uploading scorecards
3. **Google Sheet** - Connects both (admin updates it, public reads it)

##  Recommended: Deploy on Streamlit Cloud

### Step 1: Create GitHub Repository
```bash
git init
git add .
git commit -m "Fortnite Admin Panel"
git push to your GitHub repo
```

### Step 2: Deploy to Streamlit Cloud
1. Go to **share.streamlit.io**
2. Connect your GitHub repo
3. Set main file as **`app_new.py`**
4. Add these environment variables:
   ```
   GEMINI_API_KEY = your_gemini_api_key
   GOOGLE_SHEET_ID = your_existing_sheet_id
   ADMIN_PASSWORD = your_secure_password
   ```

### Step 3: Point Your Domain
- Point **admin.yourwebsite.com** to the Streamlit app
- Keep your main website unchanged

## Your Workflow
1. Take screenshots during tournaments
2. Visit **admin.yourwebsite.com**  
3. Upload screenshots (drag & drop)
4. AI processes and updates your Google Sheet
5. Your public leaderboard automatically shows new data

## Cost
- **Streamlit Cloud**: Free for testing, $20/month for private
- **Google Gemini AI**: ~$0.01-0.05 per screenshot
- **Total**: ~$25-45/month

## Alternative: Use Netlify
Since you mentioned Netlify:
1. Deploy this tool on **Railway** ($5/month) or **Streamlit Cloud** 
2. Keep your current Netlify setup for the public leaderboard
3. Perfect separation - admin tool separate from public site

## Files You Need
- `app_new.py` - Main application (already in the ZIP)
- `fortnite_processor.py` - Processing engine (already working)
- `requirements.txt` - Dependencies (included)

## Quick Start
1. Get Gemini API key from **aistudio.google.com** (free)
2. Deploy using Streamlit Cloud or your preferred platform  
3. Add environment variables
4. Point subdomain to the app
5. Start uploading scorecards!

**Result**: Secure admin panel that automatically updates your existing leaderboard via Google Sheets.
