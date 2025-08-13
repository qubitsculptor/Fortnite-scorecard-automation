# 🔒 Admin Panel Deployment Guide

Perfect for your setup! Deploy a **secure admin panel** on a separate website that only you can access.

## 🎯 Your Setup Overview

1. **Public Website**: Your existing leaderboard (displays data from Google Sheet)
2. **Admin Panel**: Secure scorecard processor (this tool) - separate subdomain  
3. **Data Flow**: Screenshots → AI Processing → Google Sheet → Your public leaderboard updates automatically

## 🚀 Recommended: Streamlit Cloud (Free/Paid)

### Step 1: Prepare for Deployment
1. **Create Private GitHub Repository**
   ```bash
   git init
   git add .
   git commit -m "Fortnite Admin Panel - Ready for deployment"
   git remote add origin https://github.com/yourusername/fortnite-admin.git
   git push -u origin main
   ```

2. **Ensure .gitignore includes**
   ```
   .env
   credentials.json
   *.csv
   __pycache__/
   ```

### Step 2: Deploy to Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Connect your GitHub account
3. Select your repository
4. **Important**: Set main file as `app_secure.py` (password protected)
5. Configure secrets in Streamlit dashboard:
   ```toml
   GEMINI_API_KEY = "your_api_key_here"
   GOOGLE_SHEET_ID = "your_existing_sheet_id_here"
   ADMIN_PASSWORD = "your_secure_password_here"
   ```
6. Upload `credentials.json` content as secret

### Step 3: Custom Subdomain Setup
1. Point `admin.yourwebsite.com` to your Streamlit app
2. In Streamlit Cloud settings, add custom domain
3. SSL certificate automatically provided

## 🔗 Your Workflow

### For You (Admin):
1. Visit `admin.yourwebsite.com`
2. Enter your password
3. Upload scorecard screenshots
4. Click "Process & Update Leaderboard"
5. Your public website updates automatically!

## 🌐 Alternative: Netlify (Your Platform)

Since you mentioned using Netlify, here's how to deploy there:

### Option 1: Static Site + External Streamlit
1. **Deploy Streamlit Admin Panel** on Railway/Streamlit Cloud
2. **Keep your current Netlify setup** for the public leaderboard
3. **Perfect separation**: Admin tool separate from public site

### Option 2: Netlify Functions (Advanced)
Deploy the admin panel as Netlify functions:
```bash
# Create netlify.toml
[build]
  command = "pip install -r requirements.txt"
  functions = "netlify/functions"

[[redirects]]
  from = "/admin/*"
  to = "/.netlify/functions/admin"
  status = 200
```

## 💰 Cost Breakdown (Perfect for Business)

### Streamlit Cloud
- **Free**: Public apps (not suitable for admin)
- **$20/month**: Private apps with password protection ✅

### API Costs (Pay per use)
- **Google Gemini**: ~$0.01-0.05 per screenshot
- **Example**: 500 screenshots/month = $5-25

### Total: $25-45/month for complete system

## 🔐 Security Features

### Built-in Password Protection
- Simple login screen
- Only you have access
- No complex user management needed

### Environment Variables
Store securely in platform secrets:
- `ADMIN_PASSWORD` - Your login password
- `GEMINI_API_KEY` - AI processing
- `GOOGLE_SHEET_ID` - Your existing spreadsheet

### Data Flow Security
- Screenshots processed via AI
- Results sent directly to your existing Google Sheet
- No data stored on admin server
- Public website remains unchanged

## ⚡ Quick Setup (15 Minutes)

1. **Create private GitHub repo** with this code
2. **Deploy to Streamlit Cloud** (free signup)
3. **Set environment variables** in dashboard
4. **Point admin.yourwebsite.com** to the app
5. **Test the workflow** with sample screenshots

## 🎯 Perfect Solution For You

✅ **Separate admin site** - No changes to your current website
✅ **Password protected** - Only you can access
✅ **Auto-updates your leaderboard** - Via your existing Google Sheet
✅ **Mobile friendly** - Upload screenshots from phone/iPad
✅ **Cost effective** - ~$25-45/month total
✅ **Zero maintenance** - Cloud hosted, auto-scaling

## 📱 Mobile Optimized Workflow

1. Take screenshot on iPad during match
2. Open admin panel on any device
3. Upload screenshot (drag & drop)
4. AI processes and updates leaderboard
5. Your public website shows new stats immediately

## 🚦 Ready to Deploy?

Choose your deployment method:
- **Streamlit Cloud**: Easiest, $20/month
- **Railway**: Developer-friendly, $5/month  
- **Netlify**: Use your current platform

All options give you the same result: **Secure admin panel that updates your public leaderboard automatically!**

---

**Next Step**: Create the secure admin panel (`app_secure.py`) and deploy! 🚀
