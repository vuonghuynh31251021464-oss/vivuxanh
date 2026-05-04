import streamlit as st
import requests
import folium
from streamlit.components.v1 import html
import random
from datetime import datetime
from functools import lru_cache

st.set_page_config(layout="wide", page_title="VivuXanh", initial_sidebar_state="collapsed")

# ================= CSS - DARK BLUE + Vehicle Selected =================
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
        padding: 12px 8px;
        border-radius: 12px;
        text-align: center;
        border: 2px solid #1e40af;
        background-color: #1e40af;
        color: white;
        font-weight: 600;
        transition: all 0.3s;
        cursor: pointer;
        width: 100%;
    }
    .vehicle-btn:hover {
        border-color: #60a5fa;
        background-color: #1e3a8a;
    }
    .vehicle-btn.active {
        background-color: #0a2540 !important;
        border-color: #60a5fa;
        box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.3);
        transform: scale(1.05);
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
    .stInfo, .stSuccess {
        background-color: #1e40af !important;
        color: white !important;
        border: 1px solid #60a5fa;
    }
</style>
""", unsafe_allow_html=True)

# ================= DATA =================
driver_names = ["Nguyễn Văn Nam", "Trần Minh Tuấn", "Lê Hoàng Phúc", "Phạm Quốc Bảo", "Đỗ Anh Khoa", "Hoàng Minh Đức"]
vehicle_models = { ... }  # giữ nguyên như cũ
pricing = { ... }        # giữ nguyên như cũ

# ================= GEOCODE & ROUTE (giữ nguyên) =================
# ... (phần geocode và route giữ nguyên)

# ================= HEADER (giữ nguyên) =================
st.markdown("""
<div class="grab-header">
    <h1 style="margin:0; font-size:28px; color:#60a5fa;">🚕 VivuXanh</h1>
</div>
""", unsafe_allow_html=True)

current_time = datetime.now()
st.caption(f"**{current_time.strftime('%A, %d/%m/%Y')} • {current_time.strftime('%H:%M')}**")

# ================= MAP (giữ nguyên) =================
map_placeholder = st.empty()

def create_default_map():
    m = folium.Map(location=[10.7769, 106.7009], zoom_start=13, tiles="cartodb dark_matter")
    return m

with map_placeholder:
    html(create_default_map()._repr_html_(), height=580)

# ================= BOTTOM PANEL =================
with st.container():
    st.markdown('<div class="bottom-panel">', unsafe_allow_html=True)
    
    # Input điểm đón / đến (giữ nguyên)
    col_input1, col_input2 = st.columns([1, 0.08])
    with col_input1:
        p1_input = st.text_input("📍 Điểm đón", placeholder="Nhập điểm đón", key="pickup")
        p2_input = st.text_input("🏁 Điểm đến", placeholder="Nhập điểm đến", key="dropoff")
    
    with col_input2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄", help="Đổi điểm đón và đến"):
            p1_input, p2_input = p2_input, p1_input

    # ================= PHẦN CHỌN PHƯƠNG TIỆN =================
    st.markdown("**Chọn phương tiện**")
    
    vehicle_options = list(pricing.keys())
    
    if "selected_vehicle" not in st.session_state:
        st.session_state.selected_vehicle = vehicle_options[0]

    # Sử dụng HTML button để kiểm soát active state tốt hơn
    cols = st.columns(len(vehicle_options))
    for idx, vehicle in enumerate(vehicle_options):
        with cols[idx]:
            is_active = vehicle == st.session_state.selected_vehicle
            active_class = "active" if is_active else ""
            
            btn_html = f"""
            <button class="vehicle-btn {active_class}" 
                    onclick="document.getElementById('veh_{idx}').click()">
                {vehicle}
            </button>
            """
            st.markdown(btn_html, unsafe_allow_html=True)
            
            # Button ẩn để xử lý logic Streamlit
            if st.button(vehicle, key=f"veh_{idx}", use_container_width=True, help=vehicle):
                st.session_state.selected_vehicle = vehicle
                st.rerun()

    vehicle_name = st.session_state.selected_vehicle

    # Phần còn lại (thời tiết, promo, nút tìm xe...) giữ nguyên như code trước
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

    # Nút tìm xe và logic sau đó giữ nguyên như bản trước...
    if st.button("🚀 TÌM XE NGAY", type="primary", use_container_width=True):
        # ... (toàn bộ logic tìm xe giữ nguyên)
        pass   # thay bằng code logic cũ của bạn

    st.markdown('</div>', unsafe_allow_html=True)
