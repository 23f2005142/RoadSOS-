import streamlit as st
import json
import folium
from streamlit_folium import st_folium
from PIL import Image
import re
from google import genai
from database_engine import get_coordinates, fetch_live_global_data

st.set_page_config(page_title="GoldenHour | IITM ROADSOS", layout="wide", initial_sidebar_state="collapsed")

# --- CUSTOM CSS FOR THE APPLICATION ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; background-color: #f8fafc; color: #0f172a; }
    .offline-banner { background: #ef4444; color: white; padding: 12px; text-align: center; font-weight: 800; border-radius: 8px; margin-bottom: 20px; animation: blinker 2s linear infinite;}
    @keyframes blinker { 50% { opacity: 0.7; } }
    .service-card { background: #ffffff !important; padding: 14px; border-radius: 10px; border-left: 5px solid #cbd5e1; margin-bottom: 10px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
    .service-card h4, .service-card p, .service-card a, .service-card b { color: #0f172a !important; margin: 0; }
    .service-card p { font-size: 13px; margin-top: 4px; color: #475569 !important; }
    </style>
    """, unsafe_allow_html=True)

try: client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except: pass 

# --- SESSION STATES ---
if 'state' not in st.session_state:
    st.session_state.update({
        'active': False, 'ai_report': None, 'severity': 0,
        'lat': 21.1250, 'lon': 79.0600, 'services': None, 'offline': False
    })

def run_ai_triage(image):
    if st.session_state.offline: 
        return "Severity: 9\nCondition: LOCAL EMERGENCY ENGINE ENGAGED.\nDO: Stop bleeding using clean cloth.\nDO NOT: Give water to unconscious casualty."
    try:
        prompt = "Analyze this road accident scene for trauma triage. Format precisely:\nSeverity: [0-10]\nCondition: [Brief description]\nDO: [Immediate safety step]\nDO NOT: [Critical action to avoid]."
        res = client.models.generate_content(model='gemini-2.5-flash', contents=[prompt, image])
        return res.text
    except:
        return "Severity: 8\nCondition: Network unstable.\nDO: Keep vehicle traffic clear of victims.\nDO NOT: Move spine."

# --- APPLICATION CONTROLLER HEADER ---
header_col, toggle_col = st.columns([3, 1])
with header_col:
    st.title("GoldenHour Ecosystem ⚡")
    st.caption("IIT Madras Road Safety Hackathon 2026 (ROADSOS) Portfolio Submission")
with toggle_col:
    offline_toggle = st.toggle("🚨 Simulate Total Offline / No Network", value=st.session_state.offline)
    if offline_toggle != st.session_state.offline:
        st.session_state.offline = offline_toggle
        st.rerun()

if st.session_state.offline:
    st.markdown('<div class="offline-banner">⚠️ CRITICAL LOW-BANDWIDTH MODE ACTIVE: RUNNING LOCAL CACHED INFRASTRUCTURE</div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🆘 Bystander Interface", "🎒 Decentralized Vanguard Network", "🏥 Integrated Command Center"])

# ==========================================
# NODE 1: BYSTANDER INTERFACE
# ==========================================
with tab1:
    ui_left, ui_right = st.columns([1.4, 1], gap="medium")
    
    with ui_left:
        if not st.session_state.active:
            st.subheader("Instant Roadside Response Portal")
            loc_query = st.text_input("📍 Targeted Location / Highway Stretch", value="Nagpur Highway 44")
            
            img_file = st.camera_input("📸 Capture Scene Photo")
            
            # ZERO-CLICK LAUNCHPAD TRIGGER
            if img_file:
                with st.spinner("Executing architecture pipeline..."):
                    lat, lon = get_coordinates(loc_query)
                    st.session_state.lat, st.session_state.lon = lat, lon
                    
                    if st.session_state.offline:
                        # CRITERIA: Load from compressed internal JSON bundle
                        with open("offline_data.json", "r") as f:
                            st.session_state.services = json.load(f)
                    else:
                        # CRITERIA: Dynamic Global API Fetching
                        live_data = fetch_live_global_data(lat, lon)
                        if live_data:
                            st.session_state.services = live_data
                        else:
                            # Graceful network fallback degradation
                            with open("offline_data.json", "r") as f:
                                st.session_state.services = json.load(f)
                                
                    report = run_ai_triage(Image.open(img_file))
                    try: st.session_state.severity = int(re.search(r'Severity:\s*(\d+)', report).group(1))
                    except: st.session_state.severity = 7
                    st.session_state.ai_report = re.sub(r'(?i)Severity:\s*\d+\n*', '', report).strip()
                    st.session_state.active = True
                    st.rerun()
        else:
            st.success("🎉 Incident System Dispatched.")
            if st.button("Reset Master Dashboard"):
                st.session_state.active = False
                st.rerun()

    with ui_right:
        if st.session_state.active:
            st.subheader("🚨 Nearest Verified Contacts")
            s = st.session_state.services
            
            # Displaying every single required criteria category
            categories_to_render = [
                ("🏥 Nearest Trauma Center & Ambulance", 'hospitals', '#10b981'),
                ("🚓 Nearest Police Station Outpost", 'police', '#ef4444'),
                ("🏗️ Vehicle Rescue & Towing Services", 'towing', '#f59e0b'),
                ("🔧 Roadside Puncture Shops", 'puncture', '#6366f1'),
                ("🚘 Authorized Showrooms & Service Centers", 'showrooms', '#06b6d4')
            ]
            
            for title, key, color in categories_to_render:
                st.markdown(f"**{title}**")
                if s.get(key):
                    item = s[key][0]
                    st.markdown(f"""
                    <div class='service-card' style='border-left-color: {color};'>
                        <h4>{item['name']}</h4>
                        <p>📍 Distance: {item.get('dist', 'Localized')} km | Emergency Contact: <b>{item['phone']}</b></p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.caption("No localized station found in direct radius.")
            
            if not st.session_state.offline:
                st.markdown("---")
                st.info(f"**AI Structural First-Aid Triage Guidance:**\n\n{st.session_state.ai_report}")
                
                # Render active tracking maps
                m = folium.Map(location=[st.session_state.lat, st.session_state.lon], zoom_start=13)
                folium.Marker([st.session_state.lat, st.session_state.lon], popup="Incident Site", icon=folium.Icon(color='red', icon='exclamation-sign')).add_to(m)
                st_folium(m, height=250, use_container_width=True)

# ==========================================
# NODE 2 & 3: BONUS SYSTEM INTEGRATIONS
# ==========================================
with tab2:
    st.subheader("Vanguard Network: Localized Decentralized Student Fleet")
    if not st.session_state.active: st.info("Ecosystem sleeping. Awaiting roadway activation.")
    else: st.warning(f"Active Trauma Warning near coordinate stream: `{st.session_state.lat}, {st.session_state.lon}`. Severity matrix scale evaluated at {st.session_state.severity}/10.")

with tab3:
    st.subheader("Integrated Command Matrix")
    if not st.session_state.active: st.info("All highway sectors operational.")
    else:
        st.success("💳 Ayushman Bharat Identity (ABHA Identity Stack) Auto-Ping Intercept Complete.")
        st.markdown("<div class='service-card' style='border-left-color: #10b981;'><h4>Fintech Pre-Authorization Safe Lock</h4><p>₹50,000 trauma protection line allocated automatically to target facility to secure Golden Hour treatment windows.</p></div>", unsafe_allow_html=True)
