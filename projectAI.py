import streamlit as st
import requests
import folium
from streamlit.components.v1 import html
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

# ===================== UI =====================
st.set_page_config(layout="wide")
st.title("🚕 VivuXanh (Grab Style)")

# ===================== GEOCODING =====================
def geocode(address):
    """Dùng Nominatim để lấy tọa độ từ địa chỉ"""
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": address, "format": "json", "limit": 1}
    headers = {"User-Agent": "vivuxanh-app"}  # Bắt buộc phải có

    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        r.raise_for_status()  # Nếu lỗi HTTP thì raise
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


# ===================== FUZZY CHỌN XE =====================
eco = ctrl.Antecedent(np.arange(0, 10.1, 0.1), 'eco')
privacy = ctrl.Antecedent(np.arange(0, 10.1, 0.1), 'privacy')
budget = ctrl.Antecedent(np.arange(0, 100.1, 0.1), 'budget')

vehicle = ctrl.Consequent(np.arange(0, 10.1, 0.1), 'vehicle')

eco['low'] = fuzz.trimf(eco.universe, [0,0,5])
eco['high'] = fuzz.trimf(eco.universe, [5,10,10])

privacy['low'] = fuzz.trimf(privacy.universe, [0,0,5])
privacy['high'] = fuzz.trimf(privacy.universe, [5,10,10])

budget['low'] = fuzz.trimf(budget.universe, [0,0,50])
budget['high'] = fuzz.trimf(budget.universe, [50,100,100])

vehicle['bike'] = fuzz.trimf(vehicle.universe, [0,0,4])
vehicle['car'] = fuzz.trimf(vehicle.universe, [3,5,7])
vehicle['premium'] = fuzz.trimf(vehicle.universe, [6,10,10])

rules = [
    ctrl.Rule(budget['low'], vehicle['bike']),
    ctrl.Rule(privacy['high'], vehicle['car']),
    ctrl.Rule(budget['high'] & privacy['high'], vehicle['premium']),
    ctrl.Rule(eco['high'] & budget['low'], vehicle['bike']),
    ctrl.Rule(eco['high'] & privacy['high'], vehicle['premium']),
]

vehicle_ctrl = ctrl.ControlSystem(rules)

# ===================== GIÁ =====================
pricing = {
    "BIKE 🏍️": {"base": 12000, "per_km": 5000, "per_min": 300},
    "CAR 🚗": {"base": 25000, "per_km": 10000, "per_min": 500},
    "PREMIUM 🚘": {"base": 40000, "per_km": 16000, "per_min": 800},
}

# ===================== OSRM =====================
def route(p1, p2):
    url = f"http://router.project-osrm.org/route/v1/driving/{p1[1]},{p1[0]};{p2[1]},{p2[0]}?overview=full&geometries=geojson"
    r = requests.get(url).json()
    route = r['routes'][0]
    d = route['distance']/1000
    t = route['duration']/60
    coords = [(lat,lon) for lon,lat in route['geometry']['coordinates']]
    return d,t,coords

# ===================== UI INPUT =====================
st.markdown("### 📍 Nhập địa chỉ bất kỳ")

col1, col2 = st.columns(2)
with col1:
    p1_input = st.text_input("📍 Điểm đón", placeholder="VD: Chợ Bến Thành, Quận 1")
with col2:
    p2_input = st.text_input("📍 Điểm đến", placeholder="VD: Landmark 81, Bình Thạnh")

eco_val = st.slider("🌱 Eco",0.0,10.0,5.0)
privacy_val = st.slider("🔒 Privacy",0.0,10.0,5.0)
budget_val = st.slider("💰 Budget",0.0,100.0,50.0)

# ===================== RUN =====================
if st.button("🚀 Tìm xe", type="primary"):
    start = geocode(p1_input)
    end = geocode(p2_input)

    if not start:
        st.error("❌ Không tìm thấy điểm đón")
        st.stop()
    if not end:
        st.error("❌ Không tìm thấy điểm đến")
        st.stop()

    d,t,coords = route(start,end)

    # ===== FUZZY =====
    sim = ctrl.ControlSystemSimulation(vehicle_ctrl)
    sim.input['eco'] = eco_val
    sim.input['privacy'] = privacy_val
    sim.input['budget'] = budget_val
    sim.compute()

    v = sim.output.get('vehicle',5)
    if v<4:
        name="BIKE 🏍️"
    elif v<7:
        name="CAR 🚗"
    else:
        name="PREMIUM 🚘"

    # ===== GIÁ =====
    p = pricing[name]
    base = p["base"]
    dist_cost = d * p["per_km"]
    time_cost = t * p["per_min"]
    final_price = base + dist_cost + time_cost

    # Làm tròn giống Grab
    final_price = int(final_price/1000)*1000

    # ===== MAP =====
    m = folium.Map(location=start, zoom_start=14, tiles="cartodbpositron")
    folium.Marker(start, popup="Pickup", icon=folium.Icon(color="green", icon="play")).add_to(m)
    folium.Marker(end, popup="Destination", icon=folium.Icon(color="red", icon="flag")).add_to(m)
    folium.PolyLine(coords,color="green",weight=6).add_to(m)
    html(m._repr_html_(),height=500)

    # ===== RESULT =====
    st.subheader("📊 Kết quả đặt xe")
    colA, colB, colC = st.columns(3)
    colA.metric("Loại xe", name)
    colB.metric("Quãng đường", f"{round(d,2)} km")
    colC.metric("Thời gian", f"{round(t,1)} phút")

    st.success(f"💰 Giá ước tính: {final_price:,} VND")
