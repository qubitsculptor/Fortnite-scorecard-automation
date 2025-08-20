#!/usr/bin/env python3
"""
Simple command-line interface for the Fortnite Scorecard Processor
For users who prefer command-line over web interface
"""

import argparse
import os
import glob
from fortnite_processor import FortniteScoreboardProcessor

def main():
    parser = argparse.ArgumentParser(description='Process Fortnite Ballistic scorecard screenshots')
    parser.add_argument('images', nargs='*', help='Image files to process (or use --folder)')
    parser.add_argument('--folder', '-f', help='Process all images in a folder')
    parser.add_argument('--output', '-o', help='Output CSV filename')
    parser.add_argument('--no-sheets', action='store_true', help='Skip Google Sheets export')
    parser.add_argument('--no-duplicates', action='store_true', help='Disable duplicate detection')
    
    args = parser.parse_args()
    
    # Initialize processor
    processor = FortniteScoreboardProcessor()
    
    # Get image files
    image_files = []
    if args.folder:
        # Process folder
        patterns = ['*.png', '*.jpg', '*.jpeg', '*.PNG', '*.JPG', '*.JPEG']
        for pattern in patterns:
            image_files.extend(glob.glob(os.path.join(args.folder, pattern)))
    else:
        # Use provided files
        image_files = args.images
    
    if not image_files:
        print("❌ No image files found. Use --help for usage information.")
        return
    
    print(f"🎯 Processing {len(image_files)} images...")
    
    # Disable duplicates if requested
    if args.no_duplicates:
        processor.enable_duplicate_check = False
    
    # Process images with context (AI-first approach)
    results = processor.process_images_with_context(image_files)
    
    if not results:
        print("❌ No data extracted from images")
        return
    
    print(f"✅ Successfully processed {len(results)} images")
    
    # Export to CSV
    csv_file = processor.export_to_csv(results, args.output)
    print(f"📄 Data saved to: {csv_file}")
    
    # Export to Google Sheets (if not disabled)
    if not args.no_sheets:
        success = processor.export_to_google_sheets(results)
        if success:
            print("📊 Data exported to Google Sheets")
    
    # Show summary
    summary = processor.create_summary_stats(results)
    if summary:
        print("\n📈 Top Players:")
        sorted_players = sorted(summary.items(), key=lambda x: x[1]['kd_ratio'], reverse=True)
        for i, (username, stats) in enumerate(sorted_players[:5]):
            print(f"{i+1:2}. {username:20} K/D: {stats['kd_ratio']:5.2f} Avg Kills: {stats['avg_eliminations']:5.2f}")

if __name__ == "__main__":
    main()
