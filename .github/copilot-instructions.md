<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Fortnite Scorecard Processor Instructions

This is a Python project for automated processing of Fortnite Ballistic scorecard screenshots using Google Gemini AI.

## Project Structure
- `fortnite_processor.py` - Core processing logic with Gemini AI integration
- `app.py` - Streamlit web interface for easy uploads
- `cli.py` - Command-line interface for batch processing
- `screenshots/` - Folder for input images
- `.env` - Configuration file with API keys

## Key Technologies
- Google Gemini AI (gemini-1.5-flash) for image analysis and data extraction
- Google Sheets API for data export
- Streamlit for web interface
- pandas for data manipulation

## Coding Guidelines
- Follow Python best practices and PEP 8
- Include comprehensive error handling
- Use type hints for better code clarity
- Focus on accuracy for scorecard data extraction
- Optimize for mobile/iPad usage in web interface
- Implement duplicate detection to avoid processing same images
- Provide clear user feedback and status messages

## API Integration Notes
- Gemini API requires specific prompting for JSON structured output
- Google Sheets API needs service account authentication
- Always handle API rate limits and errors gracefully
- Cost-optimize by using efficient prompts and image processing

## Data Structure
Extract player data in this format:
- username, eliminations, deaths, assists, damage, plants, defuses, team
- Include match metadata: result, timestamp, image_file
- Support aggregation and statistics calculation
