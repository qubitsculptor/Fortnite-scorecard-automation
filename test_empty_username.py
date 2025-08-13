#!/usr/bin/env python3
"""
Quick test to verify empty username filtering works correctly.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from fortnite_processor import FortniteScoreboardProcessor

def test_empty_username_filtering():
    """Test that empty usernames are properly filtered out."""
    
    # Create test data with empty usernames
    test_results = [
        {
            'match_info': {
                'timestamp': '2025-08-13 10:00:00',
                'match_result': 'VICTORY',
                'image_file': 'test1.jpg'
            },
            'players': [
                {
                    'username': 'ValidPlayer1',
                    'team': 'Team A',
                    'eliminations': 5,
                    'deaths': 2,
                    'assists': 3,
                    'damage': 1200,
                    'plants': 1,
                    'defuses': 0
                },
                {
                    'username': '',  # Empty username - should be filtered
                    'team': 'Team B',
                    'eliminations': 3,
                    'deaths': 1,
                    'assists': 2,
                    'damage': 800,
                    'plants': 0,
                    'defuses': 1
                },
                {
                    'username': '   ',  # Whitespace only - should be filtered
                    'team': 'Team C',
                    'eliminations': 4,
                    'deaths': 3,
                    'assists': 1,
                    'damage': 950,
                    'plants': 0,
                    'defuses': 0
                },
                {
                    'username': 'ValidPlayer2',
                    'team': 'Team D',
                    'eliminations': 2,
                    'deaths': 4,
                    'assists': 5,
                    'damage': 600,
                    'plants': 2,
                    'defuses': 1
                }
            ]
        }
    ]
    
    processor = FortniteScoreboardProcessor()
    
    print("🧪 Testing empty username filtering...")
    print(f"📊 Input: 4 total players (2 valid, 2 empty usernames)")
    
    # Test CSV export (should filter out empty usernames)
    print("\n🔍 Testing CSV export filtering...")
    csv_file = processor.export_to_csv(test_results, 'test_empty_usernames.csv')
    
    if csv_file:
        import pandas as pd
        df = pd.read_csv(csv_file)
        print(f"✅ CSV export created with {len(df)} players")
        print("Players in CSV:", df['username'].tolist())
        
        # Clean up
        os.unlink(csv_file)
        
        if len(df) == 2 and 'ValidPlayer1' in df['username'].values and 'ValidPlayer2' in df['username'].values:
            print("✅ CSV filtering works correctly!")
        else:
            print("❌ CSV filtering failed!")
            return False
    else:
        print("❌ CSV export failed!")
        return False
    
    print("\n🧪 Test completed successfully!")
    return True

if __name__ == "__main__":
    success = test_empty_username_filtering()
    sys.exit(0 if success else 1)
