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

# CSS khung trái
st.markdown("""
<style>
div[data-testid="column"]:first-child div[data-testid="stVerticalBlock"] {
    background-color: #1a1a2e;
    padding: 25px 20px;
    border-radius: 16px;
    border: 1px solid #2a2a40;
    min-height: 85vh;
}
</style>
""", unsafe_allow_html=True)

# ================= DATA =================
driver_names = [
    "Nguyễn Văn Nam", "Trần Minh Tuấn", "Lê Hoàng Phúc",
    "Phạm Quốc Bảo", "Đỗ Anh Khoa", "Hoàng Minh Đức"
]

vehicle_models = {
    "XE MÁY 🏍️": ["Honda Vision", "Yamaha Sirius", "Honda Wave"],
    "XE MÁY ĐIỆN ⚡": ["VinFast Feliz", "Yadea G5"],
    "XE Ô TÔ 🚗": ["Toyota Vios", "Hyundai Accent"],
    "XE Ô TÔ ĐIỆN ⚡🚘": ["VinFast VF e34", "Tesla Model 3"]
}

pricing = {
    "XE MÁY 🏍️": {"base": 12000, "per_km": 4500, "per_min": 250},
    "XE MÁY ĐIỆN ⚡": {"base": 15000, "per_km": 5000, "per_min": 300},
    "XE Ô TÔ 🚗": {"base": 25000, "per_km": 10000, "per_min": 500},
    "XE Ô TÔ ĐIỆN ⚡🚘": {"base": 35000, "per_km": 13000, "per_min": 700},
}

# ================= GEOCODE =================
@lru_cache(maxsize=100)
def geocode(address):
    if not address:
        return None
    try:
        r = requests.get("https://photon.komoot.io/api/", params={"q": address, "limit": 1})
        data = r.json()
        if data.get("features"):
            coords = data["features"][0]["geometry"]["coordinates"]
            return (coords[1], coords[0])
    except:
        return None

def route(p1, p2):
    url = f"http://router.project-osrm.org/route/v1/driving/{p1[1]},{p1[0]};{p2[1]},{p2[0]}?overview=full&geometries=geojson"
    r = requests.get(url).json()
    route_data = r['routes'][0]
    d = route_data['distance']/1000
    t = route_data['duration']/60
    coords = [(lat, lon) for lon, lat in route_data['geometry']['coordinates']]
    return d, t, coords

# ================= LAYOUT =================
left_col, right_col = st.columns([1, 1.35])

with right_col:
    st.markdown("### 🗺️ Bản đồ")
    map_placeholder = st.empty()
    default_map = folium.Map(location=[10.7769, 106.7009], zoom_start=12)
    with map_placeholder:
        html(default_map._repr_html_(), height=720)

with left_col:
    st.markdown("### 📍 Nhập địa chỉ")
    col1, col2 = st.columns(2)
    with col1:
        p1_input = st.text_input("📍 Điểm đón")
    with col2:
        p2_input = st.text_input("📍 Điểm đến")

    vehicle_name = st.selectbox("🚗 Chọn loại xe", list(pricing.keys()))

    # Mã giảm giá
    promo_code = st.text_input("🎁 Mã khuyến mãi")

    # Thanh toán
    payment_options = {"Tiền mặt": "💵", "Momo": "📱", "ZaloPay": "💰", "VNPay": "🏦"}
    payment_method = st.selectbox("💳 Thanh toán", list(payment_options.keys()),
                                 format_func=lambda x: f"{payment_options[x]} {x}")

    if st.button("🚀 Tìm xe ngay", use_container_width=True):

        start = geocode(p1_input)
        end = geocode(p2_input)

        if start and end:
            d, t, coords = route(start, end)

            # ===== Random driver =====
            driver = random.choice(driver_names)
            rating = round(random.uniform(4.0, 5.0), 1)
            model = random.choice(vehicle_models[vehicle_name])

            # ===== Map update =====
            m = folium.Map(location=start, zoom_start=14)
            folium.Marker(start, tooltip="Điểm đón").add_to(m)
            folium.Marker(end, tooltip="Điểm đến").add_to(m)
            folium.PolyLine(coords, color="#00ff88", weight=6).add_to(m)

            with map_placeholder:
                html(m._repr_html_(), height=720)

            # ===== Price =====
            p = pricing[vehicle_name]
            price = p["base"] + d*p["per_km"] + t*p["per_min"]

            # RANDOM yếu tố
            peak_hour = random.random() < 0.3
            bad_weather = random.random() < 0.2

            extra_tags = []

            if peak_hour:
                price *= 1.3
                extra_tags.append("⏰ Giờ cao điểm +30%")

            if bad_weather:
                price *= 1.1
                extra_tags.append("🌧️ Trời mưa +10%")

            if promo_code.strip().upper() == "GIAM10":
                price *= 0.9
                extra_tags.append("🎉 Giảm giá 10%")

            price = int(price/1000)*1000

            # ===== UI =====
            st.subheader("✅ Chuyến đi của bạn")
            st.write(f"{vehicle_name} | {model}")
            st.write(f"📏 {round(d,2)} km | ⏱️ {round(t,1)} phút")

            # Driver card
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:12px;
                        background:#1f3a5a;padding:15px;border-radius:12px">
                <img src="https://cdn-icons-png.flaticon.com/512/149/149071.png" width="50">
                <div>
                    <b>{driver}</b><br>
                    ⭐ {rating} | 🚗 {model}<br>
                    ⏱️ Xe đến sau <b>{max(3,int(t//3))} phút</b>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Price
            st.success(f"💵 Tổng tiền: {price:,} VND")

            # Extra conditions
            if extra_tags:
                st.markdown(f"""
                <div style="margin-top:10px;background:#2a2a00;
                            padding:10px;border-radius:10px">
                    {' | '.join(extra_tags)}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="margin-top:10px;background:#1f2a1f;
                            padding:10px;border-radius:10px">
                    🌤️ Điều kiện bình thường
                </div>
                """, unsafe_allow_html=True)

            st.info(f"💳 Thanh toán: {payment_options[payment_method]} {payment_method}")
