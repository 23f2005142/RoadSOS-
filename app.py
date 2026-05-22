import streamlit as st
import pandas as pd
import folium
from folium import plugins
from streamlit_folium import st_folium
from PIL import Image
import re
import html
import time
from datetime import datetime
from google import genai
from google.genai import types
from database_engine import get_coordinates, generate_local_services

# --- UI REDESIGN ---
st.set_page_config(page_title="GoldenHour | ROADSOS", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; background-color: #fcfcfd; color: #1e293b; }
    .stButton>button { width: 100%; border-radius: 12px; height: 3em; font-weight: 600; transition: 0.3s; border: none; }
    .stButton>button[kind="primary"] { background: linear-gradient(135deg, #4f46e5 0%, #3b82f6 100%); color: white; }
    .sos-btn>button { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important; color: white !important; font-size: 1.1em !important; }
    
    /* Offline Mode Banner & Cards */
    .offline-banner { background-color: #000000; color: #fbbf24; padding: 10px; text-align: center; font-weight: 800; letter-spacing: 2px; border-radius: 8px; margin-bottom: 20px;}
    .service-card { background: #ffffff; padding: 15px; border-radius: 10px; border-left: 5px solid #3b82f6; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .service-card h4 { margin: 0 0 5px 0; color: #0f172a; }
    .service-card p { margin: 0; color: #475569; font-size: 14px; }
    
    /* VibeCon/ROADSOS Input Fixes */
    .stTextInput input, .stTextArea textarea { color: #0f172a !important; background-color: #ffffff !important; font-weight: 500 !important; }
    label { color: #0f172a !important; font-weight: 600 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- API INITIALIZATION ---
try:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except:
    pass # Offline mode handles API absence smoothly

# --- GLOBAL STATE ---
if 'emergency_state' not in st.session_state:
    st.session_state.update({
        'emergency_state': 'idle', 'ai_report': None, 'severity': 0, 
        'acc_lat': 21.1250, 'acc_lon': 79.0600,
        'local_services': None, 'offline_mode': False
    })

# --- HYBRID AI TRIAGE ENGINE ---
def get_ai_triage(image, text_context):
    if st.session_state.offline_mode: 
        return "Severity: 9\nCondition: OFFLINE MODE ACTIVE. AI bypassed for bandwidth preservation.\nDO: Call emergency services directly from the list below.\nDO NOT: Wait for network connection."
    try:
        prompt = f"""
        Analyze image/text context: '{text_context}'. 
        Rule: Internal distress or severe trauma = high severity (8-10). 
        Format EXACTLY: 
        Severity: [0-10]
        Condition: [Brief]
        DO: [1 calm physical action]
        DO NOT: [1 thing to avoid].
        """
        safety_settings = [
            types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
            types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH)
        ]
        inputs = [prompt, image] if image else [prompt]
        res = client.models.generate_content(model='gemini-2.5-flash', contents=inputs, config=types.GenerateContentConfig(safety_settings=safety_settings))
        return res.text
    except Exception as e:
        return "Severity: 8\nCondition: Connection unstable.\nDO: Keep patient warm.\nDO NOT: Move patient unnecessarily."

# --- HEADER & NETWORK TOGGLE ---
col_logo, col_toggle = st.columns([3, 1])
with col_logo:
    st.title("GoldenHour 💙 ROADSOS")
    st.caption("Global Highway & Trauma Network")
with col_toggle:
    offline_toggle = st.toggle("📡 Simulate 2G / Offline Mode", value=st.session_state.offline_mode)
    if offline_toggle != st.session_state.offline_mode:
        st.session_state.offline_mode = offline_toggle
        st.rerun()

if st.session_state.offline_mode:
    st.markdown('<div class="offline-banner">⚠️ 2G / LOW NETWORK MODE ENGAGED. HEAVY ASSETS DISABLED.</div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🆘 Accident Bystander", "🏥 Ecosystem Command"])

# ==========================================
# TAB 1: BYSTANDER INTERFACE
# ==========================================
with tab1:
    col_main, col_side = st.columns([1.5, 1], gap="large")
    
    with col_main:
        st.subheader("Get Immediate Roadside Help")
        
        # GLOBAL APPLICABILITY
        loc_input = st.text_input("📍 Your Location (City, Highway, or Landmark)", value="Nagpur Highway")
        
        if not st.session_state.offline_mode:
            img_file = st.camera_input("📸 Secure Scene Scan (Optional)")
        else:
            img_file = None
            st.info("📷 Camera integration disabled to preserve bandwidth.")
            
        raw_context = st.text_input("💬 What happened? (e.g., 'Car crash', 'Bike skid')", max_chars=150)
        
        st.markdown('<div class="sos-btn">', unsafe_allow_html=True)
        sos_trigger = st.button("🚨 TRIGGER ROAD SOS")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if sos_trigger:
            with st.spinner("Locking GPS and mapping infrastructure..."):
                # Geocode location to GPS
                lat, lon = get_coordinates(loc_input)
                st.session_state.acc_lat, st.session_state.acc_lon = lat, lon
                
                # Generate infrastructure around that GPS
                st.session_state.local_services = generate_local_services(lat, lon)
                
                # Run Triage (or skip if offline)
                pil_img = Image.open(img_file) if img_file else None
                report = get_ai_triage(pil_img, html.escape(raw_context.strip()))
                
                try: 
                    st.session_state.severity = int(re.search(r'Severity:\s*(\d+)', report).group(1))
                except: 
                    st.session_state.severity = 8 
                
                st.session_state.ai_report = re.sub(r'(?i)Severity:\s*\d+\n*', '', report).strip()
                st.session_state.emergency_state = 'active'
                st.rerun()

    with col_side:
        if st.session_state.emergency_state == 'active':
            srv = st.session_state.local_services
            
            # IIT MADRAS REQUIREMENTS: Nearest Police, Ambulance, Towing, Puncture
            st.subheader("🚑 Nearest Dispatch Directory")
            
            st.markdown(f"""
            <div class='service-card' style='border-color: #ef4444;'>
                <h4>🚓 {srv['police'][0]['name']}</h4>
                <p>📍 {srv['police'][0]['dist']} km away</p>
                <a href="tel:{srv['police'][0]['phone']}" style="color: #ef4444; font-weight: bold; text-decoration: none;">📞 DISPATCH POLICE</a>
            </div>
            <div class='service-card' style='border-color: #10b981;'>
                <h4>🏥 {srv['hospitals'][0]['name']}</h4>
                <p>📍 {srv['hospitals'][0]['dist']} km away | Trauma Lvl 1</p>
                <a href="tel:{srv['hospitals'][0]['phone']}" style="color: #10b981; font-weight: bold; text-decoration: none;">📞 CALL AMBULANCE</a>
            </div>
            <div class='service-card' style='border-color: #f59e0b;'>
                <h4>🏗️ {srv['towing'][0]['name']}</h4>
                <p>📍 {srv['towing'][0]['dist']} km away</p>
                <a href="tel:{srv['towing'][0]['phone']}" style="color: #f59e0b; font-weight: bold; text-decoration: none;">📞 REQUEST TOW</a>
            </div>
            <div class='service-card' style='border-color: #64748b;'>
                <h4>🔧 {srv['puncture'][0]['name']}</h4>
                <p>📍 {srv['puncture'][0]['dist']} km away</p>
                <a href="tel:{srv['puncture'][0]['phone']}" style="color: #64748b; font-weight: bold; text-decoration: none;">📞 FIX PUNCTURE</a>
            </div>
            """, unsafe_allow_html=True)
            
            if not st.session_state.offline_mode:
                st.markdown("---")
                st.info(f"**AI First-Aid Instructions:**\n\n{st.session_state.ai_report}")
                
                # Dynamic Global Map
                m = folium.Map(location=[st.session_state.acc_lat, st.session_state.acc_lon], zoom_start=13)
                folium.Marker([st.session_state.acc_lat, st.session_state.acc_lon], popup="Crash Site", icon=folium.Icon(color='red', icon='info-sign')).add_to(m)
                
                # Add closest services to map
                h = srv['hospitals'][0]
                p = srv['police'][0]
                folium.Marker([h['lat'], h['lon']], popup=h['name'], icon=folium.Icon(color='green', icon='plus')).add_to(m)
                folium.Marker([p['lat'], p['lon']], popup=p['name'], icon=folium.Icon(color='blue', icon='flag')).add_to(m)
                
                st_folium(m, height=300, use_container_width=True)

# ==========================================
# TAB 2: ECOSYSTEM COMMAND
# ==========================================
with tab2:
    st.subheader("🏥 Regional Highway Command")
    if st.session_state.emergency_state == 'active':
        st.error(f"🔴 ACTIVE ROADWAY INCIDENT (Severity: {st.session_state.severity})")
        st.write(f"**Coordinates:** `{st.session_state.acc_lat}, {st.session_state.acc_lon}`")
        
        st.write("**💳 Smart Insurance Ping (ABHA Match)**")
        st.markdown("""
        <div style='background:#f8fafc; padding:12px; border-radius:8px; border-left: 4px solid #3b82f6;'>
            <div style='font-size:14px;'><b>Provider:</b> National Highway Authority / Ayushman Bharat</div>
            <div style='color:#059669; font-weight:bold; font-size:14px;'>✅ Pre-Auth Approved (GoldenHour Road Auto-Claim)</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Resolve Highway Incident", type="primary"):
            st.session_state.emergency_state = 'idle'
            st.rerun()
    else:
        st.info("Awaiting incoming highway SOS triggers...")
        st.write("🟢 **Dashboard clear. All highway sectors nominal.**")
