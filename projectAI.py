import streamlit as st
import requests
import folium
from streamlit.components.v1 import html
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import time
from functools import lru_cache

st.set_page_config(layout="wide", page_title="VivuXanh")
st.title("🚕 VivuXanh")

# ✅ CSS FIX KHUNG XÁM (QUAN TRỌNG)
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

if 'selected_vehicle' not in st.session_state:
    st.session_state.selected_vehicle = None

# ===================== GEOCODING =====================
@lru_cache(maxsize=100)
def geocode(address):
    if not address or str(address).strip() == "":
        return None
    try:
        url = "https://photon.komoot.io/api/"
        params = {"q": str(address).strip(), "limit": 1, "lang": "vi"}
        headers = {"User-Agent": "VivuXanh-App/1.0"}
     
        time.sleep(1.0)
        r = requests.get(url, params=params, headers=headers, timeout=15)
     
        if r.status_code == 200:
            data = r.json()
            if data.get("features") and len(data["features"]) > 0:
                coords = data["features"][0]["geometry"]["coordinates"]
                return (coords[1], coords[0])
     
        st.warning("Đang thử tìm kiếm thay thế...")
        time.sleep(1.2)
        url2 = "https://nominatim.openstreetmap.org/search"
        params2 = {"q": str(address).strip(), "format": "json", "limit": 1}
        r2 = requests.get(url2, params=params2, headers=headers, timeout=10)
     
        if r2.status_code == 200:
            data2 = r2.json()
            if data2:
                return (float(data2[0]["lat"]), float(data2[0]["lon"]))
             
        st.error(f"❌ Không tìm thấy địa chỉ: **{address}**")
        return None
     
    except Exception as e:
        st.error(f"❌ Lỗi geocoding: {e}")
        return None

# ===================== FUZZY LOGIC =====================
passengers = ctrl.Antecedent(np.arange(1, 9, 1), 'passengers')
terrain = ctrl.Antecedent(np.arange(0, 10.1, 0.1), 'terrain')
safety = ctrl.Antecedent(np.arange(0, 10.1, 0.1), 'safety')
eco_friendly = ctrl.Antecedent(np.arange(0, 10.1, 0.1), 'eco_friendly')
vehicle = ctrl.Consequent(np.arange(0, 10.1, 0.1), 'vehicle')

passengers['low'] = fuzz.trimf(passengers.universe, [1, 1, 3])
passengers['medium'] = fuzz.trimf(passengers.universe, [2, 4, 5])
passengers['high'] = fuzz.trimf(passengers.universe, [4, 7, 8])

terrain['flat'] = fuzz.trimf(terrain.universe, [0, 0, 4])
terrain['moderate'] = fuzz.trimf(terrain.universe, [3, 5, 7])
terrain['rough'] = fuzz.trimf(terrain.universe, [6, 10, 10])

safety['low'] = fuzz.trimf(safety.universe, [0, 0, 5])
safety['high'] = fuzz.trimf(safety.universe, [5, 10, 10])

eco_friendly['low'] = fuzz.trimf(eco_friendly.universe, [0, 0, 5])
eco_friendly['high'] = fuzz.trimf(eco_friendly.universe, [5, 10, 10])

vehicle['xe_may'] = fuzz.trimf(vehicle.universe, [0, 0, 3])
vehicle['xe_may_dien'] = fuzz.trimf(vehicle.universe, [2, 3.5, 5])
vehicle['xe_oto'] = fuzz.trimf(vehicle.universe, [4, 6, 8])
vehicle['xe_oto_dien'] = fuzz.trimf(vehicle.universe, [7, 10, 10])

rules = [
    ctrl.Rule(passengers['low'] & terrain['flat'] & safety['low'], vehicle['xe_may']),
    ctrl.Rule(passengers['low'] & eco_friendly['high'], vehicle['xe_may_dien']),
    ctrl.Rule(terrain['flat'] & eco_friendly['high'], vehicle['xe_may_dien']),
    ctrl.Rule(passengers['medium'] | passengers['high'], vehicle['xe_oto']),
    ctrl.Rule(terrain['rough'] | terrain['moderate'], vehicle['xe_oto']),
    ctrl.Rule(safety['high'] & passengers['medium'], vehicle['xe_oto']),
    ctrl.Rule(passengers['medium'] & eco_friendly['high'], vehicle['xe_oto_dien']),
    ctrl.Rule(eco_friendly['high'] & safety['high'], vehicle['xe_oto_dien']),
]
vehicle_ctrl = ctrl.ControlSystem(rules)

pricing = {
    "XE MÁY 🏍️": {"base": 12000, "per_km": 4500, "per_min": 250},
    "XE MÁY ĐIỆN ⚡": {"base": 15000, "per_km": 5000, "per_min": 300},
    "XE Ô TÔ 🚗": {"base": 25000, "per_km": 10000, "per_min": 500},
    "XE Ô TÔ ĐIỆN ⚡🚘": {"base": 35000, "per_km": 13000, "per_min": 700},
}

def route(p1, p2):
    url = f"http://router.project-osrm.org/route/v1/driving/{p1[1]},{p1[0]};{p2[1]},{p2[0]}?overview=full&geometries=geojson"
    r = requests.get(url).json()
    route_data = r['routes'][0]
    d = route_data['distance']/1000
    t = route_data['duration']/60
    coords = [(lat, lon) for lon, lat in route_data['geometry']['coordinates']]
    return d, t, coords

# ===================== LAYOUT =====================
left_col, right_col = st.columns([1, 1.35])

with right_col:
    st.markdown("### 🗺️ Bản đồ")
    map_placeholder = st.empty()
    default_map = folium.Map(location=[10.7769, 106.7009], zoom_start=12, tiles="cartodbpositron")
    html(default_map._repr_html_(), height=720)

with left_col:
    st.markdown("### 📍 Nhập địa chỉ")
    col1, col2 = st.columns(2)
    with col1:
        p1_input = st.text_input("📍 Điểm đón", placeholder="VD: Chợ Bến Thành, Quận 1, TP.HCM")
    with col2:
        p2_input = st.text_input("📍 Điểm đến", placeholder="VD: Landmark 81, Bình Thạnh, TP.HCM")

    mode = st.radio("Chọn cách đặt xe:", 
                    ["Chọn xe thủ công", "Tôi không biết chọn xe nào (Gợi ý thông minh)"], 
                    horizontal=True)

    if mode == "Chọn xe thủ công":
        st.markdown("#### 🚗 Chọn loại xe")
        cols = st.columns(4)
        vehicle_options = [
            ("XE MÁY 🏍️", "🏍️", "Rẻ - Nhanh"),
            ("XE MÁY ĐIỆN ⚡", "⚡", "Thân thiện môi trường"),
            ("XE Ô TÔ 🚗", "🚗", "Thoải mái"),
            ("XE Ô TÔ ĐIỆN ⚡🚘", "🚘", "Cao cấp - Xanh")
        ]
        for i, (name, icon, desc) in enumerate(vehicle_options):
            with cols[i]:
                is_selected = st.session_state.selected_vehicle == name
                if st.button(f"{icon} **{name}**\n\n{desc}", 
                            key=f"btn_{name}", 
                            use_container_width=True,
                            type="primary" if is_selected else "secondary"):
                    st.session_state.selected_vehicle = name
                    st.rerun()
        vehicle_name = st.session_state.selected_vehicle
    else:
        st.markdown("#### ⚙️ Thông số gợi ý")
        colA, colB = st.columns(2)
        with colA:
            num_passengers = st.slider("👥 Số lượng người", 1, 8, 1)
            terrain_val = st.select_slider("🛤️ Địa hình", 
                                          options=["Bằng phẳng", "Có dốc", "Gồ ghề"], 
                                          value="Bằng phẳng")
        with colB:
            safety_val = st.slider("🛡️ Độ an toàn", 0.0, 10.0, 7.0, step=0.5)
            eco_val = st.slider("🌱 Thân thiện môi trường", 0.0, 10.0, 6.0, step=0.5)
        
        terrain_map = {"Bằng phẳng": 2, "Có dốc": 6, "Gồ ghề": 9}
        vehicle_name = None

    st.markdown("### 💵 Yếu tố ảnh hưởng giá")
    col3, col4 = st.columns(2)
    with col3:
        peak_hour = st.checkbox("⏰ Giờ cao điểm (+30%)")
        bad_weather = st.checkbox("🌧️ Thời tiết xấu (+10%)")
    with col4:
        promo_code = st.text_input("🎁 Mã khuyến mãi", placeholder="GIAM10")

    st.markdown("### 💳 Phương thức thanh toán")
    payment_options = {"Tiền mặt": "💵", "Momo": "📱", "ZaloPay": "💰", "VNPay": "🏦", "Thẻ tín dụng": "💳"}
    payment_method = st.selectbox("Chọn phương thức thanh toán",
                                  options=list(payment_options.keys()),
                                  format_func=lambda x: f"{payment_options[x]} {x}")

    if st.button("🚀 Tìm xe ngay", type="primary", use_container_width=True):
        if not p1_input or not p2_input:
            st.error("Vui lòng nhập đầy đủ điểm đón và điểm đến")
        else:
            start = geocode(p1_input)
            end = geocode(p2_input)
            if start and end:
                d, t, coords = route(start, end)

                if mode == "Chọn xe thủ công":
                    if not vehicle_name:
                        st.error("Vui lòng chọn loại xe")
                    else:
                        name = vehicle_name
                else:
                    sim = ctrl.ControlSystemSimulation(vehicle_ctrl)
                    sim.input['passengers'] = num_passengers
                    sim.input['terrain'] = terrain_map[terrain_val]
                    sim.input['safety'] = safety_val
                    sim.input['eco_friendly'] = eco_val
                    sim.compute()
                    v = sim.output['vehicle']
                    if v < 3: name = "XE MÁY 🏍️"
                    elif v < 5: name = "XE MÁY ĐIỆN ⚡"
                    elif v < 7.5: name = "XE Ô TÔ 🚗"
                    else: name = "XE Ô TÔ ĐIỆN ⚡🚘"

                p = pricing[name]
                final_price = p["base"] + d * p["per_km"] + t * p["per_min"]
                if peak_hour: final_price *= 1.3
                if bad_weather: final_price *= 1.1
                if promo_code.strip().upper() == "GIAM10": final_price *= 0.9
                final_price = int(final_price / 1000) * 1000

                m = folium.Map(location=start, zoom_start=14, tiles="cartodbpositron")
                folium.Marker(start, popup="Điểm đón", icon=folium.Icon(color="green")).add_to(m)
                folium.Marker(end, popup="Điểm đến", icon=folium.Icon(color="red")).add_to(m)
                folium.PolyLine(coords, color="#00ff88", weight=6).add_to(m)
                
                with map_placeholder:
                    html(m._repr_html_(), height=720)

                st.subheader("✅ Chuyến đi của bạn")
                colA, colB, colC = st.columns(3)
                colA.metric("Loại xe", name)
                colB.metric("Quãng đường", f"{round(d,2)} km")
                colC.metric("Thời gian", f"{round(t,1)} phút")

                st.info(f"⏱️ Xe dự kiến đến sau **{max(3, int(t//3))} phút**")
                st.success(f"**Tổng tiền: {final_price:,} VND**", icon="💵")
                st.info(f"💳 **Thanh toán bằng:** {payment_options[payment_method]} **{payment_method}**")
