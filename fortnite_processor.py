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

# Try to import streamlit for cloud deployment
try:
    import streamlit as st
    IS_STREAMLIT = True
except ImportError:
    IS_STREAMLIT = False

class FortniteScoreboardProcessor:
    def __init__(self):
        """Initialize the processor with API keys and configuration."""
        # Get configuration from Streamlit secrets (cloud) or environment variables (local)
        if IS_STREAMLIT:
            try:
                # Try to get from Streamlit secrets first (for cloud deployment)
                self.gemini_api_key = st.secrets.get('GEMINI_API_KEY')
                self.sheet_id = st.secrets.get('GOOGLE_SHEET_ID')
                self.worksheet_name = st.secrets.get('WORKSHEET_NAME', 'Sheet1')
                self.sheets_credentials_data = st.secrets.get('google_credentials', {})
                self.sheets_credentials_file = None  # Will use data instead
                print("📊 Using Streamlit secrets configuration")
            except Exception:
                # Fallback to environment variables if Streamlit secrets fail
                print("⚠️ Streamlit secrets not found, using environment variables")
                self.gemini_api_key = os.getenv('GEMINI_API_KEY')
                self.sheets_credentials_file = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE')
                self.sheet_id = os.getenv('GOOGLE_SHEET_ID')
                self.worksheet_name = os.getenv('WORKSHEET_NAME', 'Leaderboard')
                self.sheets_credentials_data = None
        else:
            # Local development (non-Streamlit)
            self.gemini_api_key = os.getenv('GEMINI_API_KEY')
            self.sheets_credentials_file = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE')
            self.sheet_id = os.getenv('GOOGLE_SHEET_ID')
            self.worksheet_name = os.getenv('WORKSHEET_NAME', 'Leaderboard')
            self.sheets_credentials_data = None
            print("🔧 Using environment variables configuration")
        
        # Configure Gemini
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None
            print("⚠️ Gemini API key not found. Please set GEMINI_API_KEY in .env file")
        
        # Setup Google Sheets if credentials available
        self.sheets_client = self._setup_google_sheets()
        
        # Store service account email for diagnostics
        self.service_account_email = None
        if self.sheets_client:
            if self.sheets_credentials_data:
                # Streamlit Cloud - get email from secrets
                self.service_account_email = self.sheets_credentials_data.get('client_email')
            elif self.sheets_credentials_file and os.path.exists(self.sheets_credentials_file):
                # Local - get email from file
                try:
                    import json
                    with open(self.sheets_credentials_file, 'r') as f:
                        creds_data = json.load(f)
                        self.service_account_email = creds_data.get('client_email')
                except Exception:
                    pass
        
        # Duplicate detection
        if IS_STREAMLIT:
            try:
                duplicate_check = st.secrets.get('ENABLE_DUPLICATE_CHECK', 'true')
            except Exception:
                duplicate_check = os.getenv('ENABLE_DUPLICATE_CHECK', 'true')
        else:
            duplicate_check = os.getenv('ENABLE_DUPLICATE_CHECK', 'true')
        
        self.enable_duplicate_check = duplicate_check.lower() == 'true'
        self.processed_hashes = set()
        
        # Duplicate detection is now enabled for production use
    
    def _setup_google_sheets(self) -> Optional[gspread.Client]:
        """Setup Google Sheets client if credentials are available."""
        try:
            # Define the scope
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            if self.sheets_credentials_data:
                # Streamlit Cloud - use credentials from secrets
                credentials = Credentials.from_service_account_info(
                    self.sheets_credentials_data, 
                    scopes=scope
                )
                return gspread.authorize(credentials)
            elif self.sheets_credentials_file and os.path.exists(self.sheets_credentials_file):
                # Local development - use credentials from file
                credentials = Credentials.from_service_account_file(
                    self.sheets_credentials_file, 
                    scopes=scope
                )
                return gspread.authorize(credentials)
            else:
                print("⚠️ Google Sheets credentials not found. Export will be CSV only.")
                return None
                
        except Exception as e:
            print(f"⚠️ Failed to setup Google Sheets: {e}")
            return None
    
    def _get_image_hash(self, image_path: str) -> str:
        """Generate hash for duplicate detection."""
        with open(image_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def _create_extraction_prompt(self, existing_players: List[str] = None) -> str:
        """Create the system prompt for Gemini to extract scorecard data with existing player context."""
        
        # Build existing players context
        player_context = ""
        if existing_players and len(existing_players) > 0:
            # Limit to top 200 most active players to keep prompt manageable
            top_players = existing_players[:200]
            player_context = f"""
🎯 KNOWN PLAYERS CONTEXT (be consistent with these):
{', '.join(top_players)}

When you see usernames that look similar to these known players, use the EXACT same spelling.
Examples:
- If you see "2AMDIBBS" and "dibbs" is in known players → use "dibbs"
- If you see "NVFJJ7" and "jj" is in known players → use "jj"  
- If you see "DOBy" and "dob" is in known players → use "dob"
- If you see "ZQUINTIN" and "quintin" is in known players → use "quintin"

PRIORITIZE CONSISTENCY with known players over exact visual spelling.
"""
        
        return f"""
You are an expert at extracting data from Fortnite Ballistic game scorecards.

CRITICAL MISSION: Extract player usernames with PERFECT CONSISTENCY across all images.
{player_context}
Return ONLY this JSON structure:
{{
    "players": [
        {{
            "username": "CONSISTENT_NAME",
            "eliminations": 0,
            "deaths": 0, 
            "assists": 0,
            "damage": 0,
            "plants": 0,
            "defuses": 0,
            "team": "ATK" or "DEF"
        }}
    ],
    "match_info": {{
        "match_result": "VICTORY" or "DEFEAT",
        "rounds_won": 0,
        "rounds_lost": 0,
        "timestamp": "auto_generated"
    }}
}}

🚨 USERNAME CONSISTENCY PROTOCOL 🚨

STEP 1: Look at the username in the image
STEP 2: Check if it matches or looks similar to any KNOWN PLAYERS above
STEP 3: If similar match found → use the KNOWN PLAYER name exactly
STEP 4: If no match → extract cleanly (remove tiny clan tags only)

ABSOLUTE RULES:
✅ BE CONSISTENT with known players (most important!)
✅ Remove only tiny micro-text clan tags (TTV, dvs, etc.)
✅ Keep all normal-sized letters and numbers
✅ When in doubt, preserve more rather than less

❌ NEVER create new variations of known players
❌ NEVER add decorations to existing names
❌ NEVER change spelling of known players

CONSISTENCY EXAMPLES:
- Image shows "2AM DIBBS" + "dibbs" is known → return "dibbs"
- Image shows "NVFJJ" + "jj" is known → return "jj"
- Image shows "DOBy" + "dob" is known → return "dob"
- Image shows "SKELETO" + "skeleto" is known → return "skeleto"

YOUR JOB: Maximize consistency with existing leaderboard data.
RESULT: Same players always get same usernames across all screenshots.

Extract ALL players. Convert stats to integers. Use 0 if not visible.
"""

    def process_image(self, image_path: str, existing_players: List[str] = None) -> Optional[Dict]:
        """Process a single image and extract scorecard data with existing player context."""
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
            
            # Create prompt with existing players context
            prompt = self._create_extraction_prompt(existing_players)
            
            # Generate response
            print(f"🔄 Processing {os.path.basename(image_path)}...")
            if existing_players:
                print(f"📋 Using context of {len(existing_players)} known players for consistency")
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
    
    def _get_existing_players(self) -> List[str]:
        """Get existing players from Google Sheets for AI context."""
        if not self.sheets_client or not self.sheet_id:
            return []
        
        try:
            sheet = self.sheets_client.open_by_key(self.sheet_id)
            worksheet = sheet.worksheet(self.worksheet_name)
            
            # Get all records and extract usernames
            all_records = worksheet.get_all_records()
            players = []
            
            for record in all_records:
                username = record.get('username', '').strip()
                if username and username.lower() not in ['username', 'player']:
                    players.append(username)
            
            # Sort by games played (descending) to prioritize active players
            try:
                players_with_games = []
                for record in all_records:
                    username = record.get('username', '').strip()
                    games = int(record.get('games_played', 0))
                    if username and username.lower() not in ['username', 'player']:
                        players_with_games.append((username, games))
                
                # Sort by games played, then alphabetically
                players_with_games.sort(key=lambda x: (-x[1], x[0]))
                players = [p[0] for p in players_with_games]
            except:
                # Fallback to alphabetical sort if games_played parsing fails
                players.sort()
            
            print(f"📊 Found {len(players)} existing players for AI context")
            return players[:100]  # Limit to top 100 to keep prompt manageable
            
        except Exception as e:
            print(f"⚠️ Could not load existing players: {e}")
            return []
    
    def process_images_with_context(self, image_paths: List[str]) -> List[Dict]:
        """Process images with existing player context for maximum consistency."""
        # Get existing players for AI context
        existing_players = self._get_existing_players()
        
        if existing_players:
            print(f"🎯 AI will use {len(existing_players)} known players for consistency")
            print(f"📋 Top known players: {', '.join(existing_players[:10])}...")
        else:
            print("🆕 No existing players found - processing as new leaderboard")
        
        all_results = []
        
        for image_path in image_paths:
            result = self.process_image(image_path, existing_players)
            if result:
                all_results.append(result)
        
        return all_results
    
    def process_batch(self, image_paths: List[str]) -> List[Dict]:
        """Process multiple images (legacy method - now uses context for consistency)."""
        return self.process_images_with_context(image_paths)
    
    def export_to_csv(self, results: List[Dict], output_file: str = None) -> str:
        """Export aggregated results to CSV with improved duplicate detection."""
        if not results:
            print("❌ No results to export")
            return None
        
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"fortnite_stats_{timestamp}.csv"
        
        def normalize_username(username: str) -> str:
            """Balanced normalization - handles client patterns while preserving legitimate names."""
            import re
            
            if not username or not username.strip():
                return ""
            
            original = username.strip()
            
            # Handle anonymous/placeholder names
            if any(word in original.lower() for word in ['anonymous', 'player', 'newplayer']):
                return 'player'
            
            # Convert to lowercase and remove all special characters, keep only letters
            normalized = re.sub(r'[^a-zA-Z]', '', original).lower()
            
            # SPECIFIC FIXES for client's known problem patterns (hardcoded for accuracy)
            specific_fixes = {
                'amdibbs': 'dibbs',      # 2AMDIBBS → dibbs
                'nvfjj': 'jj',           # NVFJJ7 → jj 
                'doby': 'dob',           # DOBy → dob
                'zquintin': 'quintin',   # ZQUINTIN → quintin
                'quintin': 'quintin',    # QUINTIN → quintin (fix removal of Q)
                'skittle': 'skitle',     # SKITTLE6 → skitle
                'skeletos': 'skeleto',   # SKELETOS → skeleto
                'amdarkcel': 'darkcely', # 2AM DARKCELY → darkcely
                'amdarkcely': 'darkcely', # 2AM DARKCELY → darkcely
                'darkcel': 'darkcely',   # DARKCELY → darkcely
                'darkcely': 'darkcely',  # DARKCELY → darkcely (preserve full)
                'scamo': 'camo',         # SCAMO → camo
                'legendx': 'legend',     # XLEGENDX → legend
                'herox': 'hero',         # HEROX → hero
            }
            
            # Check specific fixes first
            if normalized in specific_fixes:
                return specific_fixes[normalized]
            
            # Handle OCR errors
            ocr_replacements = {'0': 'o', '1': 'i', '5': 's', '3': 'e', '7': 't', '8': 'b', '6': 'g'}
            for digit, letter in ocr_replacements.items():
                normalized = normalized.replace(digit, letter)
            
            # Remove repeated letters (OCR errors) - only 4+ repetitions
            normalized = re.sub(r'(.)\1{3,}', r'\1', normalized)
            
            # CONSERVATIVE prefix removal - only obvious gaming tags
            gaming_prefixes = [
                'ttv', 'twitch', 'yt', 'youtube', 'stream', 'live', 'tv',
                'dvs', 'ktk', 'gvg', 'zmr', 'faze', 'tsm', 'nrg', 'og', 'clan',
                'reign', 'team', 'guild', 'squad', 'crew', 'pro', 'esports'
            ]
            
            # Only remove if result is meaningful (4+ chars)
            for prefix in gaming_prefixes:
                if normalized.startswith(prefix) and len(normalized) > len(prefix):
                    potential = normalized[len(prefix):]
                    if len(potential) >= 4:
                        normalized = potential
                        break
            
            # CONSERVATIVE suffix removal
            gaming_suffixes = [
                'ttv', 'twitch', 'yt', 'youtube', 'stream', 'tv', 'live',
                'pro', 'gaming', 'game', 'player', 'god', 'king', 'queen',
                'win', 'wins', 'best', 'top', 'og', 'official'
            ]
            
            for suffix in gaming_suffixes:
                if normalized.endswith(suffix) and len(normalized) > len(suffix):
                    potential = normalized[:-len(suffix)]
                    if len(potential) >= 4:
                        normalized = potential
                        break
            
            # Handle xX wrapper patterns
            if len(normalized) > 6 and normalized.startswith('xx') and normalized.endswith('xx'):
                potential = normalized[2:-2]
                if len(potential) >= 3:
                    normalized = potential
            
            # TARGETED pattern fixes for number+letter combos (2AM, 3KT, etc.)
            if len(normalized) > 6:
                # Handle "2AM..." "3AM..." "4KT..." patterns
                if re.match(r'^[0-9]am', normalized):
                    potential = normalized[3:]  # Remove "2am"
                    if len(potential) >= 4:
                        normalized = potential
                elif re.match(r'^[0-9]kt', normalized):
                    potential = normalized[3:]  # Remove "4kt"
                    if len(potential) >= 4:
                        normalized = potential
            
            # TARGETED short prefix removal (NVF, GVG, ZMR) - only if followed by 4+ chars
            if len(normalized) > 6:
                short_prefixes = ['nvf', 'gvg', 'zmr']
                for prefix in short_prefixes:
                    if normalized.startswith(prefix):
                        potential = normalized[len(prefix):]
                        if len(potential) >= 4:
                            normalized = potential
                            break
            
            # CAREFUL single letter prefix removal - only for obvious cases
            if len(normalized) > 5:
                # Only remove single letters if result looks like a real name
                single_letters = ['z', 'x', 'q', 'b', 'c', 's']
                for letter in single_letters:
                    if normalized.startswith(letter):
                        potential = normalized[1:]
                        # Only if result starts with vowel or common consonant
                        if len(potential) >= 4 and potential[0] in 'aeioudhmnprstl':
                            normalized = potential
                            break
            
            # Handle trailing Y and Z - common suffixes
            if len(normalized) > 4:
                if normalized.endswith('y') or normalized.endswith('z'):
                    potential = normalized[:-1]
                    if len(potential) >= 3:
                        normalized = potential
            
            # Final safety check
            if len(normalized) < 2:
                cleaned = re.sub(r'[^a-zA-Z]', '', original).lower()
                if len(cleaned) >= 2:
                    normalized = cleaned
                else:
                    normalized = original.lower()
            
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
        if not self.sheets_client:
            print("❌ Google Sheets client not configured - check credentials.json")
            return False
        
        if not self.sheet_id or self.sheet_id == 'your_google_sheet_id_here':
            print("❌ Google Sheet ID not set in .env file")
            print("💡 Get your Sheet ID from the URL: https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit")
            return False
        
        try:
            print(f"🔍 Attempting to open Google Sheet: {self.sheet_id}")
            # Open the worksheet
            sheet = self.sheets_client.open_by_key(self.sheet_id)
            print(f"✅ Sheet opened successfully: {sheet.title}")
            
            print(f"🔍 Looking for worksheet: {self.worksheet_name}")
            worksheet = sheet.worksheet(self.worksheet_name)
            print(f"✅ Worksheet found: {self.worksheet_name}")
            
        except Exception as sheet_error:
            print(f"❌ Error accessing Google Sheet: {sheet_error}")
            if "404" in str(sheet_error):
                print("💡 404 Error - This usually means:")
                print("   1. Wrong Google Sheet ID in .env file")
                print("   2. Sheet not shared with service account email")
                if self.service_account_email:
                    print(f"   📧 Your service account: {self.service_account_email}")
                    print("   👆 Make sure to share your Google Sheet with this email!")
            elif "403" in str(sheet_error):
                print("💡 403 Error - Permission denied:")
                print("   1. Share your Google Sheet with the service account")
                print("   2. Give 'Editor' permissions")
                if self.service_account_email:
                    print(f"   📧 Service account: {self.service_account_email}")
            return False
        
        try:
            # Normalize usernames function for duplicate detection
            def normalize_username(username: str) -> str:
                """Balanced normalization - handles client patterns while preserving legitimate names."""
                import re
                
                if not username or not username.strip():
                    return ""
                
                original = username.strip()
                
                # Handle anonymous/placeholder names
                if any(word in original.lower() for word in ['anonymous', 'player', 'newplayer']):
                    return 'player'
                
                # Convert to lowercase and remove all special characters, keep only letters
                normalized = re.sub(r'[^a-zA-Z]', '', original).lower()
                
                # SPECIFIC FIXES for client's known problem patterns (hardcoded for accuracy)
                specific_fixes = {
                    'amdibbs': 'dibbs',      # 2AMDIBBS → dibbs
                    'nvfjj': 'jj',           # NVFJJ7 → jj 
                    'doby': 'dob',           # DOBy → dob
                    'zquintin': 'quintin',   # ZQUINTIN → quintin
                    'quintin': 'quintin',    # QUINTIN → quintin (fix removal of Q)
                    'skittle': 'skitle',     # SKITTLE6 → skitle
                    'skeletos': 'skeleto',   # SKELETOS → skeleto
                    'amdarkcel': 'darkcely', # 2AM DARKCELY → darkcely
                    'amdarkcely': 'darkcely', # 2AM DARKCELY → darkcely
                    'darkcel': 'darkcely',   # DARKCELY → darkcely
                    'darkcely': 'darkcely',  # DARKCELY → darkcely (preserve full)
                    'scamo': 'camo',         # SCAMO → camo
                    'legendx': 'legend',     # XLEGENDX → legend
                    'herox': 'hero',         # HEROX → hero
                }
                
                # Check specific fixes first
                if normalized in specific_fixes:
                    return specific_fixes[normalized]
                
                # Handle OCR errors
                ocr_replacements = {'0': 'o', '1': 'i', '5': 's', '3': 'e', '7': 't', '8': 'b', '6': 'g'}
                for digit, letter in ocr_replacements.items():
                    normalized = normalized.replace(digit, letter)
                
                # Remove repeated letters (OCR errors) - only 4+ repetitions
                normalized = re.sub(r'(.)\1{3,}', r'\1', normalized)
                
                # CONSERVATIVE prefix removal - only obvious gaming tags
                gaming_prefixes = [
                    'ttv', 'twitch', 'yt', 'youtube', 'stream', 'live', 'tv',
                    'dvs', 'ktk', 'gvg', 'zmr', 'faze', 'tsm', 'nrg', 'og', 'clan',
                    'reign', 'team', 'guild', 'squad', 'crew', 'pro', 'esports'
                ]
                
                # Only remove if result is meaningful (4+ chars)
                for prefix in gaming_prefixes:
                    if normalized.startswith(prefix) and len(normalized) > len(prefix):
                        potential = normalized[len(prefix):]
                        if len(potential) >= 4:
                            normalized = potential
                            break
                
                # CONSERVATIVE suffix removal
                gaming_suffixes = [
                    'ttv', 'twitch', 'yt', 'youtube', 'stream', 'tv', 'live',
                    'pro', 'gaming', 'game', 'player', 'god', 'king', 'queen',
                    'win', 'wins', 'best', 'top', 'og', 'official'
                ]
                
                for suffix in gaming_suffixes:
                    if normalized.endswith(suffix) and len(normalized) > len(suffix):
                        potential = normalized[:-len(suffix)]
                        if len(potential) >= 4:
                            normalized = potential
                            break
                
                # Handle xX wrapper patterns
                if len(normalized) > 6 and normalized.startswith('xx') and normalized.endswith('xx'):
                    potential = normalized[2:-2]
                    if len(potential) >= 3:
                        normalized = potential
                
                # TARGETED pattern fixes for number+letter combos (2AM, 3KT, etc.)
                if len(normalized) > 6:
                    # Handle "2AM..." "3AM..." "4KT..." patterns
                    if re.match(r'^[0-9]am', normalized):
                        potential = normalized[3:]  # Remove "2am"
                        if len(potential) >= 4:
                            normalized = potential
                    elif re.match(r'^[0-9]kt', normalized):
                        potential = normalized[3:]  # Remove "4kt"
                        if len(potential) >= 4:
                            normalized = potential
                
                # TARGETED short prefix removal (NVF, GVG, ZMR) - only if followed by 4+ chars
                if len(normalized) > 6:
                    short_prefixes = ['nvf', 'gvg', 'zmr']
                    for prefix in short_prefixes:
                        if normalized.startswith(prefix):
                            potential = normalized[len(prefix):]
                            if len(potential) >= 4:
                                normalized = potential
                                break
                
                # CAREFUL single letter prefix removal - only for obvious cases
                if len(normalized) > 5:
                    # Only remove single letters if result looks like a real name
                    single_letters = ['z', 'x', 'q', 'b', 'c', 's']
                    for letter in single_letters:
                        if normalized.startswith(letter):
                            potential = normalized[1:]
                            # Only if result starts with vowel or common consonant
                            if len(potential) >= 4 and potential[0] in 'aeioudhmnprstl':
                                normalized = potential
                                break
                
                # Handle trailing Y and Z - common suffixes
                if len(normalized) > 4:
                    if normalized.endswith('y') or normalized.endswith('z'):
                        potential = normalized[:-1]
                        if len(potential) >= 3:
                            normalized = potential
                
                # Final safety check
                if len(normalized) < 2:
                    cleaned = re.sub(r'[^a-zA-Z]', '', original).lower()
                    if len(cleaned) >= 2:
                        normalized = cleaned
                    else:
                        normalized = original.lower()
                
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
            
            # Add rows efficiently using batch operations to avoid rate limits
            import time
            batch_size = 100
            
            for i in range(0, len(rows_to_add), batch_size):
                batch = rows_to_add[i:i+batch_size]
                # Use append_rows (plural) for efficient batch operation - single API call
                worksheet.append_rows(batch, value_input_option='USER_ENTERED')
                print(f"📊 Added batch {i//batch_size + 1}/{(len(rows_to_add)-1)//batch_size + 1}")
                
                # Add small delay between batches for rate limit safety
                if i + batch_size < len(rows_to_add):  # Don't delay after last batch
                    time.sleep(1)
            
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

    def diagnose_google_sheets_setup(self) -> bool:
        """Diagnostic function to check Google Sheets configuration."""
        print("🔍 Google Sheets Setup Diagnostic")
        print("=" * 40)
        
        # Check credentials
        if self.sheets_credentials_data:
            print("✅ Using Streamlit Cloud secrets for credentials")
        elif self.sheets_credentials_file:
            if not os.path.exists(self.sheets_credentials_file):
                print(f"❌ Credentials file not found: {self.sheets_credentials_file}")
                return False
            print(f"✅ Credentials file found: {self.sheets_credentials_file}")
        else:
            print("❌ No credentials configured (neither secrets nor file)")
            return False
        
        # Check service account email
        if self.service_account_email:
            print(f"✅ Service account email: {self.service_account_email}")
            print("👆 Make sure your Google Sheet is shared with this email!")
        else:
            print("❌ Could not read service account email from credentials")
        
        # Check sheet ID
        if not self.sheet_id or self.sheet_id == 'your_google_sheet_id_here':
            print("❌ GOOGLE_SHEET_ID not properly set in .env")
            print("💡 Extract it from your sheet URL:")
            print("   https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit")
            return False
        
        print(f"✅ Sheet ID configured: {self.sheet_id}")
        
        # Check Google Sheets client
        if not self.sheets_client:
            print("❌ Google Sheets client failed to initialize")
            return False
        
        print("✅ Google Sheets client initialized")
        
        # Try to access the sheet
        try:
            print(f"🔄 Testing access to sheet...")
            sheet = self.sheets_client.open_by_key(self.sheet_id)
            print(f"✅ Successfully accessed sheet: {sheet.title}")
            
            # Try to access the worksheet
            worksheet = sheet.worksheet(self.worksheet_name)
            print(f"✅ Successfully accessed worksheet: {self.worksheet_name}")
            
            print("🎉 Google Sheets setup is working correctly!")
            return True
            
        except Exception as e:
            print(f"❌ Error accessing sheet: {e}")
            if "404" in str(e):
                print("💡 404 means either wrong Sheet ID or not shared with service account")
            elif "403" in str(e):
                print("💡 403 means no permission - share sheet with service account email")
            return False

# Example usage
if __name__ == "__main__":
    processor = FortniteScoreboardProcessor()
    
    # Process images from a folder
    import glob
    image_files = glob.glob("screenshots/*.png") + glob.glob("screenshots/*.jpg")
    
    if image_files:
        print(f"Found {len(image_files)} images to process...")
        print("🎯 Using AI-first consistency approach with existing player context")
        results = processor.process_images_with_context(image_files)
        
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
