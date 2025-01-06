import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import random

# Page configuration
st.set_page_config(
    page_title="Track Monitoring System",
    page_icon="🚇",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session states
if 'monitoring_data' not in st.session_state:
    st.session_state.monitoring_data = {
        'acoustic': [],
        'vibration': [],
        'temperature': [],
        'humidity': [],
        'timestamps': []
    }
if 'monitoring_active' not in st.session_state:
    st.session_state.monitoring_active = False
if 'reports' not in st.session_state:
    st.session_state.reports = []
if 'alerts' not in st.session_state:
    st.session_state.alerts = []

# Constants
STATIONS = {
    "Blue Line": ["Dwarka", "Rajiv Chowk", "Noida City Centre"],
    "Yellow Line": ["Samaypur Badli", "Kashmere Gate", "HUDA City Centre"],
    "Red Line": ["Rithala", "Kashmere Gate", "Dilshad Garden"],
}

THRESHOLDS = {
    'acoustic': {'warning': 65, 'danger': 75, 'unit': 'dB', 'min': 40, 'max': 90},
    'vibration': {'warning': 0.5, 'danger': 0.7, 'unit': 'g', 'min': 0, 'max': 1},
    'temperature': {'warning': 28, 'danger': 30, 'unit': '°C', 'min': 20, 'max': 35},
    'humidity': {'warning': 65, 'danger': 75, 'unit': '%', 'min': 30, 'max': 90}
}

# Styling
st.markdown("""
<style>
    .metric-card {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    .status-good { color: #10B981; }
    .status-warning { color: #F59E0B; }
    .status-danger { color: #EF4444; }
    .metric-value { font-size: 1.5rem; font-weight: bold; }
    .metric-label { font-size: 1rem; color: #6B7280; }
    .alert-card {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Utility functions
def generate_sensor_data():
    return {
        'acoustic': random.uniform(THRESHOLDS['acoustic']['min'], THRESHOLDS['acoustic']['max']),
        'vibration': random.uniform(THRESHOLDS['vibration']['min'], THRESHOLDS['vibration']['max']),
        'temperature': random.uniform(THRESHOLDS['temperature']['min'], THRESHOLDS['temperature']['max']),
        'humidity': random.uniform(THRESHOLDS['humidity']['min'], THRESHOLDS['humidity']['max'])
    }

def calculate_health_score(data):
    weights = {'acoustic': 0.3, 'vibration': 0.3, 'temperature': 0.2, 'humidity': 0.2}
    normalized_values = {
        'acoustic': 1 - (data['acoustic'] - THRESHOLDS['acoustic']['min']) / 
                   (THRESHOLDS['acoustic']['max'] - THRESHOLDS['acoustic']['min']),
        'vibration': 1 - data['vibration'],
        'temperature': 1 - abs(data['temperature'] - 25) / 15,
        'humidity': 1 - abs(data['humidity'] - 60) / 40
    }
    return sum(normalized_values[key] * weights[key] for key in weights) * 100

def get_status_color(value, metric):
    if value >= THRESHOLDS[metric]['danger']:
        return 'danger'
    elif value >= THRESHOLDS[metric]['warning']:
        return 'warning'
    return 'good'

def update_monitoring_data():
    current_time = datetime.now()
    new_data = generate_sensor_data()
    
    max_points = 100
    for metric in new_data:
        st.session_state.monitoring_data[metric].append(new_data[metric])
        if len(st.session_state.monitoring_data[metric]) > max_points:
            st.session_state.monitoring_data[metric] = st.session_state.monitoring_data[metric][-max_points:]
    
    st.session_state.monitoring_data['timestamps'].append(current_time)
    if len(st.session_state.monitoring_data['timestamps']) > max_points:
        st.session_state.monitoring_data['timestamps'] = st.session_state.monitoring_data['timestamps'][-max_points:]

    # Generate alerts based on thresholds
    for metric, value in new_data.items():
        if value >= THRESHOLDS[metric]['danger']:
            st.session_state.alerts.insert(0, {
                'time': current_time,
                'type': 'CRITICAL',
                'message': f'High {metric} level detected: {value:.1f} {THRESHOLDS[metric]["unit"]}'
            })
        elif value >= THRESHOLDS[metric]['warning']:
            st.session_state.alerts.insert(0, {
                'time': current_time,
                'type': 'WARNING',
                'message': f'Elevated {metric} level: {value:.1f} {THRESHOLDS[metric]["unit"]}'
            })

# Sidebar
with st.sidebar:
    st.title("Track Monitor Controls")
    
    selected_line = st.selectbox("Metro Line", list(STATIONS.keys()))
    selected_station = st.selectbox("Station", STATIONS[selected_line])
    
    st.divider()
    
    monitoring_toggle = st.toggle("Active Monitoring", value=st.session_state.monitoring_active)
    if monitoring_toggle != st.session_state.monitoring_active:
        st.session_state.monitoring_active = monitoring_toggle
        if monitoring_toggle:
            st.success("Monitoring activated")
        else:
            st.warning("Monitoring paused")
    
    update_interval = st.slider("Update Interval (seconds)", 1, 10, 1)
    
    if st.button("Clear Data"):
        for key in st.session_state.monitoring_data:
            st.session_state.monitoring_data[key] = []
        st.success("Data cleared")

# Main content
st.title("Track Health Monitoring Dashboard")
st.markdown(f"*Currently Monitoring:* {selected_line} - {selected_station}")

# Create tabs
tabs = st.tabs([
    "📊 Overview",
    "📈 Real-time Monitoring",
    "📝 Reports & Analysis",
    "⚠ Alerts"
])

# Overview Tab
with tabs[0]:
    if st.session_state.monitoring_data['acoustic']:
        latest_data = {
            metric: st.session_state.monitoring_data[metric][-1]
            for metric in ['acoustic', 'vibration', 'temperature', 'humidity']
        }
        health_score = calculate_health_score(latest_data)
        
        # Display health score with gauge
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=health_score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Track Health Score"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 60], 'color': "lightpink"},
                    {'range': [60, 80], 'color': "lightyellow"},
                    {'range': [80, 100], 'color': "lightgreen"}
                ]
            }
        ))
        st.plotly_chart(fig, use_container_width=True)
        
        # Metrics display
        cols = st.columns(4)
        metrics = ['acoustic', 'vibration', 'temperature', 'humidity']
        for col, metric in zip(cols, metrics):
            with col:
                status = get_status_color(latest_data[metric], metric)
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">{metric.title()}</div>
                    <div class="metric-value status-{status}">
                        {latest_data[metric]:.1f} {THRESHOLDS[metric]['unit']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Waiting for monitoring data...")

# Real-time Monitoring Tab
with tabs[1]:
    if st.session_state.monitoring_data['timestamps']:
        st.subheader("Sensor Data Visualization")
        
        # Allow user to select metrics to display
        selected_metrics = st.multiselect(
            "Select metrics to display",
            ['acoustic', 'vibration', 'temperature', 'humidity'],
            default=['acoustic']
        )
        
        # Create multi-line chart
        fig = go.Figure()
        for metric in selected_metrics:
            fig.add_trace(go.Scatter(
                x=st.session_state.monitoring_data['timestamps'],
                y=st.session_state.monitoring_data[metric],
                name=metric.title(),
                mode='lines'
            ))
            
            # Add threshold lines
            fig.add_hline(
                y=THRESHOLDS[metric]['warning'],
                line_dash="dash",
                line_color="orange",
                annotation_text=f"{metric.title()} Warning"
            )
            fig.add_hline(
                y=THRESHOLDS[metric]['danger'],
                line_dash="dash",
                line_color="red",
                annotation_text=f"{metric.title()} Danger"
            )
        
        fig.update_layout(
            height=500,
            title="Real-time Sensor Data",
            xaxis_title="Time",
            yaxis_title="Value"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Waiting for monitoring data...")

# Reports & Analysis Tab
with tabs[2]:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Create Report")
        with st.form("report_form"):
            report_type = st.selectbox(
                "Report Type",
                ["Inspection", "Incident", "Maintenance", "Other"]
            )
            report_title = st.text_input("Report Title")
            report_description = st.text_area("Description")
            report_priority = st.select_slider(
                "Priority",
                options=["Low", "Medium", "High", "Critical"]
            )
            
            if st.form_submit_button("Submit Report"):
                st.session_state.reports.append({
                    'type': report_type,
                    'title': report_title,
                    'description': report_description,
                    'priority': report_priority,
                    'time': datetime.now()
                })
                st.success("Report submitted successfully!")
    
    with col2:
        st.subheader("Recent Reports")
        for report in st.session_state.reports[::-1]:
            with st.expander(f"{report['title']} ({report['time'].strftime('%Y-%m-%d %H:%M')})"):
                st.write(f"*Type:* {report['type']}")
                st.write(f"*Priority:* {report['priority']}")
                st.write(f"*Description:* {report['description']}")

# Alerts Tab
with tabs[3]:
    st.subheader("Recent Alerts")
    
    for alert in st.session_state.alerts[:10]:  # Show last 10 alerts
        if alert['type'] == 'CRITICAL':
            st.error(f"🚨 {alert['message']} - {alert['time'].strftime('%H:%M:%S')}")
        elif alert['type'] == 'WARNING':
            st.warning(f"⚠ {alert['message']} - {alert['time'].strftime('%H:%M:%S')}")
        else:
            st.info(f"ℹ {alert['message']} - {alert['time'].strftime('%H:%M:%S')}")

# Update data if monitoring is active
if st.session_state.monitoring_active:
    update_monitoring_data()
    time.sleep(update_interval)
    st.rerun()