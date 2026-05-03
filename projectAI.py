import streamlit as st
import requests
import folium
from streamlit.components.v1 import html
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import datetime

# ===================== UI STYLING =====================
st.set_page_config(page_title="VivuXanh - Đặt xe", layout="centered")
st.markdown("""
    <style>
    .stApp {background-color: #f7f7f7;}
    .main-card {background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px;}
    .stMetric {background: #f0fdf4; padding: 10px; border-radius: 10px; border: 1px solid #10b981;}
    </style>
""", unsafe_allow_html=True)

# ===================== LOGIC MỜ & DỮ LIỆU =====================
places = {
    "Chợ Bến Thành, Quận 1": (10.772, 106.698),
    "Sân bay Tân Sơn Nhất": (10.8188, 106.6519),
    "Đại học Bách Khoa TP HCM": (10.7733, 106.6600),
    "Landmark 81, Bình Thạnh": (10.795, 106.721),
}

def create_fuzzy_system():
    eco = ctrl.Antecedent(np.arange(0, 11, 1), 'eco')
    privacy = ctrl.Antecedent(np.arange(0, 11, 1), 'privacy')
    budget = ctrl.Antecedent(np.arange(0, 101, 1), 'budget')
    vehicle = ctrl.Consequent(np.arange(0, 11, 1), 'vehicle')

    eco.automf(3); privacy.automf(3); budget.automf(3)
    vehicle['bike'] = fuzz.trimf(vehicle.universe, [0, 0, 5])
    vehicle['car'] = fuzz.trimf(vehicle.universe, [3, 5, 8])
    vehicle['premium'] = fuzz.trimf(vehicle.universe, [6, 10, 10])

    rules = [
        ctrl.Rule(budget['poor'], vehicle['bike']),
        ctrl.Rule(budget['average'] & privacy['good'], vehicle['car']),
        ctrl.Rule(budget['good'] & privacy['good'], vehicle['premium']),
        ctrl.Rule(eco['good'] & budget['poor'], vehicle['bike']),
        ctrl.Rule(privacy['poor'] & budget['good'], vehicle['car'])
    ]
    return ctrl.ControlSystemSimulation(ctrl.ControlSystem(rules))

# ===================== APP UI =====================
st.title("🚕 VivuXanh")
st.markdown("### Đặt xe nhanh, giá minh bạch")

with st.container():
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        p1 = st.selectbox("📍 Điểm đón", list(places.keys()))
    with col2:
        p2 = st.selectbox("🏁 Điểm đến", list(places.keys()))
    
    eco_val = st.slider("🌱 Thân thiện môi trường", 0, 10, 5)
    privacy_val = st.slider("🔒 Độ riêng tư", 0, 10, 5)
    budget_val = st.slider("💰 Ngân sách (k)", 0, 100, 50)
    st.markdown('</div>', unsafe_allow_html=True)

if st.button("🚀 TÌM XE NGAY", use_container_width=True):
    # Tính toán Fuzzy
    sim = create_fuzzy_system()
    sim.input['eco'] = float(eco_val)
    sim.input['privacy'] = float(privacy_val)
    sim.input['budget'] = float(budget_val)
    sim.compute()
    
    v = sim.output['vehicle']
    name = "BIKE 🏍️" if v < 4 else ("CAR 🚗" if v < 7 else "PREMIUM 🚘")
    
    # Tính lộ trình (OSRM)
    start, end = places[p1], places[p2]
    url = f"http://router.project-osrm.org/route/v1/driving/{start[1]},{start[0]};{end[1]},{end[0]}?geometries=geojson"
    route = requests.get(url).json()['routes'][0]
    dist, time = route['distance']/1000, route['duration']/60
    
    # Giá
    pricing = {"BIKE 🏍️": 12000, "CAR 🚗": 25000, "PREMIUM 🚘": 40000}
    surge = 1.5 if (7 <= datetime.datetime.now().hour <= 9) else 1.0
    total = (pricing[name] + (dist * 5000) + (time * 300)) * surge

    # Hiển thị kết quả phong cách Grab
    st.success(f"### Xe gợi ý: {name}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng giá", f"{int(total/1000)}k")
    c2.metric("Quãng đường", f"{round(dist,1)} km")
    c3.metric("Thời gian", f"{int(time)} p")
    
    # Bản đồ
    m = folium.Map(location=start, zoom_start=14)
    folium.PolyLine([(lat, lon) for lon, lat in route['geometry']['coordinates']], color="#10b981", weight=6).add_to(m)
    html(m._repr_html_(), height=300)
