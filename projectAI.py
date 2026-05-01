git init
git add .
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/USERNAME/ride-app.git
git push -u origin main

import skfuzzy as fuzz
from skfuzzy import control as ctrl
import numpy as np
from geopy.distance import geodesic
import folium
import random
import tkinter as tk
from tkinter import messagebox
import webview

# ===== FUZZY SETUP =====
friendliness = ctrl.Antecedent(np.arange(0, 10.1, 0.1), 'friendliness')
privacy = ctrl.Antecedent(np.arange(0, 10.1, 0.1), 'privacy')
distance = ctrl.Antecedent(np.arange(0, 20.1, 0.1), 'distance')
base_cost = ctrl.Antecedent(np.arange(0, 100.1, 0.1), 'base_cost')

vehicle_type = ctrl.Consequent(np.arange(0, 10.1, 0.1), 'vehicle_type')

# Membership
friendliness['low'] = fuzz.trimf(friendliness.universe, [0,0,5])
friendliness['high'] = fuzz.trimf(friendliness.universe, [5,10,10])

privacy['low'] = fuzz.trimf(privacy.universe, [0,0,5])
privacy['high'] = fuzz.trimf(privacy.universe, [5,10,10])

distance['near'] = fuzz.trimf(distance.universe, [0,0,5])
distance['medium'] = fuzz.trimf(distance.universe, [3,10,15])
distance['far'] = fuzz.trimf(distance.universe, [10,20,20])

base_cost['low'] = fuzz.trimf(base_cost.universe, [0,0,50])
base_cost['medium'] = fuzz.trimf(base_cost.universe, [30,60,90])
base_cost['high'] = fuzz.trimf(base_cost.universe, [70,100,100])

vehicle_type['bike'] = fuzz.trimf(vehicle_type.universe, [0,0,4])
vehicle_type['car'] = fuzz.trimf(vehicle_type.universe, [3,5,7])
vehicle_type['premium'] = fuzz.trimf(vehicle_type.universe, [6,10,10])

rules = [
    ctrl.Rule(distance['near'] & base_cost['low'], vehicle_type['bike']),
    ctrl.Rule(distance['far'] & privacy['high'], vehicle_type['car']),
    ctrl.Rule(privacy['high'] & base_cost['high'], vehicle_type['premium']),
    ctrl.Rule(friendliness['high'] & distance['medium'], vehicle_type['car']),
]

system = ctrl.ControlSystem(rules)

# ===== USER LOCATION =====
user_location = (10.7769, 106.7009)

# ===== GLOBAL WINDOW =====
map_window = None

# ===== MAIN FUNCTION =====
def find_driver():
    global map_window

    try:
        f = float(entry_friend.get())
        p = float(entry_privacy.get())
        d = float(entry_distance.get())
        c = float(entry_cost.get())
    except:
        messagebox.showerror("Lỗi", "Nhập số hợp lệ!")
        return

    # ===== FUZZY =====
    sim = ctrl.ControlSystemSimulation(system)
    sim.input['friendliness'] = f
    sim.input['privacy'] = p
    sim.input['distance'] = d
    sim.input['base_cost'] = c
    sim.compute()

    v = sim.output['vehicle_type']

    if v < 4:
        best_vehicle = "BIKE 🏍️"
    elif v < 7:
        best_vehicle = "CAR 🚗"
    else:
        best_vehicle = "PREMIUM 🚘"

    # ===== RANDOM DRIVER =====
    vehicle_list = ["BIKE 🏍️", "CAR 🚗", "PREMIUM 🚘"]
    drivers = []

    for _ in range(8):
        loc = (user_location[0] + random.uniform(-0.02, 0.02),
               user_location[1] + random.uniform(-0.02, 0.02))
        veh = random.choice(vehicle_list)
        dist = geodesic(user_location, loc).km
        drivers.append((loc, veh, dist))

    # ===== CHỌN DRIVER =====
    filtered = [x for x in drivers if x[1] == best_vehicle]
    if not filtered:
        filtered = drivers

    best = min(filtered, key=lambda x: x[2])
    best_loc, best_v, best_dist = best

    result_label.config(
        text=f"Xe phù hợp: {best_vehicle}\nTài xế gần nhất: {round(best_dist,2)} km"
    )

    # ===== MAP =====
    m = folium.Map(location=user_location, zoom_start=14)

    folium.Marker(user_location, popup="YOU").add_to(m)

    for loc, veh, dist in drivers:
        color = "green" if veh == best_vehicle else "gray"

        folium.Marker(
            loc,
            popup=f"{veh} | {round(dist,2)} km",
            icon=folium.Icon(color=color)
        ).add_to(m)

    folium.Marker(
        best_loc,
        popup="BEST",
        icon=folium.Icon(color='red')
    ).add_to(m)

    html = m.get_root().render()

    # ===== HIỂN THỊ MAP (KHÔNG 404) =====
    if map_window is None:
        map_window = webview.create_window("Map", html=html, width=800, height=600)
        webview.start()
    else:
        map_window.load_html(html)

# ===== TKINTER UI =====
root = tk.Tk()
root.title("Ride App 🚗")
root.geometry("400x400")

tk.Label(root, text="Friendliness (0-10)").pack()
entry_friend = tk.Entry(root)
entry_friend.pack()

tk.Label(root, text="Privacy (0-10)").pack()
entry_privacy = tk.Entry(root)
entry_privacy.pack()

tk.Label(root, text="Distance (km)").pack()
entry_distance = tk.Entry(root)
entry_distance.pack()

tk.Label(root, text="Budget (0-100)").pack()
entry_cost = tk.Entry(root)
entry_cost.pack()

tk.Button(root, text="Tìm xe", command=find_driver).pack(pady=10)

result_label = tk.Label(root, text="Kết quả sẽ hiển thị ở đây", fg="blue")
result_label.pack()

root.mainloop()
