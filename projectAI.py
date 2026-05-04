import streamlit as st
import requests
import folium
from streamlit.components.v1 import html
import random
from datetime import datetime
from functools import lru_cache

st.set_page_config(layout="wide", page_title="VivuXanh", initial_sidebar_state="collapsed")

# ================= CSS - DARK BLUE THEME =================
st.markdown("""
<style>
    .main {
        background-color: #0a2540;
    }
    .main .block-container {
        padding-top: 0.5rem;
        padding-bottom: 0;
        max-width: 100%;
    }
    .grab-header {
        background: #0a2540;
        padding: 12px 16px;
        border-bottom: 1px solid #1e40af;
        position: sticky;
        top: 0;
        z-index: 100;
        color: white;
    }
    .bottom-panel {
        background: #0f3460;
        color: white;
        border-top: 1px solid #1e40af;
        padding: 16px;
        border-radius: 20px 20px 0 0;
        box-shadow: 0 -4px 20px rgba(0,0,0,0.3);
        margin-top: 10px;
    }

    /* Vehicle Selection */
    .vehicle-btn {
        padding: 14px 8px;
        border-radius: 12px;
        text-align: center;
        border: 2px solid #1e40af;
        background-color: #1e40af;
        color: white;
        font-weight: 600;
        transition: all 0.3s;
        width: 100%;
    }
    .vehicle-btn:hover {
        border-color: #60a5fa;
        background-color: #1e3a8a;
    }
    .vehicle-btn.active {
        background-color: #0a2540 !important;
        border-color: #60a5fa;
        box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.4);
        transform: scale(1.06);
    }

    .stTextInput > div > div > input, .stSelectbox > div > div {
        background-color: #1e40af;
        color: white;
        border: 1px solid #60a5fa;
    }
    button[kind="primary"] {
        background-color: #0066ff;
        color: white;
    }
    .price-big {
        font-size: 32px;
        font-weight: 700;
        color: #60a5fa;
    }
    .stInfo, .stSuccess, .stError {
        background-color: #1e40af !important;
        color: white !important;
        border: 1px solid #60a5fa;
    }
</style>
""", unsafe_allow_html=True)

# ================= DATA =================
driver_names = ["Nguyễn Văn Nam", "Trần Minh Tuấn", "Lê Hoàng Phúc", "Phạm Quốc Bảo", "Đỗ Anh Khoa", "Hoàng Minh Đức"]
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

# ================= GEOCODE & ROUTE =================
@lru_cache(maxsize=100)
def geocode(address):
    if not address:
        return None
    try:
        headers = {'User-Agent': 'VivuXanhApp/1.0'}
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": address + ", Ho Chi Minh City", "format": "json", "limit": 1},
            headers=headers,
            timeout=6
        )
        data = r.json()
        if data:
            return (float(data[0]['lat']), float(data[0]['lon']))
    except:
        pass
    return None

def route(p1, p2):
    try:
        url = f"http://router.project-osrm.org/route/v1/driving/{p1[1]},{p1[0]};{p2[1]},{p2[0]}?overview=full&geometries=geojson"
        r = requests.get(url, timeout=8)
        data = r.json()
        if data.get('routes'):
            route_data = data['routes'][0]
            d = route_data['distance']/1000
            t = route_data['duration']/60
            coords = [(lat, lon) for lon, lat in route_data['geometry']['coordinates']]
            return d, t, coords
    except:
        pass
    return None, None, None

# ================= HEADER =================
st.markdown("""
<div class="grab-header">
    <h1 style="margin:0; font-size:28px; color:#60a5fa;">🚕 VivuXanh</h1>
</div>
""", unsafe_allow_html=True)

current_time = datetime.now()
st.caption(f"**{current_time.strftime('%A, %d/%m/%Y')} • {current_time.strftime('%H:%M')}**")

# ================= MAP =================
map_placeholder = st.empty()

def create_default_map():
    return folium.Map(location=[10.7769, 106.7009], zoom_start=13, tiles="cartodb dark_matter")

with map_placeholder:
    html(create_default_map()._repr_html_(), height=580)

# ================= BOTTOM PANEL =================
with st.container():
    st.markdown('<div class="bottom-panel">', unsafe_allow_html=True)
    
    col_input1, col_input2 = st.columns([1, 0.08])
    with col_input1:
        p1_input = st.text_input("📍 Điểm đón", placeholder="Nhập điểm đón", key="pickup")
        p2_input = st.text_input("🏁 Điểm đến", placeholder="Nhập điểm đến", key="dropoff")
    
    with col_input2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄", help="Đổi điểm đón và đến"):
            p1_input, p2_input = p2_input, p1_input

    # ================= CHỌN PHƯƠNG TIỆN =================
    st.markdown("**Chọn phương tiện**")
    vehicle_options = list(pricing.keys())
    
    if "selected_vehicle" not in st.session_state:
        st.session_state.selected_vehicle = vehicle_options[0]

    cols = st.columns(len(vehicle_options))
    for idx, vehicle in enumerate(vehicle_options):
        with cols[idx]:
            is_active = (vehicle == st.session_state.selected_vehicle)
            active_class = "active" if is_active else ""
            
            # HTML Button đẹp
            st.markdown(f"""
                <div class="vehicle-btn {active_class}">
                    {vehicle}
                </div>
            """, unsafe_allow_html=True)
            
            # Button ẩn để xử lý click
            if st.button(vehicle, key=f"veh_{idx}", use_container_width=True):
                st.session_state.selected_vehicle = vehicle
                st.rerun()

    vehicle_name = st.session_state.selected_vehicle

    # Thông tin khác
    col_info1, col_info2 = st.columns(2)
    with col_info1:
        hour = datetime.now().hour
        is_peak_hour = (7 <= hour <= 9) or (17 <= hour <= 20)
        st.info(f"**Giờ cao điểm:** {'🔴 Có (+30%)' if is_peak_hour else '🟢 Không'}")
    
    with col_info2:
        weather_options = ["☀️ Nắng", "⛅ Ít mây", "🌧️ Mưa nhẹ", "⛈️ Mưa to"]
        weather = random.choice(weather_options)
        st.info(f"**Thời tiết:** {weather}")

    promo_code = st.text_input("🎟️ Mã khuyến mãi (GIAM10)", placeholder="Nhập mã...")
    payment_method = st.selectbox("💳 Thanh toán", ["Tiền mặt", "Momo", "ZaloPay", "VNPay"], index=0)

    # ================= TÌM XE =================
    if st.button("🚀 TÌM XE NGAY", type="primary", use_container_width=True):
        with st.spinner("Đang tìm tài xế gần bạn..."):
            start = geocode(p1_input)
            end = geocode(p2_input)
            
            if not start:
                st.error("❌ Không tìm thấy **Điểm đón**")
            elif not end:
                st.error("❌ Không tìm thấy **Điểm đến**")
            else:
                d, t, coords = route(start, end)
                
                if d is None:
                    st.error("❌ Không tính được tuyến đường")
                else:
                    m = folium.Map(location=start, zoom_start=15, tiles="cartodb dark_matter")
                    
                    folium.Marker(start, popup="📍 Điểm đón", icon=folium.Icon(color="blue")).add_to(m)
                    folium.Marker(end, popup="🏁 Điểm đến", icon=folium.Icon(color="red")).add_to(m)
                    
                    if coords:
                        folium.PolyLine(coords, color="#60a5fa", weight=5, opacity=0.85).add_to(m)

                    # Tài xế xung quanh
                    for _ in range(5):
                        offset_lat = random.uniform(-0.012, 0.012)
                        offset_lon = random.uniform(-0.012, 0.012)
                        folium.Marker(
                            (start[0] + offset_lat, start[1] + offset_lon),
                            icon=folium.Icon(color="lightblue", icon="car" if "Ô TÔ" in vehicle_name else "motorcycle")
                        ).add_to(m)

                    # Tài xế được chọn
                    driver = random.choice(driver_names)
                    model = random.choice(vehicle_models[vehicle_name])
                    folium.Marker(
                        (start[0] + 0.004, start[1] + 0.004),
                        popup=f"{driver} - {model}",
                        icon=folium.Icon(color="red", icon="user", prefix="fa")
                    ).add_to(m)

                    with map_placeholder:
                        html(m._repr_html_(), height=580)

                    # Tính giá
                    p = pricing[vehicle_name]
                    price = p["base"] + d * p["per_km"] + t * p["per_min"]
                    if is_peak_hour: price *= 1.3
                    weather_mult = 1.2 if "Mưa to" in weather else 1.1 if "Mưa nhẹ" in weather else 1.0
                    price *= weather_mult
                    if promo_code.strip().upper() == "GIAM10":
                        price *= 0.9
                    price = int(price / 1000) * 1000

                    rating = round(random.uniform(4.3, 5.0), 1)

                    st.success("✅ Đã tìm thấy tài xế gần bạn!")
                    st.markdown(f"""
                    <div style="background:#1e40af; padding:18px; border-radius:12px; border:2px solid #60a5fa;">
                        <b>👨‍✈️ {driver}</b> • ⭐ {rating}<br>
                        🚘 <b>{model}</b><br>
                        📏 {round(d,2)} km • ⏱️ {round(t,1)} phút<br>
                        ⏰ Xe đến sau <b>{max(3, int(t//3))} phút</b>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown(f'<h2 class="price-big">💵 {price:,} VND</h2>', unsafe_allow_html=True)
                    st.info(f"💳 Thanh toán bằng **{payment_method}**")

    st.markdown('</div>', unsafe_allow_html=True)
