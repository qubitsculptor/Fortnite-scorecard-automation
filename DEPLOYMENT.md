# Deployment Guide

## Option 1: Streamlit Cloud (Recommended - Free)

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/fortnite-scorecard.git
   git push -u origin main
   ```

2. **Deploy to Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub repo
   - Set main file: `app.py`
   - Add secrets in Streamlit dashboard:
     ```
     GEMINI_API_KEY = "your_api_key_here"
     GOOGLE_SHEET_ID = "your_sheet_id_here"
     ```
   - Upload `credentials.json` as a secret file

## Option 2: Railway (Paid - $5/month)

1. **Create railway.json**
   ```json
   {
     "build": {
       "builder": "NIXPACKS"
     },
     "deploy": {
       "startCommand": "streamlit run app.py --server.port $PORT --server.address 0.0.0.0"
     }
   }
   ```

2. **Deploy**
   - Push to GitHub
   - Connect to Railway
   - Add environment variables

## Option 3: Local Network (Free)

Run locally and access from other devices on your network:

```bash
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

Then access via: `http://your-local-ip:8501`

## Mobile Optimization

The app is already optimized for mobile with:
- Responsive design
- Touch-friendly file uploads
- Mobile-friendly interface
- Works great on iPad

## Cost Breakdown

- **Gemini API**: ~$0.01 per 100 images
- **Google Sheets**: Free
- **Streamlit Cloud**: Free
- **Railway**: $5/month (optional)

Total cost: **Nearly free!** 🎉
