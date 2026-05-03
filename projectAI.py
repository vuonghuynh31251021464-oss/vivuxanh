import streamlit as st
import requests
import folium
from streamlit.components.v1 import html
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import time
from functools import lru_cache
import random

st.set_page_config(layout="wide", page_title="VivuXanh")
st.title("🚕 VivuXanh")

# CSS khung xám bên trái
st.markdown("""
<style>
div[data-testid="column"]:first-child div[data-testid="stVerticalBlock"] {
    background-color: #1a1a2e;
    padding: 25px 20px;
    border-radius: 16px;
    border: 1px solid #2a2a40;
    min-height: 85vh;
}
</style>
""", unsafe_allow_html=True)

if 'selected_vehicle' not in st.session_state:
    st.session_state.selected_vehicle = None

# ===================== DATA =====================
driver_names = [
    "Nguyễn Văn Nam", "Trần Minh Tuấn", "Lê Hoàng Phúc",
    "Phạm Quốc Bảo", "Đỗ Anh Khoa", "Hoàng Minh Đức"
]

vehicle_models = {
    "XE MÁY 🏍️": ["Honda Vision", "Yamaha Sirius", "Honda Wave"],
    "XE MÁY ĐIỆN ⚡": ["VinFast Feliz", "Yadea G5", "Dat Bike Weaver"],
    "XE Ô TÔ 🚗": ["Toyota Vios", "Hyundai Accent", "Kia Morning"],
    "XE Ô TÔ ĐIỆN ⚡🚘": ["VinFast VF e34", "Tesla Model 3", "BYD Dolphin"]
}

# ===================== GEOCODING =====================
@lru_cache(maxsize=100)
def geocode(address):
    if not address or str(address).strip() == "":
        return None
    try:
        url = "https://photon.komoot.io/api/"
        params = {"q": str(address).strip(), "limit": 1, "lang": "vi"}
        headers = {"User-Agent": "VivuXanh-App/1.0"}
     
        time.sleep(1.0)
        r = requests.get(url, params=params, headers=headers, timeout=15)
     
        if r.status_code == 200:
            data = r.json()
            if data.get("features"):
                coords = data["features"][0]["geometry"]["coordinates"]
                return (coords[1], coords[0])

        time.sleep(1.2)
        url2 = "https://nominatim.openstreetmap.org/search"
        params2 = {"q": str(address).strip(), "format": "json", "limit": 1}
        r2 = requests.get(url2, params=params2, headers=headers, timeout=10)
     
        if r2.status_code == 200:
            data2 = r2.json()
            if data2:
                return (float(data2[0]["lat"]), float(data2[0]["lon"]))
             
        st.error(f"❌ Không tìm thấy địa chỉ: {address}")
        return None
     
    except Exception as e:
        st.error(f"❌ Lỗi geocoding: {e}")
        return None

# ===================== FUZZY =====================
passengers = ctrl.Antecedent(np.arange(1, 9, 1), 'passengers')
terrain = ctrl.Antecedent(np.arange(0, 10.1, 0.1), 'terrain')
safety = ctrl.Antecedent(np.arange(0, 10.1, 0.1), 'safety')
eco_friendly = ctrl.Antecedent(np.arange(0, 10.1, 0.1), 'eco_friendly')
vehicle = ctrl.Consequent(np.arange(0, 10.1, 0.1), 'vehicle')

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

rules = [
    ctrl.Rule(passengers['low'] & terrain['flat'] & safety['low'], vehicle['xe_may']),
    ctrl.Rule(passengers['low'] & eco_friendly['high'], vehicle['xe_may_dien']),
    ctrl.Rule(terrain['flat'] & eco_friendly['high'], vehicle['xe_may_dien']),
    ctrl.Rule(passengers['medium'] | passengers['high'], vehicle['xe_oto']),
    ctrl.Rule(terrain['rough'] | terrain['moderate'], vehicle['xe_oto']),
    ctrl.Rule(safety['high'] & passengers['medium'], vehicle['xe_oto']),
    ctrl.Rule(passengers['medium'] & eco_friendly['high'], vehicle['xe_oto_dien']),
    ctrl.Rule(eco_friendly['high'] & safety['high'], vehicle['xe_oto_dien']),
]
vehicle_ctrl = ctrl.ControlSystem(rules)

pricing = {
    "XE MÁY 🏍️": {"base": 12000, "per_km": 4500, "per_min": 250},
    "XE MÁY ĐIỆN ⚡": {"base": 15000, "per_km": 5000, "per_min": 300},
    "XE Ô TÔ 🚗": {"base": 25000, "per_km": 10000, "per_min": 500},
    "XE Ô TÔ ĐIỆN ⚡🚘": {"base": 35000, "per_km": 13000, "per_min": 700},
}

def route(p1, p2):
    url = f"http://router.project-osrm.org/route/v1/driving/{p1[1]},{p1[0]};{p2[1]},{p2[0]}?overview=full&geometries=geojson"
    r = requests.get(url).json()
    route_data = r['routes'][0]
    d = route_data['distance']/1000
    t = route_data['duration']/60
    coords = [(lat, lon) for lon, lat in route_data['geometry']['coordinates']]
    return d, t, coords

# ===================== LAYOUT =====================
left_col, right_col = st.columns([1, 1.35])

with right_col:
    st.markdown("### 🗺️ Bản đồ")
    map_placeholder = st.empty()

    default_map = folium.Map(location=[10.7769, 106.7009], zoom_start=12, tiles="cartodbpositron")
    with map_placeholder:
        html(default_map._repr_html_(), height=720)

with left_col:
    st.markdown("### 📍 Nhập địa chỉ")
    col1, col2 = st.columns(2)
    with col1:
        p1_input = st.text_input("📍 Điểm đón")
    with col2:
        p2_input = st.text_input("📍 Điểm đến")

    mode = st.radio("Chọn cách đặt xe:", 
                    ["Chọn xe thủ công", "Gợi ý thông minh"], horizontal=True)

    if mode == "Chọn xe thủ công":
        vehicle_name = st.selectbox("Chọn xe", list(pricing.keys()))
    else:
        num_passengers = st.slider("👥 Người", 1, 8, 1)
        terrain_val = st.slider("🛤️ Địa hình", 0, 10, 2)
        safety_val = st.slider("🛡️ An toàn", 0, 10, 7)
        eco_val = st.slider("🌱 Eco", 0, 10, 6)
        vehicle_name = None

    if st.button("🚀 Tìm xe"):
        start = geocode(p1_input)
        end = geocode(p2_input)

        if start and end:
            d, t, coords = route(start, end)

            if not vehicle_name:
                sim = ctrl.ControlSystemSimulation(vehicle_ctrl)
                sim.input['passengers'] = num_passengers
                sim.input['terrain'] = terrain_val
                sim.input['safety'] = safety_val
                sim.input['eco_friendly'] = eco_val
                sim.compute()
                v = sim.output['vehicle']
                vehicle_name = list(pricing.keys())[int(v//3)]

            # random driver + xe cụ thể
            driver = random.choice(driver_names)
            rating = round(random.uniform(4.0, 5.0), 1)
            model = random.choice(vehicle_models[vehicle_name])

            # map mới
            m = folium.Map(location=start, zoom_start=14)
            folium.Marker(start).add_to(m)
            folium.Marker(end).add_to(m)
            folium.PolyLine(coords).add_to(m)

            with map_placeholder:
                html(m._repr_html_(), height=720)

            # UI kết quả
            st.subheader("✅ Chuyến đi của bạn")
            st.write(vehicle_name, "|", model)
            st.write(f"{round(d,2)} km - {round(t,1)} phút")

            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:10px;
                        background:#1f3a5a;padding:12px;border-radius:10px">
                <img src="https://cdn-icons-png.flaticon.com/512/149/149071.png" width="45">
                <div>
                    <b>{driver}</b><br>
                    ⭐ {rating} | {model}<br>
                    ⏱️ Xe đến sau {max(3,int(t//3))} phút
                </div>
            </div>
            """, unsafe_allow_html=True)

            price = int((pricing[vehicle_name]["base"] + d*5000)/1000)*1000
            st.success(f"Tổng tiền: {price:,} VND")
