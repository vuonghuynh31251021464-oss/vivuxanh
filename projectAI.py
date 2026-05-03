import streamlit as st
import requests
import folium
from streamlit.components.v1 import html
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import time

# ===================== STYLE (GRAB UI) =====================
st.set_page_config(layout="wide")

st.markdown("""
<style>
body {background-color:#0e1117;}
.block-container {padding-top: 1rem;}
.card {
    background: #1c1f26;
    padding: 15px;
    border-radius: 15px;
    margin-bottom: 10px;
    color: white;
}
.big-title {
    font-size: 28px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="big-title">🚕 Grab AI (FREE)</div>', unsafe_allow_html=True)

# ===================== AUTOCOMPLETE DATA =====================
places = {
    "Chợ Bến Thành, Quận 1": (10.772, 106.698),
    "Sân bay Tân Sơn Nhất": (10.8188, 106.6519),
    "Đại học Bách Khoa TP HCM": (10.7733, 106.6600),
    "Đại học Kinh tế TP.HCM": (10.7626, 106.6602),
    "Landmark 81": (10.795, 106.721),
    "Bitexco Tower": (10.7717, 106.7041),
    "Vincom Đồng Khởi": (10.7798, 106.6992),
    "Aeon Mall Tân Phú": (10.8015, 106.6187),
}

def suggest(q):
    return [k for k in places if q.lower() in k.lower()]

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
]

vehicle_ctrl = ctrl.ControlSystem(rules)

# ===================== FUZZY GIÁ =====================
dist_input = ctrl.Antecedent(np.arange(0, 50, 1), 'dist')
veh_input = ctrl.Antecedent(np.arange(0, 10, 1), 'veh')
cost = ctrl.Consequent(np.arange(0, 500, 1), 'cost')

dist_input['near'] = fuzz.trimf(dist_input.universe, [0,0,5])
dist_input['far'] = fuzz.trimf(dist_input.universe, [5,50,50])

veh_input['bike'] = fuzz.trimf(veh_input.universe, [0,0,4])
veh_input['car'] = fuzz.trimf(veh_input.universe, [3,5,7])
veh_input['premium'] = fuzz.trimf(veh_input.universe, [6,10,10])

cost['low'] = fuzz.trimf(cost.universe, [0,0,100])
cost['mid'] = fuzz.trimf(cost.universe, [100,250,400])
cost['high'] = fuzz.trimf(cost.universe, [300,500,500])

rules2 = [
    ctrl.Rule(veh_input['bike'] & dist_input['near'], cost['low']),
    ctrl.Rule(veh_input['car'], cost['mid']),
    ctrl.Rule(veh_input['premium'], cost['high']),
]

cost_ctrl = ctrl.ControlSystem(rules2)

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
eco_val = st.slider("🌱 Eco",0.0,10.0,5.0)
privacy_val = st.slider("🔒 Privacy",0.0,10.0,5.0)
budget_val = st.slider("💰 Budget",0.0,100.0,50.0)

q1 = st.text_input("📍 Điểm đón")
p1_list = suggest(q1)
p1 = st.selectbox("Chọn điểm đón", p1_list)

q2 = st.text_input("📍 Điểm đến")
p2_list = suggest(q2)
p2 = st.selectbox("Chọn điểm đến", p2_list)

# ===================== RUN =====================
if st.button("🚀 Tìm xe"):
    start = places[p1]
    end = places[p2]

    d,t,coords = route(start,end)

    # ===== AI CHỌN XE =====
    sim = ctrl.ControlSystemSimulation(vehicle_ctrl)
    sim.input['eco'] = eco_val
    sim.input['privacy'] = privacy_val
    sim.input['budget'] = budget_val
    sim.compute()

    v = sim.output['vehicle']

    if v<4:
        name="BIKE 🏍️"; val=2
    elif v<7:
        name="CAR 🚗"; val=5
    else:
        name="PREMIUM 🚘"; val=8

    # ===== AI GIÁ =====
    sim2 = ctrl.ControlSystemSimulation(cost_ctrl)
    sim2.input['veh']=val
    sim2.input['dist']=d
    sim2.compute()

    price = sim2.output['cost']

    # ===================== MAP =====================
    m = folium.Map(location=start, zoom_start=14)
    folium.Marker(start).add_to(m)
    folium.Marker(end).add_to(m)
    folium.PolyLine(coords,color="green",weight=6).add_to(m)

    html(m._repr_html_(),height=500)

    # ===================== UI XE =====================
    st.markdown("## 🚗 Xe đề xuất")

    st.markdown(f"""
    <div class="card">
        <h3>{name}</h3>
        <p>📏 {round(d,2)} km</p>
        <p>⏱ {round(t,1)} phút</p>
        <h2>💰 {round(price,1)}k VND</h2>
    </div>
    """, unsafe_allow_html=True)
