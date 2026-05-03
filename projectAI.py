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

# ===================== GIÁ GIỐNG GRAB =====================
pricing = {
    "BIKE 🏍️": {"base": 10000, "per_km": 4000, "per_min": 200},
    "CAR 🚗": {"base": 20000, "per_km": 8000, "per_min": 400},
    "PREMIUM 🚘": {"base": 30000, "per_km": 12000, "per_min": 600},
}

# ===================== FUZZY HỆ SỐ =====================
factor = ctrl.Antecedent(np.arange(0, 10, 1), 'factor_input')
coef = ctrl.Consequent(np.arange(0.8, 1.6, 0.1), 'coef')

factor['low'] = fuzz.trimf(factor.universe, [0,0,5])
factor['high'] = fuzz.trimf(factor.universe, [5,10,10])

coef['normal'] = fuzz.trimf(coef.universe, [0.8,1,1.2])
coef['high'] = fuzz.trimf(coef.universe, [1.1,1.4,1.6])

rules_factor = [
    ctrl.Rule(factor['low'], coef['normal']),
    ctrl.Rule(factor['high'], coef['high']),
]

factor_ctrl = ctrl.ControlSystem(rules_factor)

# ===================== OSRM =====================
def route(p1, p2):
    url = f"http://router.project-osrm.org/route/v1/driving/{p1[1]},{p1[0]};{p2[1]},{p2[0]}?overview=full&geometries=geojson"
    r = requests.get(url).json()

    route = r['routes'][0]
    d = route['distance']/1000
    t = route['duration']/60
    coords = [(lat,lon) for lon,lat in route['geometry']['coordinates']]

    return d,t,coords

# ===================== INPUT =====================
st.markdown("### 📍 Nhập địa chỉ")
p1_input = st.text_input("Điểm đón", placeholder="Chợ Bến Thành")
p2_input = st.text_input("Điểm đến", placeholder="Landmark 81")

eco_val = st.slider("🌱 Eco",0.0,10.0,5.0)
privacy_val = st.slider("🔒 Privacy",0.0,10.0,5.0)
budget_val = st.slider("💰 Budget",0.0,100.0,50.0)

# ===================== RUN =====================
if st.button("🚀 Tìm xe"):

    start = find_place(p1_input)
    end = find_place(p2_input)

    if not start or not end:
        st.error("❌ Địa chỉ không hợp lệ")
        st.stop()

    d,t,coords = route(start,end)

    # ===== CHỌN XE =====
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

    raw_price = base + dist_cost + time_cost

    # ===== HỆ SỐ AI =====
    sim2 = ctrl.ControlSystemSimulation(factor_ctrl)
    sim2.input['factor_input'] = (eco_val + budget_val/10)
    sim2.compute()

    coef_val = sim2.output.get('coef',1)

    final_price = raw_price * coef_val

    # ===== MAP =====
    m = folium.Map(location=start, zoom_start=14)
    folium.Marker(start).add_to(m)
    folium.Marker(end).add_to(m)
    folium.PolyLine(coords,color="green",weight=6).add_to(m)

    html(m._repr_html_(),height=500)

    # ===== RESULT =====
    st.success(f"🚗 Xe: {name}")
    st.info(f"📏 {round(d,2)} km | ⏱ {round(t,1)} phút")

    st.info(f"💵 Base: {round(base/1000,1)}k")
    st.info(f"🛣️ Km: {round(dist_cost/1000,1)}k")
    st.info(f"⏱️ Time: {round(time_cost/1000,1)}k")

    st.info(f"🤖 Hệ số: x{round(coef_val,2)}")

    st.warning(f"💰 Giá cuối: {round(final_price/1000,1)}k VND")
