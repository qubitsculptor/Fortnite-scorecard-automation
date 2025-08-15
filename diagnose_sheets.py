#!/usr/bin/env python3
"""
Google Sheets Setup Diagnostic Tool
Run this to check if your Google Sheets integration is properly configured.
"""

import sys
import os

# Add current directory to path so we can import fortnite_processor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fortnite_processor import FortniteScoreboardProcessor

def main():
    print("🚀 Fortnite Scorecard - Google Sheets Diagnostic")
    print("=" * 50)
    
    # Initialize processor
    try:
        processor = FortniteScoreboardProcessor()
    except Exception as e:
        print(f"❌ Failed to initialize processor: {e}")
        return False
    
    # Run diagnostics
    success = processor.diagnose_google_sheets_setup()
    
    if success:
        print("\n🎉 SUCCESS! Your Google Sheets setup is working correctly.")
        print("You can now use the Export to Google Sheets feature.")
    else:
        print("\n❌ ISSUES FOUND! Please fix the above problems.")
        print("\n📋 Quick Checklist:")
        print("1. ✅ credentials.json file exists")
        print("2. ✅ .env file has correct GOOGLE_SHEET_ID")
        print("3. ✅ Google Sheet is shared with service account email")
        print("4. ✅ Service account has 'Editor' permissions")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
