import streamlit as st
import os
import tempfile
import sys
from typing import List
from fortnite_processor import FortniteScoreboardProcessor
import pandas as pd

# Force fresh imports - no caching issues
sys.dont_write_bytecode = True
if 'fortnite_processor' in sys.modules:
    del sys.modules['fortnite_processor']

# Page config
st.set_page_config(
    page_title="Fortnite Ballistic Scorecard Processor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better mobile experience
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #FF6B35;
        margin-bottom: 2rem;
    }
    .upload-section {
        border: 2px dashed #FF6B35;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
    }
    .stats-card {
        background: #f8f9fa !important;
        border: 1px solid #dee2e6 !important;
        padding: 1rem !important;
        border-radius: 8px !important;
        margin: 0.5rem 0 !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
        color: #333 !important;
        font-size: 14px !important;
        line-height: 1.4 !important;
    }
    .stats-card strong {
        color: #2c3e50 !important;
        font-weight: bold !important;
    }
    .success-message {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Header
    st.markdown('<h1 class="main-header">Fortnite Ballistic Scorecard Processor</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #666;">Upload screenshots, extract player stats with AI, export to Google Sheets</p>', unsafe_allow_html=True)
    
    # Initialize processor fresh every time - no caching
    processor = FortniteScoreboardProcessor()
    
    # Sidebar configuration
    with st.sidebar:
        st.header("Configuration")
        
        # Force reload button
        if st.button("🔄 Force Reload", help="Clear all caches and reload"):
            # Clear session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        # API Status
        st.subheader("API Status")
        if processor.model:
            st.success("✅ Gemini AI Connected")
        else:
            st.error("❌ Gemini API Key Missing")
            st.info("Add GEMINI_API_KEY to .env file")
        
        if processor.sheets_client:
            st.success("✅ Google Sheets Connected")
        else:
            st.warning("⚠️ Google Sheets Not Connected")
            st.info("Add credentials.json and GOOGLE_SHEET_ID")
        
        # Settings
        st.subheader("Settings")
        st.info(" Advanced duplicate detection enabled")
        st.info(" Aggressive username normalization active")
        
        # Instructions
        st.subheader("Quick Setup")
        with st.expander("API Setup Instructions"):
            st.markdown("""
            **Gemini API:**
            1. Go to [Google AI Studio](https://aistudio.google.com)
            2. Create API key
            3. Add to .env file
            
            **Google Sheets:**
            1. Enable Google Sheets API
            2. Create service account
            3. Download credentials.json
            4. Share sheet with service account email
            """)
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # File upload section
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        st.subheader(" Upload Scorecard Screenshots")
        
        uploaded_files = st.file_uploader(
            "Drag and drop your Fortnite scorecard screenshots here",
            type=['png', 'jpg', 'jpeg'],
            accept_multiple_files=True,
            help="Upload one or more screenshots of Fortnite Ballistic scorecards"
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Process button
        if uploaded_files:
            st.info(f"📁 {len(uploaded_files)} images uploaded")
            
            if st.button("Process Images", type="primary", use_container_width=True):
                if not processor.model:
                    st.error("❌ Gemini API not configured. Please add your API key to .env file.")
                    return
                
                # Save uploaded files temporarily
                temp_files = []
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                with st.spinner("📝 Preparing files..."):
                    for i, uploaded_file in enumerate(uploaded_files):
                        progress_bar.progress((i + 1) / len(uploaded_files))
                        status_text.text(f"Saving {uploaded_file.name}...")
                        
                        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}")
                        temp_file.write(uploaded_file.getvalue())
                        temp_file.close()
                        temp_files.append(temp_file.name)
                
                # Process images
                status_text.text("🤖 Processing with Gemini AI...")
                progress_bar.progress(0)
                
                results = []
                for i, temp_file in enumerate(temp_files):
                    progress_bar.progress((i + 1) / len(temp_files))
                    status_text.text(f"🔍 Processing image {i+1} of {len(temp_files)}...")
                    
                    result = processor.process_image(temp_file)
                    if result:
                        results.append(result)
                
                # Clean up temp files
                for temp_file in temp_files:
                    os.unlink(temp_file)
                
                progress_bar.progress(1.0)
                status_text.text("✅ Processing complete!")
                
                if results:
                    st.session_state.results = results
                    st.session_state.processed = True
                    st.success(f"🎉 Successfully processed {len(results)} images!")
                    
                    # Show immediate aggregation info
                    total_raw_players = sum(len(r['players']) for r in results)
                    st.info(f"📊 Found {total_raw_players} player entries (before duplicate removal)")
                    
                else:
                    st.error("❌ Failed to extract data from images. Please check image quality and try again.")
        
        # Display results
        if hasattr(st.session_state, 'processed') and st.session_state.processed:
            st.subheader("📋 Aggregated Player Data")
            
            # Get aggregated data using the processor's export function
            try:
                # Create temporary CSV to get aggregated data
                temp_csv = processor.export_to_csv(st.session_state.results, 'temp_aggregated.csv')
                aggregated_df = pd.read_csv(temp_csv)
                os.unlink(temp_csv)  # Clean up
                
                st.success(f" **{len(aggregated_df)} unique players** after duplicate removal")
                
                # Display aggregated data
                st.dataframe(aggregated_df, use_container_width=True, hide_index=True)
                
            except Exception as e:
                st.error(f"Error creating aggregated view: {e}")
                
                # Fallback: show raw data
                st.warning("Showing raw data instead:")
                display_data = []
                for result in st.session_state.results:
                    match_info = result['match_info']
                    for player in result['players']:
                        display_data.append({
                            'Image': match_info.get('image_file', 'N/A'),
                            'Player': player['username'],
                            'Team': player['team'],
                            'Kills': player['eliminations'],
                            'Deaths': player['deaths'],
                            'Assists': player['assists'],
                            'Damage': player['damage'],
                            'Plants': player['plants'],
                            'Defuses': player['defuses']
                        })
                
                df = pd.DataFrame(display_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Export options
            st.subheader(" Export Data")
            col_export1, col_export2 = st.columns(2)
            
            with col_export1:
                # CSV Export
                if st.button(" Download CSV", use_container_width=True):
                    csv_file = processor.export_to_csv(st.session_state.results)
                    with open(csv_file, 'rb') as f:
                        st.download_button(
                            "Download Aggregated CSV",
                            f.read(),
                            file_name=csv_file,
                            mime='text/csv',
                            use_container_width=True
                        )
            
            with col_export2:
                # Google Sheets Export
                if st.button("📊 Export to Google Sheets", use_container_width=True):
                    if processor.sheets_client:
                        with st.spinner("Uploading to Google Sheets..."):
                            success = processor.export_to_google_sheets(st.session_state.results)
                        if success:
                            st.success("✅ Data exported to Google Sheets!")
                        else:
                            st.error("❌ Failed to export to Google Sheets")
                    else:
                        st.error("❌ Google Sheets not configured")
    
    with col2:
        # Statistics panel
        st.subheader("📈 Statistics")
        
        if hasattr(st.session_state, 'processed') and st.session_state.processed:
            # Use aggregated data for statistics
            try:
                temp_csv = processor.export_to_csv(st.session_state.results, 'temp_stats.csv')
                stats_df = pd.read_csv(temp_csv)
                os.unlink(temp_csv)
                
                if len(stats_df) > 0:
                    st.write("**🏆 Top Players (by K/D):**")
                    
                    # Sort by K/D ratio and show top 5
                    top_players = stats_df.nlargest(5, 'kd_ratio')
                    
                    for i, (idx, player) in enumerate(top_players.iterrows()):
                        with st.container():
                            st.write(f"**#{i+1} {player['username']}**")
                            col_kd, col_games = st.columns(2)
                            with col_kd:
                                st.metric("K/D Ratio", f"{player['kd_ratio']:.2f}")
                            with col_games:
                                st.metric("Games", int(player['games_played']))
                            st.write(f"Kills: {int(player['total_eliminations'])} | Damage: {int(player['total_damage']):,}")
                            if i < 4:  # Don't add divider after last item
                                st.divider()
                
            except Exception as e:
                st.error(f"Error generating statistics: {e}")
            
            # Match results summary
            total_matches = len(st.session_state.results)
            victories = sum(1 for r in st.session_state.results if r['match_info'].get('match_result') == 'VICTORY')
            
            st.write("**📊 Match Summary:**")
            col_matches, col_wins = st.columns(2)
            with col_matches:
                st.metric("Total Matches", total_matches)
            with col_wins:
                st.metric("Victories", victories)
            win_rate = (victories/total_matches*100) if total_matches > 0 else 0
            st.metric("Win Rate", f"{win_rate:.1f}%")
            
        else:
            st.info(" Upload and process images to see statistics")
        
        # Recent activity
        st.subheader(" Recent Activity")
        if hasattr(st.session_state, 'processed'):
            st.text("✅ Images processed")
            st.text("✅ Data extracted")
            st.text("✅ Duplicates merged")
            if processor.sheets_client:
                st.text("✅ Ready for export")
        else:
            st.text("⏳ Waiting for images...")

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.8rem;">
         Built with Streamlit + Gemini AI | Advanced duplicate detection active
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
