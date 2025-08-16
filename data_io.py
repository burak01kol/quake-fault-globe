import geopandas as gpd
import pandas as pd
import requests

def load_faults(path: str, bbox=None):
    """
    GeoJSON/SHP fay verisini yükler. EPSG:4326 bekler; değilse dönüştürür.
    bbox: (minLon, minLat, maxLon, maxLat)
    """
    gdf = gpd.read_file(path)

    try:
        if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs(epsg=4326)
    except Exception:
        pass

    gdf = gdf[gdf.geometry.type.isin(["LineString", "MultiLineString"])]

    if bbox:
        minx, miny, maxx, maxy = bbox
        gdf = gdf.cx[minx:maxx, miny:maxy]

    return gdf

def fetch_earthquakes(days=30, minmag=3.0, bbox=None):
    """USGS FDSN API – kullanılmıyor ama elde dursun."""
    base = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    params = {
        "format": "geojson",
        "orderby": "time",
        "minmagnitude": float(minmag),
        "limit": 20000
    }
    params["starttime"] = (pd.Timestamp.utcnow() - pd.Timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    params["endtime"]   = pd.Timestamp.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    if bbox:
        minx, miny, maxx, maxy = bbox
        params.update({
            "minlatitude": miny, "minlongitude": minx,
            "maxlatitude": maxy, "maxlongitude": maxx
        })

    r = requests.get(base, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()

    rows = []
    for f in data.get("features", []):
        props = f.get("properties", {})
        geom = f.get("geometry", {})
        if not geom or geom.get("type") != "Point":
            continue
        lon, lat = geom.get("coordinates", [None, None])[:2]
        if lon is None or lat is None:
            continue
        rows.append({
            "time": pd.to_datetime(props.get("time"), unit="ms", utc=True),
            "mag": props.get("mag"),
            "place": props.get("place"),
            "lon": float(lon),
            "lat": float(lat)
        })
    return pd.DataFrame(rows)

def explode_lines(gdf: gpd.GeoDataFrame):
    """Sadece geometri listesi döndürür."""
    out = []
    for _, row in gdf.iterrows():
        geom = row.geometry
        if geom is None:
            continue
        if geom.geom_type == "LineString":
            out.append(geom)
        elif geom.geom_type == "MultiLineString":
            for ls in geom.geoms:
                out.append(ls)
    return out

def explode_with_props(gdf: gpd.GeoDataFrame):
    """
    Özellikleri koruyarak tekil segmentlere böl.
    Dönen: {"geometry": LineString, "props": {...}}
    """
    cols = [c for c in gdf.columns if c != "geometry"]
    out = []
    for _, row in gdf.iterrows():
        geom = row.geometry
        props = {c: row.get(c) for c in cols}
        if geom is None:
            continue
        if geom.geom_type == "LineString":
            out.append({"geometry": geom, "props": props})
        elif geom.geom_type == "MultiLineString":
            for ls in geom.geoms:
                out.append({"geometry": ls, "props": props})
    return out
