import streamlit as st
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import numpy as np
from geopy.distance import geodesic
import folium
import random
from streamlit.components.v1 import html

# ===================== FUZZY 1: CHỌN XE =====================

eco = ctrl.Antecedent(np.arange(0, 10.1, 0.1), 'eco')
privacy = ctrl.Antecedent(np.arange(0, 10.1, 0.1), 'privacy')
distance = ctrl.Antecedent(np.arange(0, 20.1, 0.1), 'distance')
base_cost = ctrl.Antecedent(np.arange(0, 100.1, 0.1), 'base_cost')

vehicle_type = ctrl.Consequent(np.arange(0, 10.1, 0.1), 'vehicle_type')

# Membership
eco['low'] = fuzz.trimf(eco.universe, [0, 0, 5])
eco['high'] = fuzz.trimf(eco.universe, [5, 10, 10])

privacy['low'] = fuzz.trimf(privacy.universe, [0, 0, 5])
privacy['high'] = fuzz.trimf(privacy.universe, [5, 10, 10])

distance['near'] = fuzz.trimf(distance.universe, [0, 0, 5])
distance['medium'] = fuzz.trimf(distance.universe, [3, 10, 15])
distance['far'] = fuzz.trimf(distance.universe, [10, 20, 20])

base_cost['low'] = fuzz.trimf(base_cost.universe, [0, 0, 50])
base_cost['medium'] = fuzz.trimf(base_cost.universe, [30, 60, 90])
base_cost['high'] = fuzz.trimf(base_cost.universe, [70, 100, 100])

vehicle_type['bike'] = fuzz.trimf(vehicle_type.universe, [0, 0, 4])
vehicle_type['car'] = fuzz.trimf(vehicle_type.universe, [3, 5, 7])
vehicle_type['premium'] = fuzz.trimf(vehicle_type.universe, [6, 10, 10])

rules = [
    ctrl.Rule(distance['near'] & base_cost['low'], vehicle_type['bike']),
    ctrl.Rule(distance['far'] & privacy['high'], vehicle_type['car']),
    ctrl.Rule(privacy['high'] & base_cost['high'], vehicle_type['premium']),
    ctrl.Rule(eco['high'] & distance['near'], vehicle_type['bike']),
]

system = ctrl.ControlSystem(rules)

# ===================== FUZZY 2: TÍNH GIÁ =====================

vehicle_input = ctrl.Antecedent(np.arange(0, 10.1, 0.1), 'vehicle_input')
real_distance = ctrl.Antecedent(np.arange(0, 20.1, 0.1), 'real_distance')

total_cost = ctrl.Consequent(np.arange(0, 200.1, 0.1), 'total_cost')

vehicle_input['bike'] = fuzz.trimf(vehicle_input.universe, [0, 0, 4])
vehicle_input['car'] = fuzz.trimf(vehicle_input.universe, [3, 5, 7])
vehicle_input['premium'] = fuzz.trimf(vehicle_input.universe, [6, 10, 10])

real_distance['near'] = fuzz.trimf(real_distance.universe, [0, 0, 5])
real_distance['far'] = fuzz.trimf(real_distance.universe, [5, 20, 20])

total_cost['low'] = fuzz.trimf(total_cost.universe, [0, 0, 80])
total_cost['medium'] = fuzz.trimf(total_cost.universe, [50, 100, 150])
total_cost['high'] = fuzz.trimf(total_cost.universe, [120, 200, 200])

rules_cost = [
    ctrl.Rule(vehicle_input['bike'] & real_distance['near'], total_cost['low']),
    ctrl.Rule(vehicle_input['bike'] & real_distance['far'], total_cost['medium']),
    ctrl.Rule(vehicle_input['car'] & real_distance['near'], total_cost['medium']),
    ctrl.Rule(vehicle_input['car'] & real_distance['far'], total_cost['high']),
    ctrl.Rule(vehicle_input['premium'], total_cost['high']),
]

cost_system = ctrl.ControlSystem(rules_cost)

# ===================== USER LOCATION =====================
user_location = (10.7769, 106.7009)

# ===================== UI =====================
st.title("🚗 Ride App AI (Fuzzy Logic)")

eco_input = st.slider("Eco Friendly", 0.0, 10.0, 5.0)
privacy_input = st.slider("Privacy", 0.0, 10.0, 5.0)
distance_input = st.slider("Distance (estimate)", 0.0, 20.0, 5.0)
budget_input = st.slider("Budget", 0.0, 100.0, 50.0)

st.markdown("### 📍 Chọn điểm đón và điểm đến (demo)")
pickup = st.text_input("Pickup (lat,lon)", "10.7769,106.7009")
destination = st.text_input("Destination (lat,lon)", "10.78,106.68")

if st.button("🚀 Tìm xe"):
    # ===== FUZZY 1 =====
    sim = ctrl.ControlSystemSimulation(system)
    sim.input['eco'] = eco_input
    sim.input['privacy'] = privacy_input
    sim.input['distance'] = distance_input
    sim.input['base_cost'] = budget_input
    sim.compute()

    v = sim.output.get('vehicle_type', 5)

    if v < 4:
        best_vehicle = "BIKE 🏍️"
        v_val = 2
    elif v < 7:
        best_vehicle = "CAR 🚗"
        v_val = 5
    else:
        best_vehicle = "PREMIUM 🚘"
        v_val = 8

    # ===== PARSE TOẠ ĐỘ =====
    pickup = tuple(map(float, pickup.split(",")))
    destination = tuple(map(float, destination.split(",")))

    real_dist = geodesic(pickup, destination).km

    # ===== RANDOM DRIVER =====
    vehicle_list = ["BIKE 🏍️", "CAR 🚗", "PREMIUM 🚘"]
    drivers = []

    for _ in range(8):
        loc = (user_location[0] + random.uniform(-0.02, 0.02),
               user_location[1] + random.uniform(-0.02, 0.02))
        veh = random.choice(vehicle_list)
        dist = geodesic(user_location, loc).km
        drivers.append((loc, veh, dist))

    filtered = [x for x in drivers if x[1] == best_vehicle]
    if not filtered:
        filtered = drivers

    best = min(filtered, key=lambda x: x[2])
    best_loc, best_v, best_dist = best

    # ===== FUZZY 2 =====
    cost_sim = ctrl.ControlSystemSimulation(cost_system)
    cost_sim.input['vehicle_input'] = v_val
    cost_sim.input['real_distance'] = real_dist
    cost_sim.compute()

    final_cost = cost_sim.output['total_cost']

    # ===== OUTPUT =====
    st.success(f"🚗 Xe phù hợp: {best_vehicle}")
    st.info(f"📏 Quãng đường: {round(real_dist,2)} km")
    st.warning(f"💰 Giá dự đoán: {round(final_cost,2)} VND")
    st.info(f"👤 Tài xế gần nhất: {round(best_dist,2)} km")

    # ===== MAP =====
    m = folium.Map(location=user_location, zoom_start=14)

    folium.Marker(pickup, popup="Pickup").add_to(m)
    folium.Marker(destination, popup="Destination").add_to(m)

    folium.PolyLine([pickup, destination], color="blue").add_to(m)

    for loc, veh, dist in drivers:
        color = "green" if veh == best_vehicle else "gray"
        folium.Marker(
            loc,
            popup=f"{veh} | {round(dist,2)} km",
            icon=folium.Icon(color=color)
        ).add_to(m)

    folium.Marker(best_loc, popup="BEST DRIVER", icon=folium.Icon(color='red')).add_to(m)

    html(m._repr_html_(), height=500)
