from pathlib import Path

import matplotlib.pyplot as plt

out = Path(__file__).parent / "perth_renewables_map.png"


points = [
    ("Emu Downs Wind", -30.53, 115.40, "wind", "80 MW"),
    ("Collgar Wind", -31.73, 118.90, "wind", "222 MW"),
    ("Albany/Grasmere Wind", -35.03, 117.80, "wind", "35.4 MW"),
    ("Emu Downs Solar", -30.53, 115.40, "solar", "20 MW"),
    ("Greenough River Solar", -28.77, 114.73, "solar", "40 MW"),
    ("Merredin Solar", -31.49, 118.28, "solar", "100 MW (developing)"),
    ("Bunbury Offshore (declared area)", -33.20, 115.35, "offshore", "Proposed / no operating MW yet"),
    (
        "Suggested Hybrid Zone (Mid West)",
        -30.90,
        115.70,
        "hybrid",
        "100 MW concept: 70% wind + 30% solar",
    ),
    ("Perth", -31.95, 115.86, "city", ""),
]

colors = {"wind": "#1f77b4", "solar": "#ff7f0e", "offshore": "#2ca02c", "hybrid": "#9467bd", "city": "#d62728"}
markers = {"wind": "o", "solar": "s", "offshore": "^", "hybrid": "D", "city": "*"}

fig, ax = plt.subplots(figsize=(12, 8), dpi=150)
ax.set_title("Existing and Proposed Renewable Energy Sites Near Perth (Schematic Map)", fontsize=14)
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.set_xlim(113.8, 119.4)
ax.set_ylim(-35.8, -27.8)
ax.grid(True, linestyle="--", alpha=0.4)

# Rough southwest WA coastline sketch (for map context)
coast_lon = [114.6, 114.7, 114.8, 114.9, 115.0, 115.1, 115.2, 115.4, 115.2, 115.1, 115.2, 115.5, 116.0, 116.7, 117.5, 118.2]
coast_lat = [-28.3, -29.0, -29.8, -30.6, -31.2, -31.8, -32.3, -32.8, -33.3, -33.8, -34.4, -34.9, -35.1, -35.2, -35.1, -34.9]
ax.plot(coast_lon, coast_lat, color="black", linewidth=1.2, label="Approx. WA coastline")

for name, lat, lon, typ, cap in points:
    ax.scatter(
        lon,
        lat,
        c=colors[typ],
        s=80 if typ != "city" else 140,
        marker=markers[typ],
        edgecolors="black",
        linewidths=0.6,
    )
    label = f"{name} ({cap})" if cap else name
    ax.text(
        lon + 0.06,
        lat + 0.06,
        label,
        fontsize=8,
        color="black",
        bbox={"boxstyle": "round,pad=0.2", "fc": "white", "ec": "none", "alpha": 0.7},
    )

for typ, label in [
    ("wind", "Onshore wind"),
    ("solar", "Solar PV"),
    ("offshore", "Offshore wind area"),
    ("hybrid", "Suggested hybrid zone (70% wind / 30% solar)"),
    ("city", "Perth"),
]:
    ax.scatter([], [], c=colors[typ], marker=markers[typ], s=80, label=label, edgecolors="black", linewidths=0.6)
ax.legend(loc="lower left", frameon=True)

plt.tight_layout()
fig.savefig(out, bbox_inches="tight")
print(f"Saved: {out}")
