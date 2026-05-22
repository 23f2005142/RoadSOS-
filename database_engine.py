import random
import requests
from geopy.distance import geodesic
from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="roadsos_goldenhour_live")

def get_coordinates(location_name):
    """Fallback text-to-GPS if browser location is denied."""
    try:
        location = geolocator.geocode(location_name)
        if location: return location.latitude, location.longitude
    except: pass
    return 21.1250, 79.0600 # Fallback to Nagpur 

def get_real_infrastructure(lat, lon, radius_meters=5000): # Reduced to 5km for faster API response
    """
    Queries the OpenStreetMap database for REAL hospitals using SECURE HTTPS.
    Includes a User-Agent header to prevent the server from blocking us.
    """
    overpass_url = "https://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json];
    (
      node["amenity"="hospital"](around:{radius_meters},{lat},{lon});
      node["amenity"="police"](around:{radius_meters},{lat},{lon});
    );
    out center;
    """
    
    # THE FIX: OpenStreetMap strictly blocks requests without a User-Agent. 
    # This acts as our digital nametag.
    headers = {
        "User-Agent": "ROADSOS_IITMadras_GoldenHour/1.0"
    }
    
    try:
        # We pass the headers into the request
        response = requests.get(overpass_url, params={'data': overpass_query}, headers=headers, timeout=10)
        response.raise_for_status() 
        data = response.json()
        
        hospitals = []
        police = []
        
        for element in data.get('elements', []):
            tags = element.get('tags', {})
            name = tags.get('name', 'Local Facility (Unnamed)')
            e_lat = element['lat']
            e_lon = element['lon']
            dist = round(geodesic((lat, lon), (e_lat, e_lon)).km, 1)
            
            node_data = {
                "name": name, 
                "lat": e_lat, 
                "lon": e_lon, 
                "dist": dist,
                "phone": tags.get('phone', "Dial 112 / 108")
            }
            
            if tags.get('amenity') == 'hospital':
                hospitals.append(node_data)
            elif tags.get('amenity') == 'police':
                police.append(node_data)
                
        return sorted(hospitals, key=lambda x: x['dist']), sorted(police, key=lambda x: x['dist'])
    except Exception as e:
        print(f"CRITICAL OVERPASS ERROR: {e}")
        return [], []
        
def generate_local_services(center_lat, center_lon):
    """Combines REAL infrastructure with the Simulated Vanguard network."""
    real_hospitals, real_police = get_real_infrastructure(center_lat, center_lon)
    
    # If the real API fails or finds nothing, inject intelligent fallbacks
    services = {
        "hospitals": real_hospitals if real_hospitals else [{"name": "Regional Trauma Center", "lat": center_lat+0.01, "lon": center_lon+0.01, "dist": 2.1, "phone": "108"}],
        "police": real_police if real_police else [{"name": "Highway Patrol Outpost", "lat": center_lat-0.01, "lon": center_lon-0.01, "dist": 1.5, "phone": "112"}],
        "towing": [], 
        "vanguard": []
    }
    
    # Generate the Decentralized Network (Students and Tow Trucks)
    for i in range(3):
        t_lat, t_lon = center_lat + random.uniform(-0.04, 0.04), center_lon + random.uniform(-0.04, 0.04)
        services["towing"].append({
            "name": f"Local Tow & Rescue {i+1}", "lat": t_lat, "lon": t_lon, 
            "dist": round(geodesic((center_lat, center_lon), (t_lat, t_lon)).km, 1),
            "phone": "+91 80000 00000"
        })
        
    for i in range(5):
        v_lat, v_lon = center_lat + random.uniform(-0.03, 0.03), center_lon + random.uniform(-0.03, 0.03)
        services["vanguard"].append({
            "name": f"Vanguard Med Student {i+1}", "lat": v_lat, "lon": v_lon,
            "dist": round(geodesic((center_lat, center_lon), (v_lat, v_lon)).km, 1),
            "phone": "App User"
        })
        
    services["towing"] = sorted(services["towing"], key=lambda x: x['dist'])
    services["vanguard"] = sorted(services["vanguard"], key=lambda x: x['dist'])
    
    return services
