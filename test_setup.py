# Quick Test Script
# Run this to test if everything is working

import os
from fortnite_processor import FortniteScoreboardProcessor

def test_setup():
    print("🧪 Testing Fortnite Scorecard Processor Setup...")
    
    # Check environment file
    if os.path.exists('.env'):
        print("✅ .env file found")
    else:
        print("⚠️ .env file not found - copy from .env.example")
    
    # Test processor initialization
    try:
        processor = FortniteScoreboardProcessor()
        print("✅ Processor initialized")
        
        # Check Gemini API
        if processor.model:
            print("✅ Gemini AI connected")
        else:
            print("❌ Gemini API key missing")
        
        # Check Google Sheets
        if processor.sheets_client:
            print("✅ Google Sheets connected")
        else:
            print("⚠️ Google Sheets not configured (optional)")
            
    except Exception as e:
        print(f"❌ Error initializing processor: {e}")
    
    # Check for screenshots
    screenshot_files = []
    if os.path.exists('screenshots'):
        for ext in ['*.png', '*.jpg', '*.jpeg']:
            import glob
            screenshot_files.extend(glob.glob(f'screenshots/{ext}'))
    
    if screenshot_files:
        print(f"📸 Found {len(screenshot_files)} screenshots ready for processing")
    else:
        print("📁 No screenshots found - add some to screenshots/ folder")
    
    print("\n🚀 Ready to process! Run:")
    print("   streamlit run app.py    (for web interface)")
    print("   python cli.py --folder screenshots    (for command line)")

if __name__ == "__main__":
    test_setup()
