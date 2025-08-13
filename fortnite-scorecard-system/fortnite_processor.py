import os
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import google.generativeai as genai
import pandas as pd
from PIL import Image
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class FortniteScoreboardProcessor:
    def __init__(self):
        """Initialize the processor with API keys and configuration."""
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.sheets_credentials_file = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE')
        self.sheet_id = os.getenv('GOOGLE_SHEET_ID')
        self.worksheet_name = os.getenv('WORKSHEET_NAME', 'Leaderboard')
        
        # Configure Gemini
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None
            print("⚠️ Gemini API key not found. Please set GEMINI_API_KEY in .env file")
        
        # Setup Google Sheets if credentials available
        self.sheets_client = self._setup_google_sheets()
        
        # Duplicate detection
        self.enable_duplicate_check = os.getenv('ENABLE_DUPLICATE_CHECK', 'true').lower() == 'true'
        self.processed_hashes = set()
        
        # Duplicate detection is now enabled for production use
    
    def _setup_google_sheets(self) -> Optional[gspread.Client]:
        """Setup Google Sheets client if credentials are available."""
        if not self.sheets_credentials_file or not os.path.exists(self.sheets_credentials_file):
            print("⚠️ Google Sheets credentials not found. Export will be CSV only.")
            return None
        
        try:
            # Define the scope
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # Load credentials
            credentials = Credentials.from_service_account_file(
                self.sheets_credentials_file, 
                scopes=scope
            )
            
            return gspread.authorize(credentials)
        except Exception as e:
            print(f"⚠️ Failed to setup Google Sheets: {e}")
            return None
    
    def _get_image_hash(self, image_path: str) -> str:
        """Generate hash for duplicate detection."""
        with open(image_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def _create_extraction_prompt(self) -> str:
        """Create the system prompt for Gemini to extract scorecard data."""
        return """
You are an expert at extracting data from Fortnite Ballistic game scorecards. 

Analyze this scorecard image and extract the player statistics in JSON format.

Look for:
- Player usernames/names
- Eliminations (kills)
- Deaths
- Assists  
- Damage dealt
- Plants (bomb plants)
- Defuses (bomb defuses)

Return ONLY a JSON object with this exact structure:
{
    "players": [
        {
            "username": "player_name",
            "eliminations": 0,
            "deaths": 0, 
            "assists": 0,
            "damage": 0,
            "plants": 0,
            "defuses": 0,
            "team": "ATK" or "DEF"
        }
    ],
    "match_info": {
        "match_result": "VICTORY" or "DEFEAT",
        "rounds_won": 0,
        "rounds_lost": 0,
        "timestamp": "auto_generated"
    }
}

CRITICAL USERNAME RULES:
- Clean up usernames by removing common gaming prefixes/suffixes
- Remove streaming prefixes: TTV, TWITCH, YT, YOUTUBE, STREAM (at start or end)
- Remove clan/team tags: DVS, KTK, GVG, ZMR, FAZE, TSM, NRG, OG (at start)
- Remove special characters, numbers, and symbols: *, ², _, -, spaces, etc.
- Keep only the core alphabetic username
- Examples: "TTV HEARTMADDI" → "HEARTMADDI", "*QUINTIN" → "QUINTIN", "dvs SCOPE" → "SCOPE"
- If username becomes empty after cleaning, use original

OTHER RULES:
- Extract ALL players from the scoreboard
- Convert all stats to integers
- If a stat is not visible, use 0
- Team should be "ATK" or "DEF" based on the scoreboard
- Be very accurate with numbers
"""

    def process_image(self, image_path: str) -> Optional[Dict]:
        """Process a single image and extract scorecard data."""
        if not self.model:
            print("❌ Gemini model not available")
            return None
        
        # Check for duplicates
        if self.enable_duplicate_check:
            image_hash = self._get_image_hash(image_path)
            if image_hash in self.processed_hashes:
                print(f"⏭️ Skipping duplicate image: {os.path.basename(image_path)}")
                return None
            self.processed_hashes.add(image_hash)
        
        try:
            # Load and process image
            image = Image.open(image_path)
            
            # Create prompt
            prompt = self._create_extraction_prompt()
            
            # Generate response
            print(f"🔄 Processing {os.path.basename(image_path)}...")
            response = self.model.generate_content([prompt, image])
            
            # Parse JSON response
            json_text = response.text.strip()
            if json_text.startswith('```json'):
                json_text = json_text[7:-3]
            elif json_text.startswith('```'):
                json_text = json_text[3:-3]
            
            data = json.loads(json_text)
            
            # Add processing timestamp
            data['match_info']['timestamp'] = datetime.now().isoformat()
            data['match_info']['image_file'] = os.path.basename(image_path)
            
            print(f"✅ Extracted data for {len(data['players'])} players")
            return data
            
        except Exception as e:
            print(f"❌ Error processing {image_path}: {e}")
            return None
    
    def process_batch(self, image_paths: List[str]) -> List[Dict]:
        """Process multiple images and return combined results."""
        all_results = []
        
        for image_path in image_paths:
            result = self.process_image(image_path)
            if result:
                all_results.append(result)
        
        return all_results
    
    def export_to_csv(self, results: List[Dict], output_file: str = None) -> str:
        """Export aggregated results to CSV with improved duplicate detection."""
        if not results:
            print("❌ No results to export")
            return None
        
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"fortnite_stats_{timestamp}.csv"
        
        def normalize_username(username: str) -> str:
            """Robust username normalization for duplicate detection - algorithmic approach."""
            import re
            
            original = username.strip()
            
            # Simple cleanup as backup (AI should already handle this)
            normalized = re.sub(r'[^a-zA-Z]', '', original).lower()
            
            # Handle common OCR errors and typos
            # Remove repeated letters that might be OCR errors (e.g., SKITTLE -> SKITLE)
            normalized = re.sub(r'(.)\1+', r'\1', normalized)
            
            # Handle common OCR substitutions
            normalized = normalized.replace('0', 'o').replace('1', 'i').replace('5', 's')
            
            # Handle anonymous/placeholder names separately
            if 'anonymous' in original.lower() or 'player' in original.lower():
                return original.lower()
            
            # Fallback if normalization fails
            if not normalized.strip():
                return original.lower()
                
            return normalized.strip()
        
        # Aggregate data by player (normalize usernames for better matching)
        player_aggregates = {}
        
        for result in results:
            match_info = result['match_info']
            for player in result['players']:
                # Skip players with empty/blank usernames
                if not player['username'] or not player['username'].strip():
                    print(f"⚠️ Skipping player with empty username (team: {player.get('team', 'unknown')})")
                    continue
                
                # Normalize username for matching
                username_key = normalize_username(player['username'])
                original_username = player['username']  # Keep original for display
                
                # Double-check after normalization
                if not username_key or not username_key.strip():
                    print(f"⚠️ Skipping player - username became empty after normalization: '{original_username}'")
                    continue
                
                if username_key not in player_aggregates:
                    # First time seeing this player
                    player_aggregates[username_key] = {
                        'username': original_username,  # Use first occurrence for display
                        'team': player['team'],  # Use most recent team
                        'games_played': 0,
                        'total_eliminations': 0,
                        'total_deaths': 0,
                        'total_assists': 0,
                        'total_damage': 0,
                        'total_plants': 0,
                        'total_defuses': 0,
                        'victories': 0,
                        'defeats': 0,
                        'last_seen': match_info['timestamp'],
                        'first_seen': match_info['timestamp']
                    }
                
                # Aggregate stats
                stats = player_aggregates[username_key]
                stats['games_played'] += 1
                stats['total_eliminations'] += player['eliminations']
                stats['total_deaths'] += player['deaths']
                stats['total_assists'] += player['assists']
                stats['total_damage'] += player['damage']
                stats['total_plants'] += player['plants']
                stats['total_defuses'] += player['defuses']
                
                # Track wins/losses
                if match_info.get('match_result') == 'VICTORY':
                    stats['victories'] += 1
                else:
                    stats['defeats'] += 1
                
                # Update last seen and team
                stats['last_seen'] = match_info['timestamp']
                stats['team'] = player['team']  # Use most recent team
        
        # Convert to rows with calculated averages
        rows = []
        for username_key, stats in player_aggregates.items():
            games = stats['games_played']
            row = {
                'username': stats['username'],
                'games_played': games,
                'total_eliminations': stats['total_eliminations'],
                'total_assists': stats['total_assists'],
                'total_deaths': stats['total_deaths'],
                'total_plants': stats['total_plants'],
                'total_defuses': stats['total_defuses'],
                'avg_eliminations': round(stats['total_eliminations'] / games, 2),
                'avg_assists': round(stats['total_assists'] / games, 2),
                'avg_deaths': round(stats['total_deaths'] / games, 2),
                'avg_plants': round(stats['total_plants'] / games, 2),
                'avg_defuses': round(stats['total_defuses'] / games, 2),
                'kd_ratio': round(stats['total_eliminations'] / max(stats['total_deaths'], 1), 2),
                'team': stats['team'],
                'total_damage': stats['total_damage'],
                'avg_damage': round(stats['total_damage'] / games, 2),
                'first_seen': stats['first_seen'],
                'last_seen': stats['last_seen']
            }
            rows.append(row)
        
        # Sort by total eliminations (or K/D ratio)
        rows.sort(key=lambda x: x['kd_ratio'], reverse=True)
        
        # Create DataFrame and save
        df = pd.DataFrame(rows)
        df.to_csv(output_file, index=False)
        
        print(f"📊 Aggregated data for {len(rows)} unique players exported to {output_file}")
        return output_file
    
    def export_to_google_sheets(self, results: List[Dict]) -> bool:
        """Export aggregated results to Google Sheets with COMBINE mode - merges with existing data."""
        if not self.sheets_client or not self.sheet_id:
            print("❌ Google Sheets not configured")
            return False
        
        try:
            # Open the worksheet
            sheet = self.sheets_client.open_by_key(self.sheet_id)
            worksheet = sheet.worksheet(self.worksheet_name)
            
            def normalize_username(username: str) -> str:
                """Lightweight backup normalization - AI should handle most cases."""
                import re
                
                original = username.strip()
                
                # Simple cleanup as backup (AI should already handle this)
                normalized = re.sub(r'[^a-zA-Z]', '', original).lower()
                
                # Handle anonymous/placeholder names separately
                if 'anonymous' in original.lower() or 'player' in original.lower():
                    return original.lower()
                
                # Fallback if normalization fails
                if not normalized.strip():
                    return original.lower()
                    
                return normalized.strip()
            
            # STEP 1: Read existing data from Google Sheet
            print("🔍 Reading existing leaderboard data...")
            existing_data = {}
            try:
                all_records = worksheet.get_all_records()
                for record in all_records:
                    if record.get('username'):  # Skip empty rows
                        username_key = normalize_username(record['username'])
                        existing_data[username_key] = {
                            'username': record.get('username', ''),
                            'games_played': int(record.get('games_played', 0)),
                            'total_eliminations': int(record.get('total_eliminations', 0)),
                            'total_deaths': int(record.get('total_deaths', 0)),
                            'total_assists': int(record.get('total_assists', 0)),
                            'total_damage': int(record.get('total_damage', 0)),
                            'total_plants': int(record.get('total_plants', 0)),
                            'total_defuses': int(record.get('total_defuses', 0)),
                            'team': record.get('team', ''),
                            'last_seen': record.get('last_updated', record.get('last_seen', ''))
                        }
                print(f"📊 Found {len(existing_data)} existing players in leaderboard")
            except Exception as e:
                print(f"⚠️ No existing data found or error reading sheet: {e}")
                existing_data = {}
            
            # STEP 2: Process new data from screenshots
            print("🔄 Processing new screenshot data...")
            new_player_data = {}
            
            for result in results:
                match_info = result['match_info']
                for player in result['players']:
                    # Skip players with empty/blank usernames
                    if not player['username'] or not player['username'].strip():
                        print(f"⚠️ Skipping player with empty username (team: {player.get('team', 'unknown')})")
                        continue
                    
                    username_key = normalize_username(player['username'])
                    original_username = player['username']
                    
                    # Double-check after normalization
                    if not username_key or not username_key.strip():
                        print(f"⚠️ Skipping player - username became empty after normalization: '{original_username}'")
                        continue
                    
                    if username_key not in new_player_data:
                        new_player_data[username_key] = {
                            'username': original_username,
                            'team': player['team'],
                            'games_played': 0,
                            'total_eliminations': 0,
                            'total_deaths': 0,
                            'total_assists': 0,
                            'total_damage': 0,
                            'total_plants': 0,
                            'total_defuses': 0,
                            'last_seen': match_info['timestamp']
                        }
                    
                    stats = new_player_data[username_key]
                    stats['games_played'] += 1
                    stats['total_eliminations'] += player['eliminations']
                    stats['total_deaths'] += player['deaths']
                    stats['total_assists'] += player['assists']
                    stats['total_damage'] += player['damage']
                    stats['total_plants'] += player['plants']
                    stats['total_defuses'] += player['defuses']
                    stats['last_seen'] = match_info['timestamp']
                    stats['team'] = player['team']
            
            print(f"🆕 Found {len(new_player_data)} unique players in new screenshots")
            
            # STEP 3: COMBINE existing and new data
            print("🔄 Combining existing leaderboard with new data...")
            combined_data = existing_data.copy()  # Start with existing data
            
            for username_key, new_stats in new_player_data.items():
                if username_key in combined_data:
                    # COMBINE: Add new stats to existing player
                    existing_stats = combined_data[username_key]
                    existing_stats['games_played'] += new_stats['games_played']
                    existing_stats['total_eliminations'] += new_stats['total_eliminations']
                    existing_stats['total_deaths'] += new_stats['total_deaths']
                    existing_stats['total_assists'] += new_stats['total_assists']
                    existing_stats['total_damage'] += new_stats['total_damage']
                    existing_stats['total_plants'] += new_stats['total_plants']
                    existing_stats['total_defuses'] += new_stats['total_defuses']
                    existing_stats['team'] = new_stats['team']  # Use most recent team
                    existing_stats['last_seen'] = new_stats['last_seen']  # Update timestamp
                    print(f"✅ COMBINED: {new_stats['username']} - added {new_stats['games_played']} more games")
                else:
                    # NEW: Add completely new player
                    combined_data[username_key] = new_stats
                    print(f"🆕 NEW: {new_stats['username']} - first time on leaderboard")
            
            print(f"📊 Final leaderboard: {len(combined_data)} total players")
            
            # STEP 4: Prepare rows for Google Sheet
            rows_to_add = []
            for username_key, stats in combined_data.items():
                games = stats['games_played']
                if games > 0:  # Skip players with 0 games
                    row = [
                        stats['last_seen'],
                        stats['username'],
                        games,
                        stats['total_eliminations'],
                        stats['total_assists'],
                        stats['total_deaths'],
                        stats['total_plants'],
                        stats['total_defuses'],
                        round(stats['total_eliminations'] / games, 2),  # avg_eliminations
                        round(stats['total_assists'] / games, 2),  # avg_assists
                        round(stats['total_deaths'] / games, 2),  # avg_deaths
                        round(stats['total_plants'] / games, 2),  # avg_plants
                        round(stats['total_defuses'] / games, 2),  # avg_defuses
                        round(stats['total_eliminations'] / max(stats['total_deaths'], 1), 2),  # kd_ratio
                        stats['team'],
                        stats['total_damage'],
                        round(stats['total_damage'] / games, 2)  # avg_damage
                    ]
                    rows_to_add.append(row)
            
            # STEP 5: Update Google Sheet with combined data
            print("📝 Updating Google Sheet with combined leaderboard...")
            
            # Check if headers exist, create if needed
            try:
                headers = worksheet.row_values(1)
                if not headers or len(headers) < 10:
                    headers = [
                        'last_updated', 'username', 'games_played',
                        'total_eliminations', 'total_assists', 'total_deaths', 
                        'total_plants', 'total_defuses',
                        'avg_eliminations', 'avg_assists', 'avg_deaths', 'avg_plants', 'avg_defuses',
                        'kd_ratio', 'team', 'total_damage', 'avg_damage'
                    ]
                    worksheet.clear()  # Clear everything if headers are wrong
                    worksheet.append_row(headers)
                    print("📋 Created new headers")
            except Exception as e:
                print(f"⚠️ Creating new headers due to error: {e}")
                headers = [
                    'last_updated', 'username', 'games_played',
                    'total_eliminations', 'total_assists', 'total_deaths', 
                    'total_plants', 'total_defuses',
                    'avg_eliminations', 'avg_assists', 'avg_deaths', 'avg_plants', 'avg_defuses',
                    'kd_ratio', 'team', 'total_damage', 'avg_damage'
                ]
                worksheet.clear()
                worksheet.append_row(headers)
            
            # Clear existing data rows (keep headers)
            if len(worksheet.get_all_values()) > 1:
                worksheet.delete_rows(2, len(worksheet.get_all_values()))
            
            # Sort by K/D ratio and add combined data
            rows_to_add.sort(key=lambda x: x[13], reverse=True)  # Sort by kd_ratio (index 13)
            
            # Add rows in batches for better performance
            batch_size = 100
            for i in range(0, len(rows_to_add), batch_size):
                batch = rows_to_add[i:i+batch_size]
                for row in batch:
                    worksheet.append_row(row)
                print(f"📊 Added batch {i//batch_size + 1}/{(len(rows_to_add)-1)//batch_size + 1}")
            
            print(f"✅ Successfully updated leaderboard with {len(rows_to_add)} players")
            print(f"📈 COMBINE mode: Existing players updated, new players added!")
            return True
            
        except Exception as e:
            print(f"❌ Error exporting to Google Sheets: {e}")
            return False
    
    def create_summary_stats(self, results: List[Dict]) -> Dict:
        """Create summary statistics from the results."""
        all_players = []
        for result in results:
            all_players.extend(result['players'])
        
        if not all_players:
            return {}
        
        # Group by username
        player_stats = {}
        for player in all_players:
            username = player['username']
            if username not in player_stats:
                player_stats[username] = {
                    'games': 0,
                    'total_eliminations': 0,
                    'total_deaths': 0,
                    'total_assists': 0,
                    'total_damage': 0,
                    'total_plants': 0,
                    'total_defuses': 0
                }
            
            stats = player_stats[username]
            stats['games'] += 1
            stats['total_eliminations'] += player['eliminations']
            stats['total_deaths'] += player['deaths']
            stats['total_assists'] += player['assists']
            stats['total_damage'] += player['damage']
            stats['total_plants'] += player['plants']
            stats['total_defuses'] += player['defuses']
        
        # Calculate averages
        for username, stats in player_stats.items():
            games = stats['games']
            stats['avg_eliminations'] = round(stats['total_eliminations'] / games, 2)
            stats['avg_deaths'] = round(stats['total_deaths'] / games, 2)
            stats['avg_assists'] = round(stats['total_assists'] / games, 2)
            stats['avg_damage'] = round(stats['total_damage'] / games, 2)
            stats['kd_ratio'] = round(stats['total_eliminations'] / max(stats['total_deaths'], 1), 2)
        
        return player_stats

# Example usage
if __name__ == "__main__":
    processor = FortniteScoreboardProcessor()
    
    # Process images from a folder
    import glob
    image_files = glob.glob("screenshots/*.png") + glob.glob("screenshots/*.jpg")
    
    if image_files:
        print(f"Found {len(image_files)} images to process...")
        results = processor.process_batch(image_files)
        
        if results:
            # Export to CSV
            csv_file = processor.export_to_csv(results)
            
            # Export to Google Sheets (if configured)
            processor.export_to_google_sheets(results)
            
            # Show summary
            summary = processor.create_summary_stats(results)
            print("\n📈 Player Summary:")
            for username, stats in summary.items():
                print(f"{username}: {stats['avg_eliminations']} avg kills, {stats['kd_ratio']} K/D")
        else:
            print("❌ No data extracted from images")
    else:
        print("❌ No images found in screenshots/ folder")
