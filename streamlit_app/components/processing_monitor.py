"""
Real-time Processing Monitor Component
Live CLI progress monitoring and real-time cost tracking
"""

import streamlit as st
import json
import time
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
import subprocess
import threading
import queue

class ProcessingMonitor:
    """Real-time processing monitor for ClipScribe operations"""
    
    def __init__(self):
        self.log_queue = queue.Queue()
        self.is_monitoring = False
        self.current_process = None
        
    def start_monitoring(self, command: str, working_dir: str = "."):
        """Start monitoring a ClipScribe CLI command"""
        if self.is_monitoring:
            return False
        
        self.is_monitoring = True
        
        # Start the command in a separate thread
        def run_command():
            try:
                process = subprocess.Popen(
                    command.split(),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    cwd=working_dir
                )
                
                self.current_process = process
                
                for line in iter(process.stdout.readline, ''):
                    if line:
                        self.log_queue.put({
                            'timestamp': datetime.now(),
                            'message': line.strip(),
                            'type': 'output'
                        })
                
                process.wait()
                self.log_queue.put({
                    'timestamp': datetime.now(),
                    'message': f"Process completed with exit code: {process.returncode}",
                    'type': 'status'
                })
                
            except Exception as e:
                self.log_queue.put({
                    'timestamp': datetime.now(),
                    'message': f"Error: {str(e)}",
                    'type': 'error'
                })
            finally:
                self.is_monitoring = False
                self.current_process = None
        
        thread = threading.Thread(target=run_command)
        thread.daemon = True
        thread.start()
        
        return True
    
    def stop_monitoring(self):
        """Stop the current monitoring process"""
        if self.current_process:
            self.current_process.terminate()
        self.is_monitoring = False
    
    def get_logs(self) -> List[Dict]:
        """Get recent log entries"""
        logs = []
        while not self.log_queue.empty():
            try:
                logs.append(self.log_queue.get_nowait())
            except queue.Empty:
                break
        return logs

def show_processing_dashboard():
    """Main real-time processing dashboard"""
    
    st.header("🔄 Real-time Processing Dashboard")
    
    # Initialize monitor in session state
    if 'processing_monitor' not in st.session_state:
        st.session_state.processing_monitor = ProcessingMonitor()
    
    monitor = st.session_state.processing_monitor
    
    # Command input section
    st.subheader("🚀 Start New Processing Job")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        # Predefined commands
        command_templates = {
            "Process Single Video": "clipscribe process",
            "Process Collection": "clipscribe process-collection",
            "Research Query": "clipscribe research",
            "Custom Command": ""
        }
        
        selected_template = st.selectbox(
            "Choose command template:",
            list(command_templates.keys())
        )
        
        if selected_template == "Custom Command":
            command = st.text_input("Enter custom command:", "clipscribe ")
        else:
            base_command = command_templates[selected_template]
            if selected_template == "Process Single Video":
                url = st.text_input("Video URL:", "")
                command = f"{base_command} '{url}'" if url else base_command
            elif selected_template == "Process Collection":
                urls = st.text_area("Video URLs (one per line):", "")
                collection_name = st.text_input("Collection name:", "")
                if urls and collection_name:
                    url_list = [f"'{url.strip()}'" for url in urls.split('\n') if url.strip()]
                    command = f"{base_command} {' '.join(url_list)} --collection-name '{collection_name}'"
                else:
                    command = base_command
            elif selected_template == "Research Query":
                query = st.text_input("Search query:", "")
                count = st.number_input("Number of videos:", 1, 20, 5)
                command = f"{base_command} '{query}' --count {count}" if query else base_command
    
    with col2:
        st.markdown("### Status")
        if monitor.is_monitoring:
            st.success("🟢 Running")
            if st.button("🛑 Stop Process"):
                monitor.stop_monitoring()
                st.rerun()
        else:
            st.info("⚪ Idle")
            if st.button("▶️ Start Process"):
                if command.strip():
                    success = monitor.start_monitoring(command)
                    if success:
                        st.success("Process started!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Already monitoring a process")
                else:
                    st.error("Please enter a command")
    
    with col3:
        st.markdown("### Auto-refresh")
        auto_refresh = st.checkbox("Auto-refresh (5s)", value=True)
        if auto_refresh and monitor.is_monitoring:
            time.sleep(5)
            st.rerun()
    
    # Live logs section
    st.subheader("📜 Live Process Logs")
    
    # Get recent logs
    logs = monitor.get_logs()
    
    # Store logs in session state for persistence
    if 'processing_logs' not in st.session_state:
        st.session_state.processing_logs = []
    
    st.session_state.processing_logs.extend(logs)
    
    # Keep only last 100 log entries
    st.session_state.processing_logs = st.session_state.processing_logs[-100:]
    
    # Display logs
    if st.session_state.processing_logs:
        log_container = st.container()
        
        with log_container:
            # Create log DataFrame for better display
            log_data = []
            for log in st.session_state.processing_logs[-50:]:  # Show last 50
                log_data.append({
                    'Time': log['timestamp'].strftime('%H:%M:%S'),
                    'Type': log['type'],
                    'Message': log['message']
                })
            
            if log_data:
                log_df = pd.DataFrame(log_data)
                
                # Color code by type
                def highlight_type(row):
                    if row['Type'] == 'error':
                        return ['background-color: #ffebee'] * len(row)
                    elif row['Type'] == 'status':
                        return ['background-color: #e8f5e8'] * len(row)
                    else:
                        return [''] * len(row)
                
                styled_df = log_df.style.apply(highlight_type, axis=1)
                st.dataframe(styled_df, use_container_width=True, height=300)
    else:
        st.info("No logs yet. Start a process to see live output.")
    
    # Clear logs button
    if st.button("🗑️ Clear Logs"):
        st.session_state.processing_logs = []
        st.rerun()

def show_processing_queue():
    """Show processing queue and job history"""
    
    st.subheader("📋 Processing Queue & History")
    
    # Check for recent processing jobs
    output_path = Path("output")
    recent_jobs = []
    
    if output_path.exists():
        # Check individual videos
        for item in output_path.iterdir():
            if item.is_dir() and item.name != "collections":
                manifest_file = item / "manifest.json"
                if manifest_file.exists():
                    try:
                        with open(manifest_file, 'r') as f:
                            manifest = json.load(f)
                        
                        recent_jobs.append({
                            'name': item.name,
                            'type': 'Single Video',
                            'date': manifest.get('processing_date', 'Unknown'),
                            'cost': manifest.get('processing_cost', 0),
                            'status': 'Completed',
                            'path': str(item)
                        })
                    except:
                        continue
        
        # Check collections
        collections_path = output_path / "collections"
        if collections_path.exists():
            for item in collections_path.iterdir():
                if item.is_dir():
                    manifest_file = item / "manifest.json"
                    if manifest_file.exists():
                        try:
                            with open(manifest_file, 'r') as f:
                                manifest = json.load(f)
                            
                            recent_jobs.append({
                                'name': item.name,
                                'type': 'Collection',
                                'date': manifest.get('processing_date', 'Unknown'),
                                'cost': manifest.get('processing_cost', 0),
                                'status': 'Completed',
                                'path': str(item)
                            })
                        except:
                            continue
    
    # Sort by date
    recent_jobs.sort(key=lambda x: x['date'], reverse=True)
    
    # Display job history
    if recent_jobs:
        st.markdown("### Recent Jobs")
        
        for job in recent_jobs[:10]:  # Show last 10
            with st.expander(f"{job['name']} - {job['type']}", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Type:** {job['type']}")
                    st.write(f"**Date:** {job['date']}")
                
                with col2:
                    st.write(f"**Cost:** ${job['cost']:.2f}")
                    st.write(f"**Status:** {job['status']}")
                
                with col3:
                    if st.button(f"📁 Open Folder", key=f"open_{job['name']}"):
                        st.code(f"Folder: {job['path']}")
    else:
        st.info("No recent processing jobs found.")

def show_cost_tracker():
    """Real-time cost tracking visualization"""
    
    st.subheader("💰 Real-time Cost Tracking")
    
    # Load cost data
    output_path = Path("output")
    cost_data = []
    
    if output_path.exists():
        # Collect cost data from all processing
        for item in output_path.rglob("manifest.json"):
            try:
                with open(item, 'r') as f:
                    manifest = json.load(f)
                
                cost_data.append({
                    'date': manifest.get('processing_date', ''),
                    'cost': manifest.get('processing_cost', 0),
                    'name': item.parent.name,
                    'type': 'Collection' if 'collections' in str(item) else 'Single'
                })
            except:
                continue
    
    if cost_data:
        # Convert to DataFrame
        df = pd.DataFrame(cost_data)
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date']).sort_values('date')
        
        if not df.empty:
            # Calculate running total
            df['cumulative_cost'] = df['cost'].cumsum()
            
            # Cost over time
            fig_cost = go.Figure()
            
            fig_cost.add_trace(go.Scatter(
                x=df['date'],
                y=df['cumulative_cost'],
                mode='lines+markers',
                name='Cumulative Cost',
                line=dict(color='blue', width=3),
                marker=dict(size=8),
                fill='tozeroy',
                fillcolor='rgba(0,100,200,0.1)'
            ))
            
            fig_cost.update_layout(
                title="Cumulative Cost Over Time",
                xaxis_title="Date",
                yaxis_title="Total Cost ($)",
                height=400
            )
            
            st.plotly_chart(fig_cost, use_container_width=True)
            
            # Cost summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Spent", f"${df['cost'].sum():.2f}")
            
            with col2:
                avg_cost = df['cost'].mean()
                st.metric("Average Job Cost", f"${avg_cost:.2f}")
            
            with col3:
                # Daily spend rate
                if len(df) > 1:
                    days_span = (df['date'].max() - df['date'].min()).days + 1
                    daily_rate = df['cost'].sum() / days_span
                    st.metric("Daily Rate", f"${daily_rate:.2f}")
                else:
                    st.metric("Daily Rate", "$0.00")
            
            with col4:
                # Projected monthly
                if len(df) > 1:
                    days_span = (df['date'].max() - df['date'].min()).days + 1
                    daily_rate = df['cost'].sum() / days_span
                    monthly_projection = daily_rate * 30
                    st.metric("Monthly Projection", f"${monthly_projection:.2f}")
                else:
                    st.metric("Monthly Projection", "$0.00")
    else:
        st.info("No cost data available yet.")

def main():
    """Main processing monitor page"""
    
    # Main tabs
    tab1, tab2, tab3 = st.tabs([
        "🔄 Live Processing",
        "📋 Job Queue", 
        "💰 Cost Tracker"
    ])
    
    with tab1:
        show_processing_dashboard()
    
    with tab2:
        show_processing_queue()
    
    with tab3:
        show_cost_tracker()

if __name__ == "__main__":
    main() 