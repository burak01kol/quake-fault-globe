import argparse, os, requests
import geopandas as gpd
import folium
from data_io import load_faults

# Veri kaynakları
GEM_URL = "https://raw.githubusercontent.com/GEMScienceTools/gem-global-active-faults/master/geojson/gem_active_faults.geojson"
GEM_LOCAL = os.path.join("data", "gem_active_faults.geojson")
NE_ADMIN1_URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_admin_1_states_provinces.geojson"
NE_ADMIN1_LOCAL = os.path.join("data", "ne_10m_admin_1_states_provinces.geojson")

TR_SENSE = {
    "dextral": "sağ yanal (right-lateral)",
    "sinistral": "sol yanal (left-lateral)",
    "normal": "normal (çekme)",
    "reverse": "ters (sıkışma)",
    "thrust": "bindirme",
    "oblique": "eğik bileşenli",
}
SLIP_COLORS = {
    "dextral": "#00E5FF",
    "sinistral": "#FF4DFF",
    "normal": "#41A5FF",
    "reverse": "#FF8A50",
    "thrust": "#FFD166",
    "oblique": "#7BFF7B",
}

def ensure_file(local_path: str, url: str, label: str, timeout=180):
    if os.path.exists(local_path):
        return local_path
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    print(f">> {label} indiriliyor...")
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    with open(local_path, "wb") as f:
        f.write(r.content)
    print(f">> {label} kaydedildi: {local_path}")
    return local_path

def parse_bbox(s: str):
    if not s: return None
    parts = [float(x.strip()) for x in s.split(",")]
    if len(parts) != 4: raise ValueError("bbox 'minLon,minLat,maxLon,maxLat' olmalı.")
    return tuple(parts)

def label_from_props(props: dict):
    name_keys = ["name", "fault_name", "FAULT_NAME", "FaultName", "segment", "SEGMENT"]
    for k in name_keys:
        v = props.get(k)
        if v not in (None, "", "nan"):
            return str(v)
    return "fault segment"

def prepare_faults_gdf(gdf: gpd.GeoDataFrame, simplify: float):
    gdf = gdf[gdf.geometry.type.isin(["LineString", "MultiLineString"])].copy()
    if simplify and simplify > 0:
        gdf["geometry"] = gdf.geometry.simplify(simplify, preserve_topology=True)
    def get_sense(row):
        v = row.get("slip_type") or row.get("sense") or ""
        return str(v).lower()
    gdf["label"] = [label_from_props(row) for _, row in gdf.iterrows()]
    gdf["slip"]  = [get_sense(row) for _, row in gdf.iterrows()]
    return gdf

def style_fault(feature):
    slip = (feature["properties"].get("slip") or "").lower()
    color = SLIP_COLORS.get(slip, "#00E5FF")
    return {"color": color, "weight": 3, "opacity": 0.9}

def highlight_fault(_feature):
    return {"weight": 6, "color": "#FFFFFF", "opacity": 1.0}

def style_province(_feature):
    return {"color": "#9aa0a6", "weight": 1, "fillOpacity": 0}

def build_map(center, zoom, theme):
    tiles = "CartoDB dark_matter" if theme == "dark" else "OpenStreetMap"
    m = folium.Map(location=center, zoom_start=zoom, tiles=tiles, control_scale=True)
    if theme == "sat":
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Esri/Maxar", name="Esri Satellite",
        ).add_to(m)
    return m

def add_tooltip_css(m):
    css = """
    <style>
      .leaflet-tooltip{
        font-size:14px; font-weight:700;
        background:rgba(0,0,0,.75); color:#fff;
        border:0; border-radius:8px; padding:6px 10px;
      }
      .leaflet-tooltip-left:before,.leaflet-tooltip-right:before{border:none;}
    </style>"""
    from folium import Element
    m.get_root().header.add_child(Element(css))

def add_legend(m):
    html = """
<div style="position: fixed; bottom: 18px; left: 18px; z-index: 9999; background: rgba(0,0,0,0.6);
color: white; padding: 10px 12px; border-radius: 8px; font-size: 12px;">
<b>Fay Kinematiği</b><br>
<span style="color:#00E5FF;">■</span> Dextral (sağ yanal)<br>
<span style="color:#FF4DFF;">■</span> Sinistral (sol yanal)<br>
<span style="color:#41A5FF;">■</span> Normal (çekme)<br>
<span style="color:#FF8A50;">■</span> Reverse (ters)<br>
<span style="color:#FFD166;">■</span> Thrust (bindirme)<br>
<span style="color:#7BFF7B;">■</span> Oblique (eğik)
</div>"""
    from folium import Element
    m.get_root().html.add_child(Element(html))

def main():
    ap = argparse.ArgumentParser(description="Fay hatlarını harita üzerinde göster")
    ap.add_argument("--faults", default="auto_global", help="'auto_global' (GEM indir) veya GeoJSON/SHP yolu")
    ap.add_argument("--provinces", default="auto", help="'auto' (Natural Earth admin-1) | 'off' | dosya yolu")
    ap.add_argument("--bbox", default=None, help="minLon,minLat,maxLon,maxLat (TR: 25,35,46,43)")
    ap.add_argument("--simplify", type=float, default=0.02, help="Basitleştirme toleransı (derece)")
    ap.add_argument("--theme", default="dark", choices=["dark","osm","sat"], help="Harita teması")
    ap.add_argument("--center", default=None, help="lat,lon (örn: '39,35')")
    ap.add_argument("--zoom", type=int, default=None, help="Başlangıç zumu")
    ap.add_argument("--out", default="map_faults.html", help="HTML çıktı adı")
    args = ap.parse_args()

    bbox = parse_bbox(args.bbox) if args.bbox else None

    # 1) Fay verisi
    faults_path = ensure_file(GEM_LOCAL, GEM_URL, "GEM Global Active Faults") if args.faults.lower()=="auto_global" else args.faults
    print(">> Faylar yükleniyor...")
    gdf_faults = load_faults(faults_path, bbox=bbox)
    gdf_faults = prepare_faults_gdf(gdf_faults, simplify=args.simplify)
    print(f"   {len(gdf_faults)} geometri hazır.")

    # 2) İl sınırları
    gdf_prov = None
    if args.provinces and args.provinces.lower() != "off":
        prov_path = ensure_file(NE_ADMIN1_LOCAL, NE_ADMIN1_URL, "Natural Earth Admin-1") if args.provinces.lower()=="auto" else args.provinces
        gdf_prov = gpd.read_file(prov_path)
        try:
            if gdf_prov.crs is not None and gdf_prov.crs.to_epsg() != 4326:
                gdf_prov = gdf_prov.to_crs(4326)
        except Exception:
            pass
        if bbox:
            minx, miny, maxx, maxy = bbox
            gdf_prov = gdf_prov.cx[minx:maxx, miny:maxy]
        if "admin" in gdf_prov.columns:
            tr = gdf_prov[gdf_prov["admin"]=="Turkey"]
            if len(tr) > 0:
                gdf_prov = tr

    # 3) merkez/zoom
    if args.center:
        lat, lon = [float(x) for x in args.center.split(",")]
        center = [lat, lon]; zoom = args.zoom or (5 if bbox else 2)
    elif bbox:
        minx, miny, maxx, maxy = bbox
        center = [(miny+maxy)/2, (minx+maxx)/2]; zoom = args.zoom or 5
    else:
        center = [20, 0]; zoom = args.zoom or 2

    m = build_map(center, zoom, theme=args.theme)
    add_tooltip_css(m)

    # İl sınırları
    if gdf_prov is not None and len(gdf_prov) > 0:
        folium.GeoJson(gdf_prov.to_json(), name="İl sınırları", style_function=style_province).add_to(m)

    # Faylar (hover + highlight)
    folium.GeoJson(
        gdf_faults.to_json(),
        name="Fay hatları",
        style_function=style_fault,
        highlight_function=highlight_fault,
        tooltip=folium.GeoJsonTooltip(
            fields=["label","slip"],
            aliases=["Fay","Kinematik"],
            sticky=True
        )
    ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    add_legend(m)

    m.save(args.out)
    print(f">> Hazır! {args.out} dosyasını tarayıcıda aç.")

if __name__ == "__main__":
    main()
