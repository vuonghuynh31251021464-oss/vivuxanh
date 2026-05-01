import streamlit as st
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import numpy as np
from geopy.distance import geodesic
import folium
import random
from streamlit.components.v1 import html

# ===== FUZZY SETUP =====
friendliness = ctrl.Antecedent(np.arange(0, 10.1, 0.1), 'friendliness')
privacy = ctrl.Antecedent(np.arange(0, 10.1, 0.1), 'privacy')
distance = ctrl.Antecedent(np.arange(0, 20.1, 0.1), 'distance')
base_cost = ctrl.Antecedent(np.arange(0, 100.1, 0.1), 'base_cost')

vehicle_type = ctrl.Consequent(np.arange(0, 10.1, 0.1), 'vehicle_type')

# Membership
friendliness['low'] = fuzz.trimf(friendliness.universe, [0,0,5])
friendliness['high'] = fuzz.trimf(friendliness.universe, [5,10,10])

privacy['low'] = fuzz.trimf(privacy.universe, [0,0,5])
privacy['high'] = fuzz.trimf(privacy.universe, [5,10,10])

distance['near'] = fuzz.trimf(distance.universe, [0,0,5])
distance['medium'] = fuzz.trimf(distance.universe, [3,10,15])
distance['far'] = fuzz.trimf(distance.universe, [10,20,20])

base_cost['low'] = fuzz.trimf(base_cost.universe, [0,0,50])
base_cost['medium'] = fuzz.trimf(base_cost.universe, [30,60,90])
base_cost['high'] = fuzz.trimf(base_cost.universe, [70,100,100])

vehicle_type['bike'] = fuzz.trimf(vehicle_type.universe, [0,0,4])
vehicle_type['car'] = fuzz.trimf(vehicle_type.universe, [3,5,7])
vehicle_type['premium'] = fuzz.trimf(vehicle_type.universe, [6,10,10])

rules = [
    ctrl.Rule(distance['near'] & base_cost['low'], vehicle_type['bike']),
    ctrl.Rule(distance['far'] & privacy['high'], vehicle_type['car']),
    ctrl.Rule(privacy['high'] & base_cost['high'], vehicle_type['premium']),
    ctrl.Rule(friendliness['high'] & distance['medium'], vehicle_type['car']),
]

system = ctrl.ControlSystem(rules)

# ===== USER LOCATION =====
user_location = (10.7769, 106.7009)

# ===== STREAMLIT UI =====
st.title("🚗 Ride App AI")

f = st.slider("Friendliness", 0.0, 10.0, 5.0)
p = st.slider("Privacy", 0.0, 10.0, 5.0)
d = st.slider("Distance (km)", 0.0, 20.0, 5.0)
c = st.slider("Budget", 0.0, 100.0, 50.0)

if st.button("Tìm xe"):
    # ===== FUZZY =====
    sim = ctrl.ControlSystemSimulation(system)
    sim.input['friendliness'] = f
    sim.input['privacy'] = p
    sim.input['distance'] = d
    sim.input['base_cost'] = c
    sim.compute()

    v = sim.output.get('vehicle_type', 5)

    if v < 4:
        best_vehicle = "BIKE 🏍️"
    elif v < 7:
        best_vehicle = "CAR 🚗"
    else:
        best_vehicle = "PREMIUM 🚘"

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

    st.success(f"Xe phù hợp: {best_vehicle}")
    st.info(f"Tài xế gần nhất: {round(best_dist,2)} km")

    # ===== MAP =====
    m = folium.Map(location=user_location, zoom_start=14)

    folium.Marker(user_location, popup="YOU").add_to(m)

    for loc, veh, dist in drivers:
        color = "green" if veh == best_vehicle else "gray"
        folium.Marker(
            loc,
            popup=f"{veh} | {round(dist,2)} km",
            icon=folium.Icon(color=color)
        ).add_to(m)

    folium.Marker(best_loc, popup="BEST", icon=folium.Icon(color='red')).add_to(m)

    html_map = m._repr_html_()
    html(html_map, height=500)
