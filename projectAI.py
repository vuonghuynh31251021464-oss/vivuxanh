import streamlit as st
import requests
import folium
from streamlit.components.v1 import html
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

# ===================== UI =====================
st.set_page_config(layout="wide")
st.title("🚕 VivuXanh")

# ===================== DATA =====================
places = {
    "Chợ Bến Thành, Quận 1": (10.772, 106.698),
    "Sân bay Tân Sơn Nhất": (10.8188, 106.6519),
    "Đại học Bách Khoa TP HCM": (10.7733, 106.6600),
    "Đại học Kinh tế TP.HCM": (10.7626, 106.6602),
    "Landmark 81, Bình Thạnh": (10.795, 106.721),
    "Bitexco Tower, Quận 1": (10.7717, 106.7041),
    "Vincom Đồng Khởi, Quận 1": (10.7798, 106.6992),
    "Aeon Mall Tân Phú": (10.8015, 106.6187),
}

# ===================== FIND ADDRESS =====================
def find_place(user_input):
    if not user_input:
        return None
    user_input = user_input.lower()
    for name, coord in places.items():
        if user_input in name.lower():
            return coord
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
    ctrl.Rule(eco['low'] & privacy['low'] & budget['low'], vehicle['bike']),
]

vehicle_ctrl = ctrl.ControlSystem(rules)

# ===================== GIÁ THEO KM =====================
price_per_km = {
    "BIKE 🏍️": 4000,     # 4k / km
    "CAR 🚗": 8000,      # 8k / km
    "PREMIUM 🚘": 12000  # 12k / km
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

# ===================== HƯỚNG DẪN =====================
st.markdown("### 📍 Nhập địa chỉ")

st.info("""
💡 Nhập đúng:
- Tên địa điểm + Quận
- VD: Chợ Bến Thành, Quận 1
- VD: Landmark 81, Bình Thạnh

❌ Tránh:
- Viết tắt (UEH)
- Thiếu thông tin
""")

col1, col2 = st.columns(2)

with col1:
    p1_input = st.text_input("📍 Điểm đón", placeholder="VD: Chợ Bến Thành")

with col2:
    p2_input = st.text_input("📍 Điểm đến", placeholder="VD: Landmark 81")

# ===================== FUZZY INPUT =====================
eco_val = st.slider("🌱 Eco",0.0,10.0,5.0)
privacy_val = st.slider("🔒 Privacy",0.0,10.0,5.0)
budget_val = st.slider("💰 Budget",0.0,100.0,50.0)

# ===================== RUN =====================
if st.button("🚀 Tìm xe"):

    start = find_place(p1_input)
    end = find_place(p2_input)

    if not start:
        st.error("❌ Sai điểm đón")
        st.stop()

    if not end:
        st.error("❌ Sai điểm đến")
        st.stop()

    d,t,coords = route(start,end)

    # ===== FUZZY CHỌN XE =====
    sim = ctrl.ControlSystemSimulation(vehicle_ctrl)
    sim.input['eco'] = eco_val
    sim.input['privacy'] = privacy_val
    sim.input['budget'] = budget_val
    sim.compute()

    v = sim.output.get('vehicle', 5)

    if v < 4:
        name="BIKE 🏍️"
    elif v < 7:
        name="CAR 🚗"
    else:
        name="PREMIUM 🚘"

    # ===== TÍNH GIÁ =====
    price = d * price_per_km[name]

    # ===== MAP =====
    m = folium.Map(location=start, zoom_start=14)
    folium.Marker(start, popup="Pickup").add_to(m)
    folium.Marker(end, popup="Destination").add_to(m)
    folium.PolyLine(coords,color="green",weight=6).add_to(m)

    html(m._repr_html_(),height=500)

    # ===== RESULT =====
    st.success(f"🚗 Xe: {name}")
    st.info(f"📏 {round(d,2)} km | ⏱ {round(t,1)} phút")
    st.warning(f"💰 Giá: {round(price/1000,1)}k VND")
