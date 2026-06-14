#!/usr/bin/env python3
import os
import sys
import json
import time
import subprocess
import argparse
import urllib.request
import urllib.parse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DOWNLOADS_DIR = BASE_DIR / "downloads"
SPLITTER_JAR = DOWNLOADS_DIR / "splitter-r654" / "splitter.jar"
MKGMAP_JAR = DOWNLOADS_DIR / "mkgmap-r4924" / "mkgmap.jar"
OSMCONVERT_BIN = DOWNLOADS_DIR / "osmconvert"

def run_cmd(cmd):
    print(f"--> {' '.join(str(c) for c in cmd)}")
    subprocess.run(cmd, check=True)

def download_planet(url, dest):
    if dest.exists():
        print(f"File {dest} already exists. Skipping download.")
        return
    print(f"Downloading {url} to {dest}...")
    urllib.request.urlretrieve(url, dest)

def fetch_country_geometry(country_name):
    url = f"https://nominatim.openstreetmap.org/search?country={urllib.parse.quote(country_name.strip())}&format=json&polygon_geojson=1"
    req = urllib.request.Request(url, headers={'User-Agent': 'jarmin-pipeline/1.0'})
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
    
    for item in data:
        if item.get('osm_type') == 'relation' and item.get('class') == 'boundary' and 'geojson' in item:
            return item['geojson']
    
    if data and 'geojson' in data[0]:
        return data[0]['geojson']
    
    raise ValueError(f"Could not find GeoJSON boundary for country: {country_name}")

def build_countries_geojson(countries, output_path):
    print(f"Fetching border geometries from OSM for: {', '.join(countries)}")
    features = []
    for i, country in enumerate(countries):
        if i > 0:
            time.sleep(1.1)  # Respect Nominatim Usage Policy (max 1 request/sec)
        geom = fetch_country_geometry(country)
        features.append({
            "type": "Feature",
            "properties": {"name": country.strip()},
            "geometry": geom
        })
    
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    with open(output_path, 'w') as f:
        json.dump(geojson, f)

def extract_region(input_pbf, output_pbf, bbox=None, polygon_file=None):
    if polygon_file:
        cmd = ["osmium", "extract", "-p", str(polygon_file), str(input_pbf), "-o", str(output_pbf), "--overwrite"]
    elif bbox:
        cmd = ["osmium", "extract", "-b", bbox, str(input_pbf), "-o", str(output_pbf), "--overwrite"]
    else:
        raise ValueError("Either bbox or polygon_file must be provided for extraction.")
    run_cmd(cmd)

def split_data(input_pbf, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        "java", "-jar", str(SPLITTER_JAR),
        f"--output-dir={output_dir}",
        str(input_pbf)
    ]
    run_cmd(cmd)

def compile_map(split_dir, output_file):
    out_dir = output_file.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    template_args = split_dir / "template.args"
    
    style_dir = BASE_DIR / "style" / "edge530"
    typ_file = BASE_DIR / "style" / "edge530.txt"

    cmd = [
        "java", "-jar", str(MKGMAP_JAR),
        "--route",
        "--gmapsupp",
        "--family-id=1337",
        f"--style-file={style_dir}",
        f"--output-dir={out_dir}",
        "-c", str(template_args),
        str(typ_file)
    ]
    run_cmd(cmd)
    
    # mkgmap usually outputs gmapsupp.img inside the out_dir.
    produced_img = out_dir / "gmapsupp.img"
    if produced_img.resolve() != output_file.resolve() and produced_img.exists():
        produced_img.rename(output_file)

def merge_elevation(map_pbf, elevation_pbf, output_pbf):
    # Placeholder for Phase 2: Inject contour data using osmconvert
    # e.g., run_cmd([str(OSMCONVERT_BIN), str(map_pbf), str(elevation_pbf), "-o=" + str(output_pbf)])
    pass

def run_pipeline(planet_url, planet_file, work_dir, output_file, skip_download, bbox=None, countries=None, polygon=None):
    if not (bbox or countries or polygon):
        print("Error: You must provide one of --bbox, --countries, or --polygon to extract data.")
        sys.exit(1)

    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    output_file = Path(output_file)
    
    planet_path = work_dir / Path(planet_file).name
    region_path = work_dir / "region.osm.pbf"
    split_dir = work_dir / "split"
    mask_file = None

    if countries:
        mask_file = work_dir / "countries_mask.geojson"
        build_countries_geojson(countries.split(','), mask_file)
    elif polygon:
        mask_file = Path(polygon)

    local_planet = Path(planet_file)
    if local_planet.exists():
        print(f"Found local planet file at '{local_planet}', skipping download.")
        input_for_extraction = local_planet
    elif planet_path.exists():
        print(f"Found local planet file at '{planet_path}', skipping download.")
        input_for_extraction = planet_path
    elif not skip_download:
        download_planet(planet_url, planet_path)
        input_for_extraction = planet_path
    else:
        input_for_extraction = local_planet

    print("1. Extracting region...")
    extract_region(input_for_extraction, region_path, bbox=bbox, polygon_file=mask_file)

    print("2. Splitting data...")
    split_data(region_path, split_dir)

    print("3. Compiling Garmin map...")
    compile_map(split_dir, output_file)

    print(f"Pipeline finished! Map is available at: {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Jarmin Map Pipeline")
    parser.add_argument("--planet-url", default="https://planet.openstreetmap.org/pbf/planet-latest.osm.pbf", help="URL for the official planet file")
    parser.add_argument("--planet-file", default="planet-latest.osm.pbf", help="Local path for the planet file")
    parser.add_argument("--work-dir", default="work", help="Temporary working directory")
    parser.add_argument("--output", default="gmapsupp.img", help="Final Garmin map output path")
    parser.add_argument("--skip-download", action="store_true", help="Skip planet download and use local --planet-file")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--bbox", help="Bounding box (min_lon,min_lat,max_lon,max_lat)")
    group.add_argument("--countries", help="Comma-separated list of country names (e.g. 'Germany,France')")
    group.add_argument("--polygon", help="Path to a custom .poly or .geojson mask file")

    args = parser.parse_args()

    # Verify dependencies are in place
    for tool in [SPLITTER_JAR, MKGMAP_JAR, OSMCONVERT_BIN]:
        if not tool.exists():
            print(f"Error: Missing tool {tool}. Did you run downloads/download.sh?")
            sys.exit(1)

    run_pipeline(
        planet_url=args.planet_url,
        planet_file=args.planet_file,
        work_dir=args.work_dir,
        output_file=args.output,
        skip_download=args.skip_download,
        bbox=args.bbox,
        countries=args.countries,
        polygon=args.polygon
    )

if __name__ == "__main__":
    main()
