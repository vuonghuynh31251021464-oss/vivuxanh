import streamlit as st
import requests
import folium
from streamlit.components.v1 import html
import random
from datetime import datetime
from functools import lru_cache

st.set_page_config(layout="wide", page_title="VivuXanh", initial_sidebar_state="collapsed")

# ================= CSS - Màu xanh dương =================
st.markdown("""
<style>
    .main .block-container {
        padding-top: 0.5rem;
        padding-bottom: 0;
        max-width: 100%;
    }
    .grab-header {
        background: white;
        padding: 12px 16px;
        border-bottom: 1px solid #eee;
        position: sticky;
        top: 0;
        z-index: 100;
    }
    .bottom-panel {
        background: white;
        border-top: 1px solid #ddd;
        padding: 16px;
        border-radius: 20px 20px 0 0;
        box-shadow: 0 -4px 20px rgba(0,0,0,0.1);
        margin-top: 10px;
    }
    .price-big {
        font-size: 28px;
        font-weight: 700;
        color: #0066ff;
    }
    button[kind="primary"] {
        background-color: #0066ff !important;
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
    <h1 style="margin:0; font-size:28px; color:#0066ff;">🚕 VivuXanh</h1>
</div>
""", unsafe_allow_html=True)

current_time = datetime.now()
st.caption(f"**{current_time.strftime('%A, %d/%m/%Y')} • {current_time.strftime('%H:%M')}**")

# ================= MAP CONTAINER =================
map_placeholder = st.empty()

# Bản đồ mặc định ban đầu
def create_default_map():
    m = folium.Map(location=[10.7769, 106.7009], zoom_start=13, tiles="cartodb positron")
    return m

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

    st.markdown("**Chọn phương tiện**")
    vehicle_options = list(pricing.keys())
    vehicle_cols = st.columns(len(vehicle_options))
    
    if "selected_vehicle" not in st.session_state:
        st.session_state.selected_vehicle = vehicle_options[0]
    
    for idx, v in enumerate(vehicle_options):
        with vehicle_cols[idx]:
            if st.button(v, key=f"veh_{idx}", use_container_width=True):
                st.session_state.selected_vehicle = v
    
    vehicle_name = st.session_state.selected_vehicle

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

    # ================= NÚT TÌM XE =================
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
                    # ================= TẠO BẢN ĐỒ MỚI =================
                    m = folium.Map(location=start, zoom_start=15, tiles="cartodb positron")
                    
                    # Điểm đón & đến
                    folium.Marker(start, popup="📍 Điểm đón", icon=folium.Icon(color="blue", icon="map-marker")).add_to(m)
                    folium.Marker(end, popup="🏁 Điểm đến", icon=folium.Icon(color="red", icon="flag")).add_to(m)
                    
                    # Tuyến đường
                    if coords:
                        folium.PolyLine(coords, color="#0066ff", weight=5, opacity=0.8).add_to(m)
                    
                    # === Tài xế xung quanh (tượng trưng) ===
                    icon_color = "green" if "XE MÁY" in vehicle_name else "purple"
                    for _ in range(5):  # 5 xe ngẫu nhiên xung quanh
                        offset_lat = random.uniform(-0.015, 0.015)
                        offset_lon = random.uniform(-0.015, 0.015)
                        folium.Marker(
                            (start[0] + offset_lat, start[1] + offset_lon),
                            popup="Tài xế gần đây",
                            icon=folium.Icon(color=icon_color, icon="car" if "Ô TÔ" in vehicle_name else "motorcycle")
                        ).add_to(m)
                    
                    # === Tài xế được chọn (to hơn) ===
                    driver = random.choice(driver_names)
                    model = random.choice(vehicle_models[vehicle_name])
                    folium.Marker(
                        (start[0] + 0.003, start[1] + 0.003),
                        popup=f"👨‍✈️ {driver}\n🚘 {model}",
                        icon=folium.Icon(color="red", icon="user", prefix="fa")
                    ).add_to(m)

                    # Hiển thị map
                    with map_placeholder:
                        html(m._repr_html_(), height=580)

                    # Tính tiền
                    p = pricing[vehicle_name]
                    price = p["base"] + d * p["per_km"] + t * p["per_min"]
                    if is_peak_hour:
                        price *= 1.3
                    weather_mult = 1.2 if "Mưa to" in weather else 1.1 if "Mưa nhẹ" in weather else 1.0
                    price *= weather_mult
                    if promo_code.strip().upper() == "GIAM10":
                        price *= 0.9
                    price = int(price / 1000) * 1000

                    rating = round(random.uniform(4.3, 5.0), 1)

                    st.success("✅ Đã tìm thấy tài xế gần bạn!")
                    st.markdown(f"""
                    <div style="background:#f0f7ff; padding:16px; border-radius:12px; border:2px solid #0066ff;">
                        <b>👨‍✈️ {driver}</b> • ⭐ {rating}<br>
                        🚘 <b>{model}</b><br>
                        📏 {round(d,2)} km • ⏱️ {round(t,1)} phút<br>
                        ⏰ Xe đến sau <b>{max(3, int(t//3))} phút</b>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown(f'<h2 class="price-big">💵 {price:,} VND</h2>', unsafe_allow_html=True)
                    st.info(f"💳 Thanh toán bằng **{payment_method}**")

    st.markdown('</div>', unsafe_allow_html=True)
