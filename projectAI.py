import streamlit as st
import requests
import folium
from streamlit.components.v1 import html
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

# ===================== UI =====================
st.set_page_config(layout="wide")
st.title("🚕 VivuXanh 🌱")

# ===================== GEOCODING =====================
def geocode(address):
    """Dùng Nominatim để lấy tọa độ từ địa chỉ"""
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": address, "format": "json", "limit": 1}
    headers = {"User-Agent": "vivuxanh-app"}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        if data:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            return (lat, lon)
        else:
            return None
    except Exception as e:
        st.error(f"❌ Lỗi geocoding: {e}")
        return None

# ===================== FUZZY LOGIC =====================
# Antecedents (Input)
passengers = ctrl.Antecedent(np.arange(1, 9, 1), 'passengers')
terrain = ctrl.Antecedent(np.arange(0, 10.1, 0.1), 'terrain')
safety = ctrl.Antecedent(np.arange(0, 10.1, 0.1), 'safety')
eco_friendly = ctrl.Antecedent(np.arange(0, 10.1, 0.1), 'eco_friendly')

# Consequent (Output - Loại xe)
vehicle = ctrl.Consequent(np.arange(0, 10.1, 0.1), 'vehicle')

# Membership functions
passengers['low'] = fuzz.trimf(passengers.universe, [1, 1, 3])
passengers['medium'] = fuzz.trimf(passengers.universe, [2, 4, 5])
passengers['high'] = fuzz.trimf(passengers.universe, [4, 7, 8])

terrain['flat'] = fuzz.trimf(terrain.universe, [0, 0, 4])
terrain['moderate'] = fuzz.trimf(terrain.universe, [3, 5, 7])
terrain['rough'] = fuzz.trimf(terrain.universe, [6, 10, 10])

safety['low'] = fuzz.trimf(safety.universe, [0, 0, 5])
safety['high'] = fuzz.trimf(safety.universe, [5, 10, 10])

eco_friendly['low'] = fuzz.trimf(eco_friendly.universe, [0, 0, 5])
eco_friendly['high'] = fuzz.trimf(eco_friendly.universe, [5, 10, 10])

vehicle['xe_may'] = fuzz.trimf(vehicle.universe, [0, 0, 3])
vehicle['xe_may_dien'] = fuzz.trimf(vehicle.universe, [2, 3.5, 5])
vehicle['xe_oto'] = fuzz.trimf(vehicle.universe, [4, 6, 8])
vehicle['xe_oto_dien'] = fuzz.trimf(vehicle.universe, [7, 10, 10])

# Rules
rules = [
    ctrl.Rule(passengers['low'] & terrain['flat'] & safety['low'], vehicle['xe_may']),
    ctrl.Rule(passengers['low'] & eco_friendly['high'], vehicle['xe_may_dien']),
    ctrl.Rule(terrain['flat'] & eco_friendly['high'], vehicle['xe_may_dien']),
    ctrl.Rule(passengers['medium'] | passengers['high'], vehicle['xe_oto']),
    ctrl.Rule(terrain['rough'] | terrain['moderate'], vehicle['xe_oto']),
    ctrl.Rule(safety['high'] & passengers['medium'], vehicle['xe_oto']),
    ctrl.Rule(passengers['medium'] & eco_friendly['high'], vehicle['xe_oto_dien']),
    ctrl.Rule(eco_friendly['high'] & safety['high'], vehicle['xe_oto_dien']),
    ctrl.Rule(terrain['flat'] & eco_friendly['high'] & passengers['medium'], vehicle['xe_oto_dien']),
]

vehicle_ctrl = ctrl.ControlSystem(rules)

# ===================== GIÁ =====================
pricing = {
    "XE MÁY 🏍️": {"base": 12000, "per_km": 4500, "per_min": 250},
    "XE MÁY ĐIỆN ⚡": {"base": 15000, "per_km": 5000, "per_min": 300},
    "XE Ô TÔ 🚗": {"base": 25000, "per_km": 10000, "per_min": 500},
    "XE Ô TÔ ĐIỆN ⚡🚘": {"base": 35000, "per_km": 13000, "per_min": 700},
}

# ===================== OSRM =====================
def route(p1, p2):
    url = f"http://router.project-osrm.org/route/v1/driving/{p1[1]},{p1[0]};{p2[1]},{p2[0]}?overview=full&geometries=geojson"
    r = requests.get(url).json()
    route = r['routes'][0]
    d = route['distance']/1000
    t = route['duration']/60
    coords = [(lat, lon) for lon, lat in route['geometry']['coordinates']]
    return d, t, coords

# ===================== UI INPUT =====================
st.markdown("### 📍 Nhập địa chỉ")
col1, col2 = st.columns(2)
with col1:
    p1_input = st.text_input("📍 Điểm đón")
with col2:
    p2_input = st.text_input("📍 Điểm đến")

st.markdown("### ⚙️ Gợi ý phương tiện di chuyển phù hợp")
colA, colB = st.columns(2)
with colA:
    num_passengers = st.slider("👥 Số lượng người", 1, 8, 1)
    terrain_val = st.select_slider("🛤️ Địa hình", 
                                  options=["Bằng phẳng", "Có dốc", "Gồ ghề"], 
                                  value="Bằng phẳng")
with colB:
    safety_val = st.slider("🛡️ Độ an toàn ưu tiên", 0.0, 10.0, 7.0)
    eco_val = st.slider("🌱 Độ thân thiện môi trường", 0.0, 10.0, 6.0)

terrain_map = {"Bằng phẳng": 2, "Có dốc": 6, "Gồ ghề": 9}

# ===================== Người dùng chọn phương tiện =====================
vehicle_options = ["Gợi ý từ hệ thống", "XE MÁY 🏍️", "XE MÁY ĐIỆN ⚡", "XE Ô TÔ 🚗", "XE Ô TÔ ĐIỆN ⚡🚘"]
selected_vehicle = st.selectbox("🚗 Chọn phương tiện", vehicle_options)

# ===================== RUN =====================
if st.button("🚀 Tìm xe", type="primary"):
    start = geocode(p1_input)
    end = geocode(p2_input)
    
    if not start or not end:
        st.error("❌ Không tìm thấy địa chỉ")
        st.stop()

    d, t, coords = route(start, end)

    # Nếu người dùng chọn "Gợi ý từ hệ thống" thì chạy fuzzy
    if selected_vehicle == "Gợi ý từ hệ thống":
        sim = ctrl.ControlSystemSimulation(vehicle_ctrl)
        sim.input['passengers'] = num_passengers
        sim.input['terrain'] = terrain_map[terrain_val]
        sim.input['safety'] = safety_val
        sim.input['eco_friendly'] = eco_val
        sim.compute()
        
        v = sim.output['vehicle']
        if v < 3:
            name = "XE MÁY 🏍️"
        elif v < 5:
            name = "XE MÁY ĐIỆN ⚡"
        elif v < 7.5:
            name = "XE Ô TÔ 🚗"
        else:
            name = "XE Ô TÔ ĐIỆN ⚡🚘"
    else:
        name = selected_vehicle

    # ===== GIÁ =====
    p = pricing[name]
    base = p["base"]
    dist_cost = d * p["per_km"]
    time_cost = t * p["per_min"]
    final_price = base + dist_cost + time_cost
    final_price = int(final_price / 1000) * 1000

    # ===== MAP =====
    m = folium.Map(location=start, zoom_start=14, tiles="cartodbpositron")
    folium.Marker(start, popup="Pickup", icon=folium.Icon(color="green", icon="play")).add_to(m)
    folium.Marker(end, popup="Destination", icon=folium.Icon)
