<img width="2543" height="1317" alt="Ekran görüntüsü 2025-08-16 150205" src="https://github.com/user-attachments/assets/41de7939-0ef0-4472-a769-3c1aef009ef9" /># Quake Fault Globe

![Active Faults on a Black Globe](assets/cover.png)

**Active faults on a black 3D globe + interactive web map (Python).**  
Hover labels show **fault name + kinematics** (dextral / sinistral / normal / thrust / oblique).  
**Live demo:**  
- Map (index): https://burak01kol.github.io/quake-fault-globe/  
- 3D Globe: https://burak01kol.github.io/quake-fault-globe/globe.html  
- Map (direct): https://burak01kol.github.io/quake-fault-globe/map.html

> **Note:** This is **not** a hazard/forecast map. It visualizes published fault geometries from open datasets.

---

## Features
- 🌍 **3D black globe** (Plotly) with global active faults (single-trace, high-contrast)
- 🗺️ **Interactive web map** (Folium/Leaflet) with optional Admin-1 (provincial) boundaries
- 🏷️ **Hover labels**: fault **name** + **kinematics** (dextral/sinistral/…)
- ⚙️ **CLI flags** for bbox, line width/color, simplification & sampling
- 📦 **Single-file outputs**: standalone HTML and optional PNG

---

## Tech Stack
- **Python (GIS):** GeoPandas, Shapely, pyproj (CRS/WGS84, geometry ops)
- **3D & Web Viz:** Plotly (3D globe), Folium/Leaflet (tile map, tooltip, highlight)
- **Ops:** CRS management, bounding-box clipping, polyline **simplification** & **sampling**

---

## Data & Licensing
- **Faults:** GEM Global Active Faults — *CC BY-SA 4.0*  
- **Admin-1 boundaries:** Natural Earth — *Public Domain*  
Please attribute GEM and Natural Earth when sharing derivatives.

---

## Quick Start (Windows / PowerShell)

```powershell
# clone your repo
git clone https://github.com/burak01kol/quake-fault-globe.git
cd quake-fault-globe

# create & activate venv
python -m venv .venv<img width="2555" height="1309" alt="Ekran görüntüsü 2025-08-16 150327 - Kopya" src="https://github.com/user-attachments/assets/5ed17036-25df-4543-9025-77d05e36017b" />

.\.venv\Scripts\Activate.ps1

# install deps
pip install -r requirements.txt
