import streamlit as st
import requests
import folium
from streamlit.components.v1 import html
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
from geopy.geocoders import Nominatim
import time

# ===================== FUZZY 1 =====================
eco = ctrl.Antecedent(np.arange(0, 10.1, 0.1), 'eco')
privacy = ctrl.Antecedent(np.arange(0, 10.1, 0.1), 'privacy')
budget = ctrl.Antecedent(np.arange(0, 100.1, 0.1), 'budget')

vehicle_type = ctrl.Consequent(np.arange(0, 10.1, 0.1), 'vehicle_type')

eco['low'] = fuzz.trimf(eco.universe, [0,0,5])
eco['high'] = fuzz.trimf(eco.universe, [5,10,10])

privacy['low'] = fuzz.trimf(privacy.universe, [0,0,5])
privacy['high'] = fuzz.trimf(privacy.universe, [5,10,10])

budget['low'] = fuzz.trimf(budget.universe, [0,0,50])
budget['high'] = fuzz.trimf(budget.universe, [50,100,100])

vehicle_type['bike'] = fuzz.trimf(vehicle_type.universe, [0,0,4])
vehicle_type['car'] = fuzz.trimf(vehicle_type.universe, [3,5,7])
vehicle_type['premium'] = fuzz.trimf(vehicle_type.universe, [6,10,10])

rules_vehicle = [
    ctrl.Rule(budget['low'], vehicle_type['bike']),
    ctrl.Rule(privacy['high'], vehicle_type['car']),
    ctrl.Rule(budget['high'] & privacy['high'], vehicle_type['premium']),
]

vehicle_system = ctrl.ControlSystem(rules_vehicle)

# ===================== FUZZY 2 =====================
vehicle_input = ctrl.Antecedent(np.arange(0, 10.1, 0.1), 'vehicle_input')
real_distance = ctrl.Antecedent(np.arange(0, 50.1, 0.1), 'real_distance')
total_cost = ctrl.Consequent(np.arange(0, 500.1, 0.1), 'total_cost')

vehicle_input['bike'] = fuzz.trimf(vehicle_input.universe, [0,0,4])
vehicle_input['car'] = fuzz.trimf(vehicle_input.universe, [3,5,7])
vehicle_input['premium'] = fuzz.trimf(vehicle_input.universe, [6,10,10])

real_distance['near'] = fuzz.trimf(real_distance.universe, [0,0,5])
real_distance['far'] = fuzz.trimf(real_distance.universe, [5,50,50])

total_cost['low'] = fuzz.trimf(total_cost.universe, [0,0,100])
total_cost['medium'] = fuzz.trimf(total_cost.universe, [80,200,350])
total_cost['high'] = fuzz.trimf(total_cost.universe, [300,500,500])

rules_cost = [
    ctrl.Rule(vehicle_input['bike'] & real_distance['near'], total_cost['low']),
    ctrl.Rule(vehicle_input['bike'] & real_distance['far'], total_cost['medium']),
    ctrl.Rule(vehicle_input['car'] & real_distance['near'], total_cost['medium']),
    ctrl.Rule(vehicle_input['car'] & real_distance['far'], total_cost['high']),
    ctrl.Rule(vehicle_input['premium'], total_cost['high']),
]

cost_system = ctrl.ControlSystem(rules_cost)

# ===================== GEOCODE FIX 429 =====================
geolocator = Nominatim(user_agent="ride_app_ai_v2")

@st.cache_data(show_spinner=False)
def geocode(address):
    for _ in range(3):  # retry tối đa 3 lần
        try:
            time.sleep(1)  # tránh spam

            query = address + ", Ho Chi Minh, Vietnam"
            loc = geolocator.geocode(query, timeout=10)

            if loc:
                return (loc.latitude, loc.longitude)

            time.sleep(1)

            loc = geolocator.geocode(address, timeout=10)
            if loc:
                return (loc.latitude, loc.longitude)

        except Exception as e:
            if "429" in str(e):
                time.sleep(2)  # bị block thì đợi lâu hơn
            else:
                st.error(f"Lỗi geocode: {e}")
                return None

    return None

# ===================== OSRM =====================
def get_route(pickup, destination):
    url = f"http://router.project-osrm.org/route/v1/driving/{pickup[1]},{pickup[0]};{destination[1]},{destination[0]}?overview=full&geometries=geojson"

    res = requests.get(url).json()

    if "routes" in res:
        route = res['routes'][0]
        distance_km = route['distance'] / 1000
        duration_min = route['duration'] / 60

        coords = route['geometry']['coordinates']
        route_coords = [(lat, lon) for lon, lat in coords]

        return distance_km, duration_min, route_coords

    return None, None, []

# ===================== UI =====================
st.set_page_config(layout="wide")
st.title("🚕 Ride App AI (ỔN ĐỊNH - KHÔNG 429)")

eco_input = st.slider("🌱 Eco", 0.0, 10.0, 5.0)
privacy_input = st.slider("🔒 Privacy", 0.0, 10.0, 5.0)
budget_input = st.slider("💰 Budget", 0.0, 100.0, 50.0)

col1, col2 = st.columns(2)

with col1:
    pickup_address = st.text_input("📍 Điểm đón", "Đại học Kinh tế TP.HCM")

with col2:
    destination_address = st.text_input("📍 Điểm đến", "Chợ Bến Thành")

if st.button("🚀 Tìm chuyến đi"):
    pickup = geocode(pickup_address)
    destination = geocode(destination_address)

    st.write("DEBUG pickup:", pickup)
    st.write("DEBUG destination:", destination)

    if not pickup or not destination:
        st.error("❌ Không tìm được địa chỉ (đừng spam click)")
        st.stop()

    dist, time_route, route = get_route(pickup, destination)

    if dist is None:
        st.error("❌ Không tìm được đường đi")
        st.stop()

    # ===== FUZZY CHỌN XE =====
    sim_v = ctrl.ControlSystemSimulation(vehicle_system)
    sim_v.input['eco'] = eco_input
    sim_v.input['privacy'] = privacy_input
    sim_v.input['budget'] = budget_input
    sim_v.compute()

    v = sim_v.output['vehicle_type']

    if v < 4:
        best_vehicle = "BIKE 🏍️"
        v_val = 2
    elif v < 7:
        best_vehicle = "CAR 🚗"
        v_val = 5
    else:
        best_vehicle = "PREMIUM 🚘"
        v_val = 8

    st.success(f"🚗 Xe AI đề xuất: {best_vehicle}")

    # ===== FUZZY GIÁ =====
    sim_cost = ctrl.ControlSystemSimulation(cost_system)
    sim_cost.input['vehicle_input'] = v_val
    sim_cost.input['real_distance'] = dist
    sim_cost.compute()

    final_cost = sim_cost.output['total_cost']

    st.info(f"📏 {round(dist,2)} km | ⏱️ {round(time_route,1)} phút")
    st.warning(f"💰 Giá: {round(final_cost,1)}k VND")

    # ===== MAP =====
    m = folium.Map(location=pickup, zoom_start=14)

    folium.Marker(pickup, popup="Pickup").add_to(m)
    folium.Marker(destination, popup="Destination").add_to(m)

    folium.PolyLine(route, color="green", weight=6).add_to(m)

    html(m._repr_html_(), height=500)
