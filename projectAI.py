import streamlit as st
import requests
import folium
from streamlit.components.v1 import html
import random
from datetime import datetime
from functools import lru_cache

st.set_page_config(layout="wide", page_title="VivuXanh", initial_sidebar_state="collapsed")

# ================= CSS =================
st.markdown("""
<style>
    .main { background-color: #0a2540; }
    .grab-header {
        background: #0a2540;
        padding: 12px 16px;
        border-bottom: 1px solid #1e40af;
        color: white;
    }
    .bottom-panel {
        background: #0f3460;
        color: white;
        padding: 16px;
        border-radius: 20px 20px 0 0;
        border-top: 1px solid #1e40af;
    }

    div[data-testid="stButton"] button {
        width: 100% !important;
        height: 72px !important;
        font-size: 15px;
        font-weight: 600;
        border-radius: 12px;
        border: 2px solid #60a5fa;
        background-color: #1e90ff;
        color: white;
        transition: all 0.3s ease;
    }
    div[data-testid="stButton"] button:hover {
        background-color: #0a2540;
        border-color: #bae6fd;
        transform: scale(1.04);
    }
    div[data-testid="stButton"] button[kind="primary"] {
        background-color: #0a2540 !important;
        border: 3px solid #60a5fa !important;
        box-shadow: 0 0 12px rgba(96, 165, 250, 0.6);
    }

    button[data-testid="baseButton-secondary"] {
        background-color: #1e90ff !important;
        color: white !important;
        font-size: 18px;
        font-weight: bold;
        height: 60px !important;
        border: 2px solid #60a5fa !important;
    }

    .price-big { font-size: 32px; font-weight: 700; color: #2563eb; }
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

# ================= GEOCODE (FIX) =================
@lru_cache(maxsize=200)
def geocode(address):
    if not address or len(address.strip()) < 3:
        return None

    try:
        headers = {'User-Agent': 'VivuXanhApp/1.0'}

        params = {
            "q": address,
            "format": "json",
            "limit": 1,
            "countrycodes": "vn",
            "viewbox": "106.55,10.65,106.85,10.95",
            "bounded": 1
        }

        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params=params,
            headers=headers,
            timeout=6
        )

        data = r.json()

        if data:
            return (float(data[0]['lat']), float(data[0]['lon']))

    except Exception as e:
        print("Geocode error:", e)

    return None

# ================= ROUTE =================
def route(p1, p2):
    try:
        url = f"http://router.project-osrm.org/route/v1/driving/{p1[1]},{p1[0]};{p2[1]},{p2[0]}?overview=full&geometries=geojson"
        r = requests.get(url, timeout=8)
        data = r.json()
        if data.get('routes'):
            rd = data['routes'][0]
            d = rd['distance']/1000
            t = rd['duration']/60
            coords = [(lat, lon) for lon, lat in rd['geometry']['coordinates']]
            return d, t, coords
    except:
        pass
    return None, None, None

# ================= HEADER =================
st.markdown('<div class="grab-header"><h1 style="margin:0; font-size:28px; color:#60a5fa;">🚕 VivuXanh</h1></div>', unsafe_allow_html=True)
st.caption(f"**{datetime.now().strftime('%A, %d/%m/%Y')} • {datetime.now().strftime('%H:%M')}**")

# ================= MAP =================
map_placeholder = st.empty()
with map_placeholder:
    html(folium.Map([10.7769, 106.7009], zoom_start=13, tiles="cartodb positron")._repr_html_(), height=580)

# ================= UI =================
with st.container():
    st.markdown('<div class="bottom-panel">', unsafe_allow_html=True)

    p1_input = st.text_input("📍 Điểm đón", placeholder="Ví dụ: Chợ Bến Thành Quận 1")
    p2_input = st.text_input("🏁 Điểm đến", placeholder="Ví dụ: Landmark 81 Bình Thạnh")

    st.caption("💡 Nhập rõ địa chỉ + quận để tăng độ chính xác")

    vehicle_name = st.selectbox("🚗 Chọn phương tiện", list(pricing.keys()))

    if st.button("🚀 TÌM XE NGAY"):
        start = geocode(p1_input)
        end = geocode(p2_input)

        if not start:
            st.error("❌ Không tìm thấy điểm đón")
        elif not end:
            st.error("❌ Không tìm thấy điểm đến")
        else:
            d, t, coords = route(start, end)

            if d is None:
                st.error("❌ Không tính được tuyến đường")
            else:
                m = folium.Map(location=start, zoom_start=15, tiles="cartodb positron")

                folium.Marker(start, popup="📍 Điểm đón").add_to(m)
                folium.Marker(end, popup="🏁 Điểm đến").add_to(m)

                folium.PolyLine(coords, color="#2563eb", weight=6).add_to(m)

                html(m._repr_html_(), height=580)

                p = pricing[vehicle_name]
                price = int(p["base"] + d * p["per_km"] + t * p["per_min"])

                driver = random.choice(driver_names)
                model = random.choice(vehicle_models[vehicle_name])

                st.success("✅ Đã tìm thấy tài xế!")
                st.markdown(f"👨‍✈️ {driver} | 🚘 {model}")
                st.info(f"📏 {d:.2f} km | ⏱ {t:.1f} phút")
                st.markdown(f"<h2 class='price-big'>💰 {price:,} VND</h2>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
