import streamlit as st
import os
import tempfile
from fortnite_processor import FortniteScoreboardProcessor
import pandas as pd

# Page config
st.set_page_config(
    page_title="Fortnite Admin Panel",
    page_icon="🔒",
    layout="wide"
)

# Simple password protection
def check_admin_access():
    """Simple password protection for admin access."""
    def password_entered():
        if st.session_state["admin_password"] == os.getenv("ADMIN_PASSWORD", "fortnite2024"):
            st.session_state["authenticated"] = True
            del st.session_state["admin_password"]
        else:
            st.session_state["authenticated"] = False

    if "authenticated" not in st.session_state:
        st.title("🔒 Admin Access Required")
        st.text_input("Enter Admin Password", type="password", 
                     on_change=password_entered, key="admin_password")
        st.info("This admin panel is for authorized users only.")
        return False
    elif not st.session_state["authenticated"]:
        st.title("🔒 Admin Access Required")
        st.text_input("Enter Admin Password", type="password", 
                     on_change=password_entered, key="admin_password")
        st.error("❌ Incorrect password. Access denied.")
        return False
    else:
        return True

def main():
    # Check authentication first
    if not check_admin_access():
        st.stop()
    
    # Main app header
    st.title("🎮 Fortnite Leaderboard Admin Panel")
    st.subheader("Upload scorecard screenshots to automatically update your leaderboard")
    
    # Initialize processor
    processor = FortniteScoreboardProcessor()
    
    # API Status Check
    col1, col2 = st.columns(2)
    
    with col1:
        if processor.model:
            st.success("✅ AI Processing Ready")
        else:
            st.error("❌ Gemini AI Not Configured")
            st.info("Please add GEMINI_API_KEY to environment variables")
            st.stop()
    
    with col2:
        if processor.sheets_client:
            st.success("✅ Leaderboard Connected")
        else:
            st.error("❌ Google Sheets Not Connected")
            st.info("Your leaderboard won't auto-update without Google Sheets")
    
    # Logout button
    if st.sidebar.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()
    
    st.sidebar.markdown("### ℹ️ How It Works")
    st.sidebar.info("""
    1. Upload Fortnite scorecard screenshots
    2. AI extracts all player stats  
    3. System detects duplicate players
    4. Your Google Sheet updates automatically
    5. Your public leaderboard reflects changes
    """)
    
    # Upload section
    st.markdown("### 📸 Upload Scorecard Screenshots")
    
    uploaded_files = st.file_uploader(
        "Drag and drop your Fortnite Ballistic scorecard screenshots here",
        type=['png', 'jpg', 'jpeg'],
        accept_multiple_files=True,
        help="Upload multiple screenshots to automatically aggregate player stats across games"
    )
    
    if uploaded_files:
        st.info(f"📁 **{len(uploaded_files)} screenshots** ready for processing")
        
        # Show preview of uploaded files
        with st.expander("📋 View Uploaded Files"):
            for i, file in enumerate(uploaded_files, 1):
                st.write(f"{i}. {file.name} ({file.size:,} bytes)")
        
        if st.button("🚀 Process Screenshots & Update Leaderboard", type="primary", use_container_width=True):
            # Processing workflow
            temp_files = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Step 1: Save uploaded files
            with st.spinner("Preparing files for AI processing..."):
                for i, uploaded_file in enumerate(uploaded_files):
                    progress_bar.progress((i + 1) / len(uploaded_files) / 3)  # First third of progress
                    status_text.text(f"Saving {uploaded_file.name}...")
                    
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}")
                    temp_file.write(uploaded_file.getvalue())
                    temp_file.close()
                    temp_files.append(temp_file.name)
            
            # Step 2: AI Processing
            status_text.text("🤖 AI analyzing screenshots...")
            results = []
            
            for i, temp_file in enumerate(temp_files):
                progress_bar.progress((1/3) + (i + 1) / len(temp_files) / 3)  # Second third
                status_text.text(f"AI processing screenshot {i+1} of {len(temp_files)}...")
                
                result = processor.process_image(temp_file)
                if result:
                    results.append(result)
            
            # Clean up temp files
            for temp_file in temp_files:
                os.unlink(temp_file)
            
            if results:
                # Step 3: Show Results and Update Leaderboard
                progress_bar.progress(2/3)
                status_text.text("📊 Aggregating player data...")
                
                # Count total players found
                total_players = sum(len(r.get('players', [])) for r in results)
                st.success(f"🎉 **AI successfully extracted {total_players} player entries** from {len(results)} screenshots!")
                
                # Display quick preview
                with st.expander("👀 Preview Extracted Data"):
                    for i, result in enumerate(results, 1):
                        st.write(f"**Screenshot {i}**: {len(result.get('players', []))} players found")
                        for player in result.get('players', [])[:3]:  # Show first 3 players
                            st.write(f"- {player['username']}: {player['eliminations']} kills, {player['deaths']} deaths")
                        if len(result.get('players', [])) > 3:
                            st.write(f"... and {len(result.get('players', [])) - 3} more players")
                
                # Step 4: Update Leaderboard
                progress_bar.progress(1.0)
                status_text.text("🔄 Updating your leaderboard...")
                
                if processor.sheets_client:
                    with st.spinner("Uploading to your Google Sheet..."):
                        success = processor.export_to_google_sheets(results)
                    
                    if success:
                        st.success("✅ **Leaderboard updated successfully!**")
                        st.balloons()
                        st.info("🌐 Your public website will now show the updated player statistics!")
                    else:
                        st.error("❌ Failed to update Google Sheet")
                        st.warning("Creating backup CSV file instead...")
                        
                        # Provide CSV backup
                        csv_file = processor.export_to_csv(results)
                        if csv_file and os.path.exists(csv_file):
                            with open(csv_file, 'r') as f:
                                st.download_button(
                                    "📥 Download Backup CSV",
                                    f.read(),
                                    file_name=f"fortnite_backup_{len(results)}_games.csv",
                                    mime="text/csv",
                                    use_container_width=True
                                )
                else:
                    st.warning("⚠️ Google Sheets not configured - Creating CSV export instead")
                    csv_file = processor.export_to_csv(results)
                    if csv_file and os.path.exists(csv_file):
                        with open(csv_file, 'r') as f:
                            st.download_button(
                                "📥 Download Player Stats CSV",
                                f.read(),
                                file_name=f"fortnite_stats_{len(results)}_games.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
                
                # Store results in session for potential re-export
                st.session_state.last_results = results
                
            else:
                st.error("❌ No player data could be extracted from the screenshots")
                st.info("Please ensure:")
                st.write("- Images show the complete Fortnite Ballistic scorecard")
                st.write("- Screenshots are clear and not blurry")
                st.write("- Player names and stats are visible")

    # Quick actions section
    if hasattr(st.session_state, 'last_results') and st.session_state.last_results:
        st.markdown("### 🔄 Quick Actions")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Re-export to CSV", use_container_width=True):
                csv_file = processor.export_to_csv(st.session_state.last_results)
                if csv_file and os.path.exists(csv_file):
                    with open(csv_file, 'r') as f:
                        st.download_button(
                            "📥 Download Latest CSV",
                            f.read(),
                            file_name=csv_file,
                            mime="text/csv",
                            key="reexport_csv"
                        )
        
        with col2:
            if processor.sheets_client and st.button("🔄 Re-sync to Leaderboard", use_container_width=True):
                with st.spinner("Syncing to Google Sheets..."):
                    success = processor.export_to_google_sheets(st.session_state.last_results)
                if success:
                    st.success("✅ Leaderboard re-synced!")
                else:
                    st.error("❌ Sync failed")

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.8rem;">
        🔒 Secure Admin Panel | AI-powered scorecard processing | Auto-updates your leaderboard
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
