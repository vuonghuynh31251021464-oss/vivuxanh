import streamlit as st
import requests
import folium
from streamlit.components.v1 import html
import random
from datetime import datetime
from functools import lru_cache

st.set_page_config(layout="wide", page_title="VivuXanh")
st.title("🚕 VivuXanh")

current_time = datetime.now()
st.markdown(f"""
**📅 {current_time.strftime('%A, %d/%m/%Y')} | ⏰ {current_time.strftime('%H:%M:%S')}**
""", unsafe_allow_html=True)

# CSS
st.markdown("""
 <style> 
 div[data-testid="column"]:first-child div[data-testid="stVerticalBlock"] { 
    background-color: #1a1a2e; padding: 25px 20px; border-radius: 16px;
    border: 1px solid #2a2a40; min-height: 85vh;
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

# ================= GEOCODE (ĐÃ ĐỔI) =================
@lru_cache(maxsize=100)
def geocode(address):
    if not address:
        return None
    try:
        # Sử dụng Nominatim - tốt hơn cho địa chỉ Việt Nam
        headers = {'User-Agent': 'VivuXanhApp/1.0'}
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": address + ", Ho Chi Minh City", "format": "json", "limit": 1},
            headers=headers,
            timeout=6
        )
        data = r.json()
        if data:
            lat = float(data[0]['lat'])
            lon = float(data[0]['lon'])
            return (lat, lon)
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
        p1_input = st.text_input("Điểm đón", placeholder="Ví dụ: Bến Thành, Quận 1")
    with col2:
        p2_input = st.text_input("Điểm đến", placeholder="Ví dụ: Landmark 81, Quận Bình Thạnh")

    vehicle_name = st.selectbox("Chọn xe", list(pricing.keys()))

    st.markdown("### Tình Hình Hiện Tại")
    current_time = datetime.now()
    hour = current_time.hour
    is_peak_hour = (7 <= hour <= 9) or (17 <= hour <= 20)

    weather_options = ["☀️ Trời nắng", "⛅ Ít mây", "🌧️ Mưa nhẹ", "⛈️ Mưa to"]
    weather = random.choice(weather_options)
    weather_mult = 1.2 if "Mưa to" in weather else 1.1 if "Mưa nhẹ" in weather else 1.0

    st.info(f"**Thời tiết:** {weather}")
    st.info(f"**Giờ cao điểm:** {'🔴 Có (+30%)' if is_peak_hour else '🟢 Không'}")

    promo_code = st.text_input("🎁 Mã khuyến mãi")

    payment_method = st.selectbox("Chọn phương thức thanh toán", ["Tiền mặt", "Momo", "ZaloPay", "VNPay"])

    if st.button("🚀 Tìm xe", type="primary", use_container_width=True):
        with st.spinner("Đang tìm vị trí và tính toán..."):
            start = geocode(p1_input)
            end = geocode(p2_input)

            if not start:
                st.error(f"❌ Không tìm thấy **Điểm đón**: `{p1_input}`")
                st.info("💡 Gợi ý: Bến Thành, Quận 1 | Bitexco | Aeon Mall Tân Phú | Đại học Bách Khoa")
            elif not end:
                st.error(f"❌ Không tìm thấy **Điểm đến**: `{p2_input}`")
            else:
                d, t, coords = route(start, end)
                
                if d is None:
                    st.error("❌ Không thể tính tuyến đường. Thử lại sau.")
                else:
                    driver = random.choice(driver_names)
                    rating = round(random.uniform(4.0, 5.0), 1)
                    model = random.choice(vehicle_models[vehicle_name])

                    # Update map
                    m = folium.Map(location=start, zoom_start=14)
                    folium.Marker(start, popup="Điểm đón").add_to(m)
                    folium.Marker(end, popup="Điểm đến").add_to(m)
                    if coords:
                        folium.PolyLine(coords, color="#0066ff", weight=5, opacity=0.8).add_to(m)

                    with map_placeholder:
                        html(m._repr_html_(), height=720)

                    # Tính giá
                    p = pricing[vehicle_name]
                    price = p["base"] + d * p["per_km"] + t * p["per_min"]
                    if is_peak_hour:
                        price *= 1.3
                    price *= weather_mult
                    if promo_code.strip().upper() == "GIAM10":
                        price *= 0.9
                    price = int(price / 1000) * 1000

                    st.success("✅ Tìm thấy xe gần bạn!")
                    st.subheader("🚘 Chuyến đi của bạn")
                    st.write(f"**{vehicle_name}** | **{model}**")
                    st.write(f"📏 {round(d,2)} km — ⏱️ {round(t,1)} phút")

                    st.markdown(f"""
                    <div style="background:#16213e;padding:15px;border-radius:12px;">
                        👨‍✈️ <b>{driver}</b> &nbsp; ⭐ {rating}<br>
                        🛵 {model}<br>
                        ⏰ Xe đến sau khoảng <b>{max(3, int(t//3))} phút</b>
                    </div>
                    """, unsafe_allow_html=True)

                    st.success(f"💵 **Tổng tiền: {price:,} VND**")
                    st.info(f"💳 Thanh toán bằng: **{payment_method}**")
