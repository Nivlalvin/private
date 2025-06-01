# lap_time.py

import fastf1
from fastf1.plotting import setup_mpl
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# ----------------------------
# Setup: Cache & Plot Style
# ----------------------------
if not os.path.exists('./f1_cache'):
    os.makedirs('./f1_cache')

fastf1.Cache.enable_cache('./f1_cache')
setup_mpl()

# ----------------------------
# Input: Session & Drivers
# ----------------------------
year = int(input("Enter year (e.g., 2023): "))
event = input("Enter event name (e.g., Monza): ").strip()
session_type = input("Enter session type (FP1, FP2, Q, R): ").strip().upper()
driver1 = input("Enter first driver abbreviation (e.g., VER): ").strip().upper()
driver2 = input("Enter second driver abbreviation (e.g., LEC): ").strip().upper()

session = fastf1.get_session(year, event, session_type)
session.load()

# ----------------------------
# Fastest Laps & Telemetry
# ----------------------------
lap1 = session.laps.pick_driver(driver1).pick_fastest()
lap2 = session.laps.pick_driver(driver2).pick_fastest()

tel1 = lap1.get_telemetry().add_distance()
tel2 = lap2.get_telemetry().add_distance()

# Interpolate tel2 to match tel1 distance
tel2_interp = tel2.set_index('Distance').reindex(tel1['Distance']).interpolate(method='linear')

# Compute delta time
delta_time = (tel1['Time'] - tel2_interp['Time']).dt.total_seconds()

# ----------------------------
# Sector Distance Boundaries
# ----------------------------
try:
    s1_time = lap1['Sector1Time']
    s2_time = lap1['Sector2Time']
    s3_time = lap1['Sector3Time']

    sector1_end_time = lap1['LapStartTime'] + s1_time
    sector2_end_time = sector1_end_time + s2_time

    tel1_time = tel1[['Time', 'Distance']].copy()
    sector1_dist = tel1_time[tel1_time['Time'] >= sector1_end_time].iloc[0]['Distance']
    sector2_dist = tel1_time[tel1_time['Time'] >= sector2_end_time].iloc[0]['Distance']
except Exception as e:
    print(f"[!] Warning: Could not extract sector distances. Reason: {e}")
    sector1_dist = sector2_dist = None

# ----------------------------
# Plot: Speed Trace
# ----------------------------
plt.figure(figsize=(12, 6))
plt.plot(tel1['Distance'], tel1['Speed'], label=driver1, color='red')
plt.plot(tel2['Distance'], tel2['Speed'], label=driver2, color='blue')
plt.title(f"Speed Trace Comparison - {driver1} vs {driver2} ({event} {year})")
plt.xlabel("Distance (m)")
plt.ylabel("Speed (km/h)")
plt.grid(True)
plt.legend()

# Draw sector lines
if sector1_dist and sector2_dist:
    plt.axvline(x=sector1_dist, color='white', linestyle='--', alpha=0.6, label='Sector 1 End')
    plt.axvline(x=sector2_dist, color='gray', linestyle='--', alpha=0.6, label='Sector 2 End')
    plt.text(sector1_dist + 20, 100, 'S1 End', color='white')
    plt.text(sector2_dist + 20, 100, 'S2 End', color='gray')

plt.tight_layout()
plt.show()

# ----------------------------
# Plot: Delta Time
# ----------------------------
plt.figure(figsize=(12, 6))
plt.plot(tel1['Distance'], delta_time, color='purple', label=f'{driver1} vs {driver2}')
plt.axhline(0, linestyle='--', color='black', linewidth=1)
plt.title(f"Delta Time Over Lap Distance - {driver1} vs {driver2}")
plt.xlabel("Distance (m)")
plt.ylabel("Time Delta (s)")
plt.grid(True)
plt.legend()

# Draw sector lines on delta plot
if sector1_dist and sector2_dist:
    plt.axvline(x=sector1_dist, color='white', linestyle='--', alpha=0.6)
    plt.axvline(x=sector2_dist, color='gray', linestyle='--', alpha=0.6)
    plt.text(sector1_dist + 20, 0.05, 'S1 End', color='white')
    plt.text(sector2_dist + 20, 0.05, 'S2 End', color='gray')

plt.tight_layout()
plt.show()

# ----------------------------
# Plot: Sector Time Comparison
# ----------------------------
sector_times = {
    'Sector': ['Sector 1', 'Sector 2', 'Sector 3'],
    driver1: [
        lap1['Sector1Time'].total_seconds(),
        lap1['Sector2Time'].total_seconds(),
        lap1['Sector3Time'].total_seconds()
    ],
    driver2: [
        lap2['Sector1Time'].total_seconds(),
        lap2['Sector2Time'].total_seconds(),
        lap2['Sector3Time'].total_seconds()
    ]
}

sector_df = pd.DataFrame(sector_times)
sector_df_melted = sector_df.melt(id_vars='Sector', var_name='Driver', value_name='Time (s)')

plt.figure(figsize=(8, 6))
sns.barplot(data=sector_df_melted, x='Sector', y='Time (s)', hue='Driver', palette=['red', 'blue'])
plt.title(f"Sector Time Comparison - {driver1} vs {driver2} ({event} {year})")
plt.ylabel("Time (s)")
plt.grid(True, axis='y')
plt.tight_layout()
plt.show()
