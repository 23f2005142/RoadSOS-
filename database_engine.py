import random
from geopy.distance import geodesic
from geopy.geocoders import Nominatim

# We set a custom user agent for the geocoder
geolocator = Nominatim(user_agent="roadsos_goldenhour_demo")

def get_coordinates(location_name):
    """Converts a typed city/highway into GPS coordinates."""
    try:
        location = geolocator.geocode(location_name)
        if location:
            return location.latitude, location.longitude
    except Exception as e:
        print(f"Geocoding error: {e}")
        pass
    # Fallback to Nagpur Highway coordinates if network fails
    return 21.1250, 79.0600 

def generate_local_services(center_lat, center_lon):
    """
    DYNAMIC GLOBAL ENGINE:
    Generates local emergency infrastructure within a 10km radius 
    of ANY given coordinate on Earth.
    """
    services = {
        "hospitals": [], 
        "police": [], 
        "towing": [], 
        "puncture": [], 
        "vanguard": []
    }
    
    categories = [
        ("hospitals", "Trauma Center", 3),
        ("police", "Police Station", 2),
        ("towing", "Vehicle Rescue & Tow", 3),
        ("puncture", "24/7 Puncture & Service", 4),
        ("vanguard", "Med Student (Vanguard)", 8)
    ]
    
    for cat_key, prefix, count in categories:
        for i in range(count):
            # Generate nodes within ~5-10km radius
            lat = center_lat + random.uniform(-0.05, 0.05)
            lon = center_lon + random.uniform(-0.05, 0.05)
            dist = round(geodesic((center_lat, center_lon), (lat, lon)).km, 1)
            
            services[cat_key].append({
                "name": f"Local {prefix} {i+1}",
                "lat": lat,
                "lon": lon,
                "dist": dist,
                "phone": f"+91 {random.randint(9000000000, 9999999999)}",
                "level": random.randint(1, 5) if cat_key == "vanguard" else None
            })
            
    # Sort all lists by closest distance
    for key in services:
        services[key] = sorted(services[key], key=lambda x: x['dist'])
        
    return services
