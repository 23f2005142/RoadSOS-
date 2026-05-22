import streamlit as st
import folium
from streamlit_folium import st_folium
from streamlit_geolocation import streamlit_geolocation
from PIL import Image
import re
import html
from google import genai
from database_engine import generate_local_services

st.set_page_config(page_title="GoldenHour Ecosystem", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; background-color: #f8fafc; color: #0f172a; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; font-weight: 600; transition: 0.2s; border: none; }
    .stButton>button[kind="primary"] { background: #2563eb; color: white; }
    .offline-banner { background: #000; color: #fbbf24; padding: 12px; text-align: center; font-weight: 800; border-radius: 8px; margin-bottom: 20px;}
    .service-card { background: #ffffff !important; padding: 16px; border-radius: 12px; border-left: 6px solid #e2e8f0; margin-bottom: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
    .service-card, .service-card h4, .service-card p, .service-card b, .service-card span, .service-card i, .service-card a { color: #0f172a !important; }
    .status-badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 700; background: #dcfce7 !important; color: #166534 !important; }
    .progress-box { background: #ffffff !important; padding: 20px; border-radius: 12px; border: 2px solid #3b82f6; text-align: center; margin-top: 15px; color: #0f172a !important;}
    </style>
    """, unsafe_allow_html=True)

try: client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except: pass 

if 'ecosystem_state' not in st.session_state:
    st.session_state.update({'ecosystem_state': 'idle', 'ai_report': None, 'severity': 0, 'acc_lat': 21.1250, 'acc_lon': 79.0600, 'local_services': None, 'offline_mode': False, 'active_vanguard': None, 'eta': 0})

def get_ai_triage(image):
    if st.session_state.offline_mode: return "Severity: 9\nCondition: OFFLINE MODE. AI bypassed.\nDO: Secure scene.\nDO NOT: Move patient."
    try:
        prompt = "Analyze this road accident scene. Rule: Internal distress or severe trauma = severity 8-10. Format EXACTLY: \nSeverity: [0-10]\nCondition: [Brief]\nDO: [1 action]\nDO NOT: [1 avoidance]."
        res = client.models.generate_content(model='gemini-2.5-flash', contents=[prompt, image])
        return res.text
    except: return "Severity: 8\nCondition: Unstable Network.\nDO: Keep warm.\nDO NOT: Move patient."

col1, col2 = st.columns([3, 1])
with col1: st.title("GoldenHour ⚡ ROADSOS")
with col2:
    offline_toggle = st.toggle("📡 Simulate 2G / Offline", value=st.session_state.offline_mode)
    if offline_toggle != st.session_state.offline_mode:
        st.session_state.offline_mode = offline_toggle
        st.rerun()

if st.session_state.offline_mode: st.markdown('<div class="offline-banner">⚠️ 2G EDGE NETWORK / OFFLINE ENGAGED.</div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🆘 Node 1: Bystander", "🎒 Node 2: Vanguard App", "🏥 Node 3: Command Hub"])

with tab1:
    c1, c2 = st.columns([1.5, 1], gap="large")
    with c1:
        if st.session_state.ecosystem_state == 'idle':
            st.markdown("### Step 1: Allow Location Access")
            loc_data = streamlit_geolocation() # User clicks this once to grant GPS access
            
            st.markdown("### Step 2: Snap a photo.")
            img_file = st.camera_input("Emergency Scan", label_visibility="collapsed")
            
            if st.session_state.offline_mode:
                st.markdown(f"""
                <a href="sms:112?body=CRITICAL%20ROAD%20SOS.%20Medical%20Emergency.%20Need%20immediate%20assistance." target="_blank" style="display: block; width: 100%; text-align: center; background-color: #ef4444; color: white; padding: 15px; border-radius: 12px; font-weight: bold; text-decoration: none; font-size: 1.2em;">
                📱 SEND OFFLINE SMS SOS
                </a>
                """, unsafe_allow_html=True)
            
            if img_file and not st.session_state.offline_mode:
                with st.spinner("Locking exact GPS & pinging regional infrastructure..."):
                    if loc_data and loc_data.get('latitude'): lat, lon = loc_data['latitude'], loc_data['longitude']
                    else: lat, lon = 21.1250, 79.0600 # Fallback to Nagpur if they didn't click
                        
                    st.session_state.acc_lat, st.session_state.acc_lon = lat, lon
                    st.session_state.local_services = generate_local_services(lat, lon)
                    
                    if st.session_state.local_services['hospitals'][0]['name'] == "Regional Trauma Center":
                        st.toast("⚠️ OSM API blocked by Cloud. Using local failsafe data.", icon="📡")
                    else:
                        st.toast("✅ Live OpenStreetMap data connected!", icon="🌍")
                    
                    report = get_ai_triage(Image.open(img_file))
                    if "Unstable Network" in report: st.error("🚨 Gemini AI Failed! Check your Streamlit Secrets.")
                    
                    try: st.session_state.severity = int(re.search(r'Severity:\s*(\d+)', report).group(1))
                    except: st.session_state.severity = 8 
                    st.session_state.ai_report = re.sub(r'(?i)Severity:\s*\d+\n*', '', report).strip()
                    st.session_state.ecosystem_state = 'active'
                    st.rerun()
        else:
            st.success("✅ **SOS Dispatched Successfully**")
            st.button("Reset Emergency Dashboard", on_click=lambda: st.session_state.update({'ecosystem_state': 'idle'}))

    with c2:
        if st.session_state.ecosystem_state != 'idle' and not st.session_state.offline_mode:
            st.subheader("Automated Dispatch Log")
            srv = st.session_state.local_services
            st.info(f"**AI Triage:**\n\n{st.session_state.ai_report}")
            st.markdown(f"""
            <div class='service-card' style='border-left-color: #ef4444;'>
                <h4>🚓 Highway Patrol Pinged</h4><p><b>{srv['police'][0]['name']}</b> • {srv['police'][0]['dist']} km</p>
            </div>
            <div class='service-card' style='border-left-color: #10b981;'>
                <h4>🏥 Destination ER</h4><p><b>{srv['hospitals'][0]['name']}</b> • {srv['hospitals'][0]['dist']} km</p>
            </div>
            """, unsafe_allow_html=True)

with tab2:
    st.subheader("Vanguard Network: Local Med Students")
    if st.session_state.ecosystem_state == 'idle': st.write("🟢 You are on duty. Awaiting local SOS pings...")
    elif st.session_state.ecosystem_state == 'active':
        vanguard = st.session_state.local_services['vanguard'][0]
        st.error("🚨 CRITICAL SOS: 3km from your location!")
        if st.button("✅ ACCEPT DISPATCH & NAVIGATE", type="primary"):
            st.session_state.active_vanguard = vanguard
            st.session_state.eta = int(vanguard['dist'] * 3)
            st.session_state.ecosystem_state = 'dispatched'
            st.rerun()
    elif st.session_state.ecosystem_state == 'dispatched':
        st.success(f"📍 Navigating to Crash Site. ETA: {st.session_state.eta} mins.")
        if not st.session_state.offline_mode:
            m = folium.Map(location=[st.session_state.acc_lat, st.session_state.acc_lon], zoom_start=14)
            folium.Marker([st.session_state.acc_lat, st.session_state.acc_lon], popup="Victim", icon=folium.Icon(color='red')).add_to(m)
            st_folium(m, height=300, use_container_width=True)

with tab3:
    st.subheader("Hospital ER & Financial Command")
    if st.session_state.ecosystem_state == 'idle': st.info("ER Dashboard clear.")
    else:
        srv = st.session_state.local_services['hospitals'][0]
        st.write(f"**Target Facility:** {srv['name']} ({srv['dist']} km away)")
        st.markdown(f"<div class='service-card'><h4>💳 Ayushman Bharat (ABHA) Auto-Claim</h4><p><b>Status:</b> <span style='color:#16a34a;font-weight:bold;'>PRE-AUTHORIZED</span></p></div>", unsafe_allow_html=True)
        if st.button("Close Incident (Post-Care)"):
            st.session_state.update({'ecosystem_state': 'idle', 'active_vanguard': None})
            st.rerun()
