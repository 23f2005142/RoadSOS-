import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from PIL import Image
import re
import html
import time
from google import genai
from google.genai import types
from database_engine import get_coordinates, generate_local_services

# --- UI REDESIGN ---
st.set_page_config(page_title="GoldenHour Ecosystem", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; background-color: #f8fafc; color: #0f172a; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; font-weight: 600; transition: 0.2s; border: none; }
    .stButton>button[kind="primary"] { background: #2563eb; color: white; }
    .sos-btn>button { background: #ef4444 !important; color: white !important; font-size: 1.2em !important; font-weight: 800 !important; border-radius: 12px; height: 4em;}
    
    /* Ecosystem Cards */
    .offline-banner { background: #000; color: #fbbf24; padding: 12px; text-align: center; font-weight: 800; letter-spacing: 1px; border-radius: 8px; margin-bottom: 20px;}
    .service-card { background: #ffffff !important; padding: 16px; border-radius: 12px; border-left: 6px solid #e2e8f0; margin-bottom: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
    /* THIS IS THE FIX: Force all text inside the card to be dark */
    .service-card, .service-card h4, .service-card p, .service-card b, .service-card span, .service-card i { color: #0f172a !important; }
    .status-badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 700; background: #dcfce7 !important; color: #166534 !important; }
    .progress-box { background: #fff; padding: 20px; border-radius: 12px; border: 2px solid #3b82f6; text-align: center; margin-top: 15px;}
    </style>
    """, unsafe_allow_html=True)

# --- API & STATE INITIALIZATION ---
try:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except: pass 

if 'ecosystem_state' not in st.session_state:
    st.session_state.update({
        'ecosystem_state': 'idle', # idle -> active -> dispatched
        'ai_report': None, 'severity': 0, 
        'acc_lat': 21.1250, 'acc_lon': 79.0600,
        'local_services': None, 'offline_mode': False,
        'active_vanguard': None, 'eta': 0
    })

def get_ai_triage(image, text_context):
    if st.session_state.offline_mode: 
        return "Severity: 9\nCondition: OFFLINE MODE. AI bypassed.\nDO: Secure scene.\nDO NOT: Move patient."
    try:
        prompt = f"Analyze: '{text_context}'. Rule: Internal distress = severity 8-10. Format EXACTLY: \nSeverity: [0-10]\nCondition: [Brief]\nDO: [1 action]\nDO NOT: [1 avoidance]."
        inputs = [prompt, image] if image else [prompt]
        res = client.models.generate_content(model='gemini-2.5-flash', contents=inputs)
        return res.text
    except:
        return "Severity: 8\nCondition: Unstable Network.\nDO: Keep warm.\nDO NOT: Move patient."

# --- GLOBAL HEADER ---
col1, col2 = st.columns([3, 1])
with col1:
    st.title("GoldenHour ⚡")
    st.caption("Autonomous Highway Emergency Ecosystem")
with col2:
    st.session_state.offline_mode = st.toggle("📡 Simulate 2G / Offline", value=st.session_state.offline_mode)

if st.session_state.offline_mode:
    st.markdown('<div class="offline-banner">⚠️ 2G EDGE NETWORK ENGAGED. AUTONOMOUS LOCAL ROUTING ACTIVE.</div>', unsafe_allow_html=True)

# --- THE 3-NODE ECOSYSTEM ---
tab1, tab2, tab3 = st.tabs(["🆘 Node 1: Bystander", "🎒 Node 2: Vanguard App", "🏥 Node 3: Command Hub"])

# ==========================================
# TAB 1: THE BYSTANDER (TRIGGER)
# ==========================================
with tab1:
    c1, c2 = st.columns([1.5, 1], gap="large")
    with c1:
        loc_input = st.text_input("📍 Auto-Detected Location", value="Nagpur Highway 44")
        img_file = st.camera_input("📸 Scene Scan") if not st.session_state.offline_mode else None
        raw_context = st.text_input("💬 Context (e.g., 'Two-wheeler collision')", max_chars=100)
        
        st.markdown('<div class="sos-btn">', unsafe_allow_html=True)
        if st.button("🚨 INITIATE ECOSYSTEM RESPONSE"):
            with st.spinner("Locking coordinates & routing network..."):
                lat, lon = get_coordinates(loc_input)
                st.session_state.acc_lat, st.session_state.acc_lon = lat, lon
                st.session_state.local_services = generate_local_services(lat, lon)
                
                report = get_ai_triage(Image.open(img_file) if img_file else None, html.escape(raw_context.strip()))
                try: st.session_state.severity = int(re.search(r'Severity:\s*(\d+)', report).group(1))
                except: st.session_state.severity = 8 
                
                st.session_state.ai_report = re.sub(r'(?i)Severity:\s*\d+\n*', '', report).strip()
                st.session_state.ecosystem_state = 'active'
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        if st.session_state.ecosystem_state != 'idle':
            if st.session_state.ecosystem_state == 'dispatched':
                st.markdown(f"""
                <div class='progress-box'>
                    <h3>🎒 Vanguard En Route!</h3>
                    <p><b>{st.session_state.active_vanguard['name']}</b> (Med Student) is navigating to you.</p>
                    <h2 style='color:#2563eb;'>ETA: {st.session_state.eta} Mins</h2>
                    <span class='status-badge'>Hospital ER Prepped</span>
                </div>
                """, unsafe_allow_html=True)
            
            st.subheader("Automated Dispatch Log")
            srv = st.session_state.local_services
            st.info(f"**AI Triage:**\n\n{st.session_state.ai_report}")
            
            st.markdown(f"""
            <div class='service-card' style='border-left-color: #ef4444;'>
                <h4>🚓 Highway Patrol Auto-Pinged</h4>
                <p>{srv['police'][0]['name']} • {srv['police'][0]['dist']} km</p>
            </div>
            <div class='service-card' style='border-left-color: #f59e0b;'>
                <h4>🏗️ Tow Truck Auto-Pinged</h4>
                <p>{srv['towing'][0]['name']} • {srv['towing'][0]['dist']} km</p>
            </div>
            """, unsafe_allow_html=True)

# ==========================================
# TAB 2: VANGUARD RESPONDER (DISPATCH)
# ==========================================
with tab2:
    st.subheader("Vanguard Network: Local Med Students")
    if st.session_state.ecosystem_state == 'idle':
        st.write("🟢 You are on duty. Awaiting local SOS pings...")
        
    elif st.session_state.ecosystem_state == 'active':
        st.error("🚨 CRITICAL SOS: 3km from your location!")
        vanguard = st.session_state.local_services['vanguard'][0]
        
        st.write(f"**Severity Level:** {st.session_state.severity}/10")
        st.write(f"**AI Scene Assessment:**\n{st.session_state.ai_report}")
        
        if st.button("✅ ACCEPT DISPATCH & NAVIGATE", type="primary"):
            st.session_state.active_vanguard = vanguard
            st.session_state.eta = int(vanguard['dist'] * 3) # Rough ETA calc
            st.session_state.ecosystem_state = 'dispatched'
            st.rerun()
            
    elif st.session_state.ecosystem_state == 'dispatched':
        st.success(f"📍 Navigating to Crash Site. ETA: {st.session_state.eta} mins.")
        if not st.session_state.offline_mode:
            m = folium.Map(location=[st.session_state.acc_lat, st.session_state.acc_lon], zoom_start=14)
            folium.Marker([st.session_state.acc_lat, st.session_state.acc_lon], popup="Victim", icon=folium.Icon(color='red')).add_to(m)
            st_folium(m, height=300, use_container_width=True)

# ==========================================
# TAB 3: COMMAND & INSURANCE (INFRASTRUCTURE)
# ==========================================
with tab3:
    st.subheader("Hospital ER & Financial Command")
    if st.session_state.ecosystem_state == 'idle':
        st.info("ER Dashboard clear.")
    else:
        srv = st.session_state.local_services['hospitals'][0]
        st.write(f"**Target Facility:** {srv['name']} (Trauma Level 1)")
        
        st.markdown(f"""
        <div class='service-card'>
            <h4>💳 Ayushman Bharat (ABHA) Auto-Claim</h4>
            <p><b>Status:</b> <span style='color:green;font-weight:bold;'>PRE-AUTHORIZED</span></p>
            <p><b>Fund Allocated:</b> ₹50,000 (GoldenHour Emergency Protocol)</p>
            <p><i>The hospital is guaranteed payment. No billing delays upon arrival.</i></p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.ecosystem_state == 'dispatched':
            st.warning(f"🚑 Vanguard Responding. ER Prep Initiated for Severity {st.session_state.severity} trauma.")
        
        st.markdown("---")
        if st.button("Close Incident (Post-Care)"):
            st.session_state.ecosystem_state = 'idle'
            st.session_state.active_vanguard = None
            st.rerun()
