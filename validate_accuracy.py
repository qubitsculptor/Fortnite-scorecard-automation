#!/usr/bin/env python3
"""
Accuracy validation script for Fortnite scorecard processing.
Compares extracted data against manual verification.
"""

import json
from fortnite_processor import FortniteScoreboardProcessor

def validate_extraction(image_path: str, expected_players: int = None):
    """Test extraction accuracy for a specific image."""
    processor = FortniteScoreboardProcessor()
    result = processor.process_image(image_path)
    
    if not result:
        print(f"❌ Failed to process {image_path}")
        return False
    
    players = result.get('players', [])
    print(f"📊 Processing Results for {image_path}:")
    print(f"   Players extracted: {len(players)}")
    
    if expected_players and len(players) != expected_players:
        print(f"⚠️  Expected {expected_players} players, got {len(players)}")
    
    # Check for reasonable stats
    issues = []
    for player in players:
        username = player.get('username', 'Unknown')
        eliminations = player.get('eliminations', 0)
        deaths = player.get('deaths', 0)
        damage = player.get('damage', 0)
        
        # Sanity checks
        if eliminations > 50:
            issues.append(f"{username}: Eliminations too high ({eliminations})")
        if damage > 10000:
            issues.append(f"{username}: Damage too high ({damage})")
        if not player.get('team') in ['ATK', 'DEF']:
            issues.append(f"{username}: Invalid team ({player.get('team')})")
    
    if issues:
        print("⚠️  Potential accuracy issues:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("✅ All stats look reasonable")
    
    return len(issues) == 0

if __name__ == "__main__":
    # Test with your screenshots
    test_images = [
        "screenshots/test1.png",
        "screenshots/test2.png", 
        # Add your test images here
    ]
    
    for image in test_images:
        try:
            validate_extraction(image, expected_players=16)  # Adjust expected count
            print("-" * 50)
        except FileNotFoundError:
            print(f"Image not found: {image}")
