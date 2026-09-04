#!/usr/bin/env python3
# staticInst/plot_childcare.py
"""
Safe helper to plot childcare spatial geometry produced by CityGen.py.

Usage:
  python staticInst/plot_childcare.py -i <input_dir_with_city.geojson> -o <output_dir_with_childcare_centres.json>

Outputs:
  - <output_dir>/childcare_map.png      (static map)
  - <output_dir>/childcare_map.html     (interactive; only if plotly is installed)
  - <output_dir>/childcare_plot_error.log  (on failure)
"""
from pathlib import Path
import argparse
import traceback
import json
import os

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

# plotly optional
try:
    import plotly.express as px
    import plotly
    HAVE_PLOTLY = True
except Exception:
    HAVE_PLOTLY = False


def plot_childcare_from_files(input_dir, output_dir):
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    geo_path = input_dir / "city.geojson"
    centres_path = output_dir / "childcare_centres.json"

    if not geo_path.exists():
        raise FileNotFoundError(f"GeoJSON not found: {geo_path}")
    if not centres_path.exists():
        raise FileNotFoundError(f"Childcare centres file not found: {centres_path}\nRun CityGen.py first to generate {centres_path.name}")

    # Read wards geometry (keep original CRS)
    wards = gpd.read_file(str(geo_path))
    if 'wardIndex' not in wards.columns and 'wardNo' in wards.columns:
        wards['wardIndex'] = wards['wardNo'].astype(int) - 1
    if 'geometry' not in wards.columns:
        raise RuntimeError("city.geojson missing 'geometry'")

    wards_crs = wards.crs  # may be None
    wards = wards.set_geometry('geometry')

    # Read centres list
    with open(str(centres_path), 'r') as fh:
        centres = json.load(fh)

    centres_df = pd.DataFrame(centres) if centres else pd.DataFrame(columns=['ID', 'wardIndex', 'lat', 'lon', 'enrolled'])

    # Create centres GeoDataFrame using same CRS as wards (so containment checks are valid)
    if not centres_df.empty:
        centres_gdf = gpd.GeoDataFrame(
            centres_df.copy(),
            geometry=gpd.points_from_xy(centres_df.lon, centres_df.lat),
            crs=wards_crs  # match wards CRS (may be None)
        )
    else:
        centres_gdf = gpd.GeoDataFrame(centres_df.copy(), geometry=None, crs=wards_crs)

    # Aggregation per ward
    if not centres_df.empty:
        enrolled_per_ward = centres_df.groupby('wardIndex')['enrolled'].sum().rename('enrolled_sum')
        centres_count = centres_df.groupby('wardIndex').size().rename('num_centres')
    else:
        enrolled_per_ward = pd.Series(dtype=int)
        centres_count = pd.Series(dtype=int)

    wards = wards.reset_index(drop=True)
    wards['wardIndex'] = wards['wardIndex'].astype(int)
    wards['enrolled_sum'] = wards['wardIndex'].map(enrolled_per_ward).fillna(0).astype(int)
    wards['num_centres'] = wards['wardIndex'].map(centres_count).fillna(0).astype(int)

    # ---- STATIC PNG: ensure points lie inside ward polygons (in same CRS) ----
    out_png = output_dir / "childcare_map.png"
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    wards.plot(column='enrolled_sum', cmap='Blues', legend=True,
               legend_kwds={'label': "Enrolled children (sum)"},
               ax=ax, edgecolor='k', linewidth=0.2)

    if not centres_gdf.empty:
        # For each centre, check it is inside the ward polygon; if not, snap to representative_point()
        for idx, row in centres_gdf.iterrows():
            try:
                widx = int(row['wardIndex'])
            except Exception:
                continue
            sel = wards.loc[wards['wardIndex'] == widx]
            if sel.empty:
                continue
            poly = sel.iloc[0].geometry
            pt = row.geometry
            # If any CRS is missing, shapely ops still work if both geometries are in same coordinate values.
            if pt is None or not poly.contains(pt):
                # replace with a guaranteed-inside point
                rep = poly.representative_point()
                centres_gdf.at[idx, 'geometry'] = rep
                centres_gdf.at[idx, 'lon'] = rep.x
                centres_gdf.at[idx, 'lat'] = rep.y

        # plot centres on top (smaller sizes to avoid visual spanning of boundaries)
        sizes = (centres_gdf.get('enrolled', pd.Series(1)).fillna(1).clip(lower=1).astype(int) * 1.5).tolist()
        centres_gdf.plot(ax=ax, color='red', markersize=sizes, alpha=0.85, marker='o', label='Childcare centres', zorder=3)

    ax.set_title('Childcare centres: enrolled children and locations')
    ax.axis('off')
    plt.savefig(str(out_png), bbox_inches='tight', dpi=150)
    plt.close()

    # ---- INTERACTIVE PLOTLY (optional) ----
    out_html = None
    if HAVE_PLOTLY:
        # Convert to EPSG:4326 for Plotly (only if CRS is known)
        try:
            if wards_crs is not None and wards_crs.to_string() != 'EPSG:4326':
                wards_plot = wards.to_crs(epsg=4326)
            else:
                wards_plot = wards.copy()
        except Exception:
            wards_plot = wards.copy()

        if not centres_gdf.empty:
            try:
                if centres_gdf.crs is not None and centres_gdf.crs.to_string() != 'EPSG:4326':
                    centres_plot = centres_gdf.to_crs(epsg=4326)
                else:
                    centres_plot = centres_gdf.copy()
            except Exception:
                centres_plot = centres_gdf.copy()
        else:
            centres_plot = centres_gdf.copy()

        out_html = output_dir / "childcare_map.html"
        plot_df = wards_plot.reset_index(drop=True)
        fig2 = px.choropleth(
            plot_df,
            geojson=plot_df.geometry,
            locations=plot_df.index,
            color='enrolled_sum',
            hover_name=plot_df.get('wardName', None),
            color_continuous_scale='Viridis',
            labels={'enrolled_sum': 'Enrolled children'}
        )
        fig2.update_geos(fitbounds="locations", visible=False)
        if not centres_plot.empty:
            fig2.add_scattergeo(
                lon=centres_plot['lon'],
                lat=centres_plot['lat'],
                text=centres_plot.apply(lambda r: f"Centre {int(r['ID'])}<br>enrolled: {int(r.get('enrolled',0))}", axis=1),
                marker=dict(size=centres_plot['enrolled'].fillna(1).clip(lower=1) * 2, color='red', opacity=0.8),
                name='Childcare centres'
            )
        fig2.update_layout(title_text='Childcare centres (enrolled) — interactive', margin={"r":0,"t":30,"l":0,"b":0})
        plotly.offline.plot(fig2, filename=str(out_html), auto_open=False)

    return str(out_png), (str(out_html) if out_html else None)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', required=True, help='input dir containing city.geojson')
    parser.add_argument('-o', '--output', required=True, help='output dir containing childcare_centres.json (and where outputs will be written)')
    args = parser.parse_args()

    error_log = Path(args.output) / "childcare_plot_error.log"
    try:
        png, html = plot_childcare_from_files(args.input, args.output)
        print("Wrote:", png)
        if html:
            print("Wrote:", html)
        else:
            print("Plotly not installed or HTML skipped.")
    except Exception as e:
        tb = traceback.format_exc()
        print("Error while plotting childcare map. See log:", error_log)
        with open(str(error_log), "w") as fh:
            fh.write("Exception:\n")
            fh.write(str(e))
            fh.write("\n\nTraceback:\n")
            fh.write(tb)


if __name__ == "__main__":
    main()