import numpy as np
import plotly.graph_objects as go

def latlon_to_xyz(lat, lon, R=1.0):
    lat_r = np.radians(lat)
    lon_r = np.radians(lon)
    x = R * np.cos(lat_r) * np.cos(lon_r)
    y = R * np.cos(lat_r) * np.sin(lon_r)
    z = R * np.sin(lat_r)
    return x, y, z

def sphere_surface(R=1.0, res=140):
    lats = np.linspace(-90, 90, res)
    lons = np.linspace(-180, 180, res)
    X = np.zeros((res, res)); Y = np.zeros((res, res)); Z = np.zeros((res, res))
    for i, lat in enumerate(lats):
        for j, lon in enumerate(lons):
            X[i, j], Y[i, j], Z[i, j] = latlon_to_xyz(lat, lon, R=R)
    S = np.tile(np.linspace(0, 1, res).reshape(-1, 1), (1, res))  # gradyan
    return X, Y, Z, S

def _add_polyline_trace(fig, segments, color, width, name, hover=False, R=1.0, bump=1.003):
    xs, ys, zs, texts = [], [], [], []
    for seg in segments:
        coords = seg["coords"]
        label = seg.get("label", name)
        for (lt, ln) in coords:
            x, y, z = latlon_to_xyz(lt, ln, R=R*bump)
            xs.append(x); ys.append(y); zs.append(z)
            if hover:
                texts.append(label)
        xs.append(None); ys.append(None); zs.append(None)
        if hover:
            texts.append(None)
    fig.add_trace(go.Scatter3d(
        x=xs, y=ys, z=zs,
        mode="lines",
        line=dict(width=width, color=color),
        name=name,
        hoverinfo="text" if hover else "skip",
        text=texts if hover else None
    ))

def make_faults_globe(fault_segments,
                      coast_segments=None,
                      line_color="#00E5FF",
                      line_width=3.5,
                      bg="#000000",
                      sphere_top="#101010",
                      sphere_bottom="#222222",
                      hover=False,
                      show_coast=False):
    R = 1.0
    X, Y, Z, S = sphere_surface(R=R, res=140)

    fig = go.Figure()
    # SİYAH KÜRE
    fig.add_trace(go.Surface(
        x=X, y=Y, z=Z, surfacecolor=S,
        colorscale=[[0, sphere_bottom], [1, sphere_top]],
        showscale=False, opacity=1.0, hoverinfo="skip"
    ))

    # FAYLAR
    _add_polyline_trace(fig, fault_segments, line_color, line_width, "Faults", hover=hover, R=R, bump=1.003)

    # KIYILAR (opsiyonel)
    if show_coast and coast_segments:
        _add_polyline_trace(fig, coast_segments, "rgb(120,120,120)", 1.5, "Coastlines", hover=False, R=R, bump=1.001)

    fig.update_layout(
        paper_bgcolor=bg,
        scene=dict(
            bgcolor=bg,
            xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False),
            aspectmode="data"
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False
    )
    return fig
