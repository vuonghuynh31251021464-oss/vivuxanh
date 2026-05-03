import streamlit as st
import requests
import folium
from streamlit.components.v1 import html
import polyline
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
from geopy.geocoders import Nominatim

# ===================== FUZZY =====================
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

rules = [
    ctrl.Rule(vehicle_input['bike'] & real_distance['near'], total_cost['low']),
    ctrl.Rule(vehicle_input['bike'] & real_distance['far'], total_cost['medium']),
    ctrl.Rule(vehicle_input['car'] & real_distance['near'], total_cost['medium']),
    ctrl.Rule(vehicle_input['car'] & real_distance['far'], total_cost['high']),
    ctrl.Rule(vehicle_input['premium'], total_cost['high']),
]

cost_system = ctrl.ControlSystem(rules)

# ===================== GEOCODE =====================
geolocator = Nominatim(user_agent="ride_app")

def geocode(address):
    try:
        loc = geolocator.geocode(address + ", Vietnam", timeout=10)
        if loc:
            return (loc.latitude, loc.longitude)
    except:
        return None
    return None

# ===================== OSRM ROUTE =====================
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
st.title("🚕 Ride App AI (FREE - OSRM Version)")

col1, col2 = st.columns(2)

with col1:
    pickup_address = st.text_input("📍 Điểm đón", "Đại học Kinh tế TP.HCM")

with col2:
    destination_address = st.text_input("📍 Điểm đến", "Chợ Bến Thành")

if st.button("🚀 Tìm chuyến đi"):
    pickup = geocode(pickup_address)
    destination = geocode(destination_address)

    if not pickup or not destination:
        st.error("❌ Không tìm được địa chỉ (hãy nhập rõ hơn)")
        st.stop()

    dist, time, route = get_route(pickup, destination)

    if dist is None:
        st.error("❌ Không tìm được đường đi")
        st.stop()

    # ===================== VEHICLES =====================
    vehicles = [
        {"name": "BIKE 🏍️", "base": 8, "per_km": 5, "val": 2},
        {"name": "CAR 🚗", "base": 15, "per_km": 8, "val": 5},
        {"name": "PREMIUM 🚘", "base": 25, "per_km": 12, "val": 8},
    ]

    st.markdown("## 🚗 Chọn loại xe")

    selected = None

    for v in vehicles:
        sim = ctrl.ControlSystemSimulation(cost_system)
        sim.input['vehicle_input'] = v["val"]
        sim.input['real_distance'] = dist
        sim.compute()

        fuzzy_price = sim.output['total_cost']
        price = v["base"] + v["per_km"] * dist + fuzzy_price

        if st.button(f"{v['name']} | {round(price,1)}k | {round(time)} phút"):
            selected = (v, price)

    # ===================== MAP =====================
    m = folium.Map(location=pickup, zoom_start=14)

    folium.Marker(pickup, popup="Pickup").add_to(m)
    folium.Marker(destination, popup="Destination").add_to(m)

    folium.PolyLine(route, color="green", weight=6).add_to(m)

    html(m._repr_html_(), height=500)

    # ===================== RESULT =====================
    if selected:
        v, price = selected
        st.success(f"🚕 Đã chọn: {v['name']}")
        st.info(f"💰 Giá: {round(price,1)}k VND")
        st.info(f"⏱️ ETA: {round(time)} phút")
