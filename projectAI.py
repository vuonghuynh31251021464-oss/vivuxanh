import streamlit as st
import requests
import folium
from streamlit.components.v1 import html
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import datetime

# ===================== UI SETUP =====================
st.set_page_config(layout="wide", page_title="VivuXanh - Hệ thống gợi ý xe")
st.title("🚕 VivuXanh - AI Ride Suggestion")

# ===================== DỮ LIỆU ĐỊA ĐIỂM =====================
places = {
    "Chợ Bến Thành, Quận 1": (10.772, 106.698),
    "Sân bay Tân Sơn Nhất": (10.8188, 106.6519),
    "Đại học Bách Khoa TP HCM": (10.7733, 106.6600),
    "Landmark 81, Bình Thạnh": (10.795, 106.721),
}

# ===================== LOGIC MỜ (FUZZY) =====================
def create_fuzzy_system():
    eco = ctrl.Antecedent(np.arange(0, 11, 1), 'eco')
    privacy = ctrl.Antecedent(np.arange(0, 11, 1), 'privacy')
    budget = ctrl.Antecedent(np.arange(0, 101, 1), 'budget')
    vehicle = ctrl.Consequent(np.arange(0, 11, 1), 'vehicle')

    eco.automf(3) # low, medium, high
    privacy.automf(3)
    budget.automf(3)

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

# 

# ===================== TÍNH TOÁN =====================
def get_route(p1, p2):
    url = f"http://router.project-osrm.org/route/v1/driving/{p1[1]},{p1[0]};{p2[1]},{p2[0]}?overview=full&geometries=geojson"
    data = requests.get(url).json()
    route = data['routes'][0]
    return route['distance']/1000, route['duration']/60, route['geometry']['coordinates']

def calculate_price(name, dist, time):
    pricing = {
        "BIKE 🏍️": {"base": 12000, "km": 4000, "min": 200},
        "CAR 🚗": {"base": 25000, "km": 9000, "min": 500},
        "PREMIUM 🚘": {"base": 40000, "km": 15000, "min": 800},
    }
    # Surge pricing logic (giờ cao điểm 7-9h, 17-19h)
    hour = datetime.datetime.now().hour
    surge = 1.5 if (7 <= hour <= 9 or 17 <= hour <= 19) else 1.0
    
    p = pricing[name]
    total = (p["base"] + (dist * p["km"]) + (time * p["min"])) * surge
    return total, surge

# ===================== UI RENDER =====================
col1, col2 = st.columns([1, 1])

with col1:
    p1_name = st.selectbox("📍 Điểm đón", list(places.keys()))
    p2_name = st.selectbox("🏁 Điểm đến", list(places.keys()))
    
    eco_val = st.slider("🌱 Thân thiện môi trường", 0, 10, 5)
    privacy_val = st.slider("🔒 Độ riêng tư", 0, 10, 5)
    budget_val = st.slider("💰 Ngân sách (k)", 0, 100, 50)

if st.button("🚀 Gợi ý xe cho bạn"):
    sim = create_fuzzy_system()
    sim.input.update({'eco': eco_val, 'privacy': privacy_val, 'budget': budget_val})
    sim.compute()
    
    v = sim.output['vehicle']
    name = "BIKE 🏍️" if v < 4 else ("CAR 🚗" if v < 7 else "PREMIUM 🚘")
    
    dist, time, coords = get_route(places[p1_name], places[p2_name])
    price, surge = calculate_price(name, dist, time)

    # Hiển thị kết quả
    st.success(f"### Xe đề xuất: {name}")
    st.metric("Tổng giá dự kiến", f"{int(price/1000)}k VND", f"{int((surge-1)*100)}% Phụ phí giờ cao điểm" if surge > 1 else None)
    
    # Bản đồ
    m = folium.Map(location=places[p1_name], zoom_start=14)
    folium.PolyLine([(lat, lon) for lon, lat in coords], color="green", weight=5).add_to(m)
    html(m._repr_html_(), height=400)
