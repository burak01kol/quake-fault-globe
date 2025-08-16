import argparse
import os
import requests
from shapely.geometry import LineString
from data_io import load_faults, explode_with_props, explode_lines
from globe import make_faults_globe

# Kaynaklar
GEM_URL   = "https://raw.githubusercontent.com/GEMScienceTools/gem-global-active-faults/master/geojson/gem_active_faults.geojson"
GEM_LOCAL = os.path.join("data", "gem_active_faults.geojson")
COAST_URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_coastline.geojson"
COAST_LOCAL = os.path.join("data", "ne_110m_coastline.geojson")

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

def sample_line_coords(line: LineString, step=0.03):
    pts = []
    t = 0.0
    while t <= 1.0 + 1e-9:
        p = line.interpolate(t, normalized=True)
        pts.append((float(p.y), float(p.x)))  # (lat, lon)
        t += step
    return pts

def parse_bbox(s: str):
    if not s:
        return None
    parts = [float(x.strip()) for x in s.split(",")]
    if len(parts) != 4:
        raise ValueError("bbox 'minLon,minLat,maxLon,maxLat' olmalı.")
    return tuple(parts)

def label_from_props(props: dict):
    name_keys = ["name", "fault_name", "FAULT_NAME", "FaultName", "segment", "SEGMENT"]
    for k in name_keys:
        v = props.get(k)
        if v not in (None, "", "nan"):
            return str(v)
    return "fault segment"

def main():
    ap = argparse.ArgumentParser(description="Global Faults on Black Globe")
    ap.add_argument("--faults", default="auto_global", help="'auto_global' (GEM indir) veya GeoJSON/SHP yolu")
    ap.add_argument("--coast", default="off", help="'off' | 'auto' (Natural Earth indir) | <dosya yolu>")
    ap.add_argument("--bbox", type=str, default=None, help="minLon,minLat,maxLon,maxLat (opsiyonel)")
    ap.add_argument("--simplify", type=float, default=0.02, help="Basitleştirme toleransı (derece). 0 kapatır.")
    ap.add_argument("--step", type=float, default=0.03, help="Örnekleme adımı (0.02-0.05)")
    ap.add_argument("--line_color", type=str, default="#00E5FF", help="Fay çizgi rengi")
    ap.add_argument("--line_width", type=float, default=3.5, help="Fay çizgi kalınlığı")
    ap.add_argument("--hover", action="store_true", help="Hover’da fay adını göster")
    ap.add_argument("--png", type=str, default=None, help="PNG çıktı adı (ör. faults.png) — kaleido gerekir")
    ap.add_argument("--out", type=str, default="faults_world_dark.html", help="HTML çıktı")
    args = ap.parse_args()

    bbox = parse_bbox(args.bbox) if args.bbox else None

    # FAYLAR
    faults_path = ensure_file(GEM_LOCAL, GEM_URL, "GEM Global Active Faults") if args.faults.lower() == "auto_global" else args.faults
    print(">> Faylar yükleniyor...")
    gdf_faults = load_faults(faults_path, bbox=bbox)
    if args.simplify and args.simplify > 0:
        gdf_faults["geometry"] = gdf_faults.geometry.simplify(args.simplify, preserve_topology=True)
    print(f"   {len(gdf_faults)} çizgi geometri.")

    print(">> Segmentlere ayırma + örnekleme...")
    segs = explode_with_props(gdf_faults)
    fault_segments = []
    for item in segs:
        ls = item["geometry"]; props = item["props"] or {}
        coords = sample_line_coords(ls, step=float(args.step))
        fault_segments.append({"coords": coords, "label": label_from_props(props)})

    # COAST (opsiyonel)
    coast_segments = None
    if args.coast and args.coast.lower() != "off":
        coast_path = ensure_file(COAST_LOCAL, COAST_URL, "Natural Earth coastline") if args.coast.lower()=="auto" else args.coast
        print(">> Coastline yükleniyor...")
        gdf_coast = load_faults(coast_path, bbox=bbox)
        coast_segments = [{"coords": sample_line_coords(ls, step=0.05)} for ls in explode_lines(gdf_coast)]

    print(">> Siyah küre render ediliyor...")
    fig = make_faults_globe(
        fault_segments,
        coast_segments=coast_segments,
        line_color=args.line_color,
        line_width=args.line_width,
        hover=args.hover,
        show_coast=bool(coast_segments)
    )
    fig.write_html(args.out, include_plotlyjs="cdn")
    print(f">> Hazır! HTML: {args.out}")

    if args.png:
        try:
            import plotly.io as pio
            fig.write_image(args.png, scale=2)
            print(f">> PNG kaydedildi: {args.png}")
        except Exception as e:
            print(">> PNG için 'pip install kaleido' kurmanız gerekir.")
            print(f">> Hata: {e}")

if __name__ == "__main__":
    main()
