import streamlit as st
import requests
import folium
from streamlit.components.v1 import html
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
from functools import lru_cache
import random


st.set_page_config(layout="wide", page_title="VivuXanh")
st.title("🚕 VivuXanh")

# ================= CSS =================
st.markdown("""
<style>
div[data-testid="column"]:first-child div[data-testid="stVerticalBlock"] {
    background-color: #1a1a2e;
    padding: 25px;
    border-radius: 16px;
}
</style>
""", unsafe_allow_html=True)

# ================= DATA =================
driver_names = ["Nam","Tuấn","Phúc","Bảo","Khoa"]
vehicle_models = {
    "XE MÁY 🏍️": ["Vision","Wave","Sirius"],
    "XE Ô TÔ 🚗": ["Vios","Accent","Morning"]
}
pricing = {
    "XE MÁY 🏍️": {"base":12000,"per_km":4500,"per_min":250},
    "XE Ô TÔ 🚗": {"base":25000,"per_km":10000,"per_min":500},
}

# ================= UTILS =================
def random_plate():
    return f"{random.randint(10,99)}A-{random.randint(10000,99999)}"

def random_nearby(lat, lon, r=0.01):
    return (lat + random.uniform(-r,r), lon + random.uniform(-r,r))

def distance(a,b):
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)

@lru_cache
def geocode(addr):
    try:
        r = requests.get("https://photon.komoot.io/api/", params={"q":addr,"limit":1})
        data = r.json()
        coords = data["features"][0]["geometry"]["coordinates"]
        return (coords[1], coords[0])
    except:
        return None

def route(p1,p2):
    url=f"http://router.project-osrm.org/route/v1/driving/{p1[1]},{p1[0]};{p2[1]},{p2[0]}?overview=full&geometries=geojson"
    r=requests.get(url).json()
    route=r['routes'][0]
    d=route['distance']/1000
    t=route['duration']/60
    coords=[(lat,lon) for lon,lat in route['geometry']['coordinates']]
    return d,t,coords

# ================= LAYOUT =================
left,right = st.columns([1,1.4])

with right:
    map_placeholder = st.empty()
    default_map = folium.Map(location=[10.7769,106.7009], zoom_start=12)
    with map_placeholder:
        html(default_map._repr_html_(), height=700)

with left:
    st.markdown("### 📍 Địa chỉ")
    p1 = st.text_input("Điểm đón")
    p2 = st.text_input("Điểm đến")

    vehicle = st.selectbox("🚗 Loại xe", list(pricing.keys()))
    promo = st.text_input("🎁 Mã giảm giá")

    payment_options = {"Tiền mặt":"💵","Momo":"📱","ZaloPay":"💰","VNPay":"🏦"}
    payment = st.selectbox("💳 Thanh toán", list(payment_options.keys()),
                           format_func=lambda x: f"{payment_options[x]} {x}")

    if st.button("🚀 Tìm xe", use_container_width=True):

        start = geocode(p1)
        end = geocode(p2)

        if not start or not end:
            st.error("❌ Không tìm được địa chỉ")
        else:
            d,t,coords = route(start,end)

            # ===== DRIVER POOL =====
            drivers = []
            for _ in range(6):
                pos = random_nearby(start[0],start[1])
                drivers.append({
                    "name": random.choice(driver_names),
                    "rating": round(random.uniform(4,5),1),
                    "pos": pos,
                    "plate": random_plate()
                })

            best = min(drivers, key=lambda x: distance(x["pos"], start))

            # ===== LOADING =====
            with st.spinner("🔎 Đang tìm tài xế..."):
                time.sleep(1.5)

            # ===== ANIMATION =====
            steps = 12
            lat_step = (start[0]-best["pos"][0])/steps
            lon_step = (start[1]-best["pos"][1])/steps
            pos = list(best["pos"])

            for _ in range(steps):
                pos[0]+=lat_step
                pos[1]+=lon_step

                m = folium.Map(location=start, zoom_start=14)

                for dvr in drivers:
                    folium.Marker(dvr["pos"],
                                  icon=folium.Icon(color="gray")).add_to(m)

                folium.Marker(tuple(pos),
                              icon=folium.Icon(color="blue",icon="car")).add_to(m)

                folium.Marker(start, icon=folium.Icon(color="green")).add_to(m)
                folium.Marker(end, icon=folium.Icon(color="red")).add_to(m)

                with map_placeholder:
                    html(m._repr_html_(), height=700)

                time.sleep(0.2)

            # ===== PRICE =====
            p = pricing[vehicle]
            price = p["base"] + d*p["per_km"] + t*p["per_min"]

            peak = random.random() < 0.3
            rain = random.random() < 0.2

            tags = []
            if peak:
                price *= 1.3
                tags.append("⏰ Cao điểm")
            if rain:
                price *= 1.1
                tags.append("🌧️ Mưa")
            if promo.upper() == "GIAM10":
                price *= 0.9
                tags.append("🎉 -10%")

            price = int(price/1000)*1000
            model = random.choice(vehicle_models[vehicle])

            # ===== UI =====
            st.subheader("✅ Chuyến đi của bạn")
            st.write(f"{vehicle} | {model}")
            st.write(f"📏 {round(d,2)} km | ⏱️ {round(t,1)} phút")

            st.markdown(f"""
            <div style="background:#1f3a5a;padding:15px;border-radius:12px">
            👤 <b>{best['name']}</b><br>
            ⭐ {best['rating']} | 🚗 {model}<br>
            🪪 {best['plate']}<br>
            ⏱️ Xe đã tới điểm đón
            </div>
            """, unsafe_allow_html=True)

            st.success(f"💵 Tổng tiền: {price:,} VND")

            if tags:
                st.info(" | ".join(tags))
            else:
                st.info("🌤️ Điều kiện bình thường")

            st.info(f"💳 Thanh toán: {payment_options[payment]} {payment}")
import time
import math

st.set_page_config(layout="wide", page_title="VivuXanh")
st.title("🚕 VivuXanh - Smart Ride")

# ================= CSS =================
st.markdown("""
<style>
div[data-testid="column"]:first-child div[data-testid="stVerticalBlock"] {
    background-color: #1a1a2e;
    padding: 25px 20px;
    border-radius: 16px;
}
</style>
""", unsafe_allow_html=True)

# ================= DATA =================
driver_names = ["Nam","Tuấn","Phúc","Bảo","Khoa"]
vehicle_models = {
    "XE MÁY 🏍️": ["Vision","Wave","Sirius"],
    "XE Ô TÔ 🚗": ["Vios","Accent","Morning"],
}

pricing = {
    "XE MÁY 🏍️": {"base":12000,"per_km":4500,"per_min":250},
    "XE Ô TÔ 🚗": {"base":25000,"per_km":10000,"per_min":500},
}

# ================= UTILS =================
def random_plate():
    return f"{random.randint(10,99)}A-{random.randint(10000,99999)}"

def random_nearby(lat, lon, r=0.01):
    return (lat + random.uniform(-r,r), lon + random.uniform(-r,r))

def distance(a,b):
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)

@lru_cache
def geocode(addr):
    try:
        r = requests.get("https://photon.komoot.io/api/", params={"q":addr,"limit":1})
        data = r.json()
        coords = data["features"][0]["geometry"]["coordinates"]
        return (coords[1], coords[0])
    except:
        return None

def route(p1,p2):
    url=f"http://router.project-osrm.org/route/v1/driving/{p1[1]},{p1[0]};{p2[1]},{p2[0]}?overview=full&geometries=geojson"
    r=requests.get(url).json()
    route=r['routes'][0]
    d=route['distance']/1000
    t=route['duration']/60
    coords=[(lat,lon) for lon,lat in route['geometry']['coordinates']]
    return d,t,coords

# ================= LAYOUT =================
left,right = st.columns([1,1.4])

with right:
    map_placeholder = st.empty()
    default_map = folium.Map(location=[10.7769,106.7009], zoom_start=12)
    with map_placeholder:
        html(default_map._repr_html_(), height=700)

with left:
    st.markdown("### 📍 Địa chỉ")
    p1 = st.text_input("Điểm đón")
    p2 = st.text_input("Điểm đến")

    vehicle = st.selectbox("🚗 Loại xe", list(pricing.keys()))
    promo = st.text_input("🎁 Mã giảm giá")

    payment_options = {"Tiền mặt":"💵","Momo":"📱","ZaloPay":"💰","VNPay":"🏦"}
    payment = st.selectbox("💳 Thanh toán", list(payment_options.keys()),
                           format_func=lambda x: f"{payment_options[x]} {x}")

    if st.button("🚀 Tìm xe", use_container_width=True):

        start = geocode(p1)
        end = geocode(p2)

        if not start or not end:
            st.error("❌ Không tìm được địa chỉ")
        else:
            # ===== route =====
            d,t,coords = route(start,end)

            # ===== generate driver pool =====
            drivers = []
            for _ in range(6):
                pos = random_nearby(start[0],start[1])
                drivers.append({
                    "name": random.choice(driver_names),
                    "rating": round(random.uniform(4,5),1),
                    "pos": pos,
                    "plate": random_plate()
                })

            # ===== chọn driver gần nhất =====
            best = min(drivers, key=lambda x: distance(x["pos"], start))

            # ===== loading =====
            loading = st.empty()
            for i in range(3):
                loading.info("🔎 Đang tìm tài xế" + "."*(i+1))
                time.sleep(0.6)
            loading.empty()

            # ===== animate xe di chuyển =====
            steps = 15
            lat_step = (start[0]-best["pos"][0])/steps
            lon_step = (start[1]-best["pos"][1])/steps
            pos = list(best["pos"])

            for _ in range(steps):
                pos[0]+=lat_step
                pos[1]+=lon_step

                m = folium.Map(location=start, zoom_start=14)

                # tất cả xe
                for dvr in drivers:
                    folium.Marker(dvr["pos"],
                                  icon=folium.Icon(color="gray")).add_to(m)

                # xe được chọn
                folium.Marker(tuple(pos),
                              icon=folium.Icon(color="blue",icon="car")).add_to(m)

                folium.Marker(start, icon=folium.Icon(color="green")).add_to(m)
                folium.Marker(end, icon=folium.Icon(color="red")).add_to(m)

                with map_placeholder:
                    html(m._repr_html_(), height=700)

                time.sleep(0.2)

            # ===== price =====
            p = pricing[vehicle]
            price = p["base"] + d*p["per_km"] + t*p["per_min"]

            peak = random.random() < 0.3
            rain = random.random() < 0.2

            tags = []

            if peak:
                price *= 1.3
                tags.append("⏰ Cao điểm")

            if rain:
                price *= 1.1
                tags.append("🌧️ Mưa")

            if promo.upper() == "GIAM10":
                price *= 0.9
                tags.append("🎉 -10%")

            price = int(price/1000)*1000

            model = random.choice(vehicle_models[vehicle])

            # ===== UI =====
            st.subheader("✅ Chuyến đi của bạn")
            st.write(f"{vehicle} | {model}")
            st.write(f"📏 {round(d,2)} km | ⏱️ {round(t,1)} phút")

            st.markdown(f"""
            <div style="background:#1f3a5a;padding:15px;border-radius:12px">
            👤 <b>{best['name']}</b><br>
            ⭐ {best['rating']} | 🚗 {model}<br>
            🪪 {best['plate']}<br>
            ⏱️ Xe đã tới điểm đón
            </div>
            """, unsafe_allow_html=True)

            st.success(f"💵 Tổng tiền: {price:,} VND")

            if tags:
                st.info(" | ".join(tags))
            else:
                st.info("🌤️ Điều kiện bình thường")

            st.info(f"💳 Thanh toán: {payment_options[payment]} {payment}")
