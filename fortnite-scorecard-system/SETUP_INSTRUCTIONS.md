# Fortnite Ballistic Scorecard Processor - Setup Instructions

##  Overview
This tool automatically extracts player statistics from Fortnite Ballistic scorecard screenshots using AI and exports the data to CSV files and Google Sheets. It features advanced duplicate detection and player aggregation across multiple games.

##  What This Tool Does
- **AI-Powered Extraction**: Uses Google Gemini AI to read scorecard screenshots
- **Smart Duplicate Detection**: Automatically identifies and merges duplicate players across games
- **Data Aggregation**: Combines stats from multiple matches per player
- **Export Options**: Save to CSV files or directly export to Google Sheets
- **Web Interface**: Easy-to-use Streamlit web app

##  What's Included
- `app_new.py` - Main web application (use this one)
- `fortnite_processor.py` - Core processing engine
- `requirements.txt` - Python dependencies
- `credentials.json.example` - Google Sheets setup template
- `DEPLOYMENT.md` - Website deployment guide
- This setup guide

##  Deployment Options
This tool can be used in multiple ways:
- **Local Usage**: Run on your computer for personal use
- **Website Integration**: Deploy on your website for public access
- **Team Setup**: Share with team members via cloud deployment

For website deployment, see `DEPLOYMENT.md` for detailed instructions.ic Scorecard Processor - Setup Instructions

##  Overview
This tool automatically extracts player statistics from Fortnite Ballistic scorecard screenshots using AI and exports the data to CSV files and Google Sheets. It features advanced duplicate detection and player aggregation across multiple games.

## What This Tool Does
- **AI-Powered Extraction**: Uses Google Gemini AI to read scorecard screenshots
- **Smart Duplicate Detection**: Automatically identifies and merges duplicate players across games
- **Data Aggregation**: Combines stats from multiple matches per player
- **Export Options**: Save to CSV files or directly export to Google Sheets
- **Web Interface**: Easy-to-use Streamlit web app

## What's Included
- `app_new.py` - Main web application (use this one)
- `fortnite_processor.py` - Core processing engine
- `requirements.txt` - Python dependencies
- `credentials.json.example` - Google Sheets setup template
- This setup guide

##  Quick Start (Recommended)

### Step 1: Install Python
1. Download Python 3.8+ from https://python.org/downloads
2. During installation, **check "Add Python to PATH"**
3. Verify installation by opening Terminal/Command Prompt and typing:
   ```
   python --version
   ```

### Step 2: Extract and Setup
1. Extract the ZIP file to your desired location
2. Open Terminal/Command Prompt
3. Navigate to the project folder:
   ```
   cd path/to/fortnite-scorecard
   ```

### Step 3: Install Dependencies
Run this command to install all required packages:
```bash
pip install -r requirements.txt
```

### Step 4: Setup API Keys
Create a file called `.env` in the project folder with this content:
```
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_SHEET_ID=your_google_sheet_id_here
```

### Step 5: Run the Application
```bash
streamlit run app_new.py
```

The app will open in your web browser at `http://localhost:8501`

##  API Setup (Required)

### Google Gemini AI (Required for Processing)
1. Go to [Google AI Studio](https://aistudio.google.com)
2. Sign in with your Google account
3. Click "Get API Key" → "Create API Key"
4. Copy the API key
5. Add it to your `.env` file as `GEMINI_API_KEY=your_key_here`

**Cost**: ~$0.01-0.05 per image (very affordable)

### Google Sheets (Optional - for direct export)
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing one
3. Enable Google Sheets API
4. Create Service Account:
   - Go to IAM & Admin → Service Accounts
   - Click "Create Service Account"
   - Name it "Fortnite Stats Bot"
   - Download the JSON credentials file
5. Rename the file to `credentials.json` and place in project folder
6. Create a Google Sheet and share it with the service account email
7. Copy the Sheet ID from the URL and add to `.env` file

## 📱 How to Use

### Basic Usage
1. Run the app: `streamlit run app_new.py`
2. Upload your Fortnite scorecard screenshots
3. Click "Process Images"
4. View aggregated player statistics
5. Export to CSV or Google Sheets

### Advanced Features
- **Duplicate Detection**: Players with similar usernames are automatically merged
- **Username Cleaning**: Removes TTV, DVS, special characters for better matching
- **Multi-Game Aggregation**: Combines stats across all uploaded screenshots
- **Smart Error Handling**: Handles OCR errors and partial data extraction

##  Data Output
The tool exports the following columns:
- Username (cleaned)
- Games Played
- Total Eliminations, Assists, Deaths, Plants, Defuses
- Average stats per game
- K/D Ratio
- Team information

##  Troubleshooting

### Common Issues

**"Gemini API Key Missing"**
- Make sure your `.env` file exists in the project folder
- Check that `GEMINI_API_KEY=` has your actual API key (no spaces)

**"Failed to process images"**
- Ensure images are clear and show the full scorecard
- Try with different image formats (PNG, JPG)
- Check that scorecards are from Fortnite Ballistic mode

**"Google Sheets not configured"**
- This is optional - you can still export CSV files
- Follow the Google Sheets setup steps if you want direct export

**"Module not found" errors**
- Run `pip install -r requirements.txt` again
- Make sure you're in the correct project folder

### Getting Help
If you encounter issues:
1. Check that all files are in the same folder
2. Verify your API keys in the `.env` file
3. Try restarting the application
4. Ensure your Python version is 3.8+

## 💡 Tips for Best Results

### Image Quality
- Use clear, high-resolution screenshots
- Ensure the entire scorecard is visible
- Avoid blurry or cropped images

### Batch Processing
- Upload multiple screenshots at once for efficiency
- The tool automatically detects and merges duplicate players
- Process 5-10 images at a time for optimal performance

### Cost Management
- Gemini AI costs ~$0.01-0.05 per image
- Process images in batches to minimize API calls
- The tool is optimized to keep costs low

##  Advanced Configuration

### Custom Google Sheets
To use your own Google Sheet:
1. Create a new Google Sheet
2. Share it with your service account email (found in credentials.json)
3. Copy the Sheet ID from the URL
4. Add `GOOGLE_SHEET_ID=your_sheet_id` to `.env` file

### Running on Different Ports
If port 8501 is busy:
```bash
streamlit run app_new.py --server.port 8502
```

##  Sample Workflow
1. Take screenshots of Fortnite Ballistic scorecards
2. Save them to your device
3. Open the web app
4. Upload 3-5 screenshots
5. Click "Process Images"
6. Review the aggregated player statistics
7. Export to CSV or Google Sheets
8. Analyze player performance across games

##  Security Notes
- Keep your `.env` file secure (contains API keys)
- Don't share your `credentials.json` file
- API keys are only used for processing - no data is stored externally

##  Support
The application includes:
- Real-time processing status
- Clear error messages
- API connection status indicators
- Built-in help text and tooltips

---

**Ready to start processing your Fortnite scorecards? Run `streamlit run app_new.py` and upload your first screenshots!** 
