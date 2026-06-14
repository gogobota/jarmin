#!/usr/bin/env python3
import os
import sys
import subprocess
import argparse
import urllib.request
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

def extract_bbox(input_pbf, output_pbf, bbox):
    # bbox format for osmium: min_lon,min_lat,max_lon,max_lat
    cmd = ["osmium", "extract", "-b", bbox, str(input_pbf), "-o", str(output_pbf), "--overwrite"]
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
    
    cmd = [
        "java", "-jar", str(MKGMAP_JAR),
        "--route",
        "--gmapsupp",
        f"--output-dir={out_dir}",
        "-c", str(template_args)
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

def run_pipeline(planet_url, planet_file, bbox, work_dir, output_file, skip_download):
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    output_file = Path(output_file)
    
    planet_path = work_dir / Path(planet_file).name
    region_path = work_dir / "region.osm.pbf"
    split_dir = work_dir / "split"

    if not skip_download:
        download_planet(planet_url, planet_path)
        input_for_extraction = planet_path
    else:
        input_for_extraction = Path(planet_file)

    print("1. Extracting region...")
    extract_bbox(input_for_extraction, region_path, bbox)

    print("2. Splitting data...")
    split_data(region_path, split_dir)

    print("3. Compiling Garmin map...")
    compile_map(split_dir, output_file)

    print(f"Pipeline finished! Map is available at: {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Jarmin Map Pipeline")
    parser.add_argument("--planet-url", default="https://planet.openstreetmap.org/pbf/planet-latest.osm.pbf", help="URL for the official planet file")
    parser.add_argument("--planet-file", default="planet-latest.osm.pbf", help="Local path for the planet file")
    parser.add_argument("--bbox", required=True, help="Bounding box (min_lon,min_lat,max_lon,max_lat)")
    parser.add_argument("--work-dir", default="work", help="Temporary working directory")
    parser.add_argument("--output", default="gmapsupp.img", help="Final Garmin map output path")
    parser.add_argument("--skip-download", action="store_true", help="Skip planet download and use local --planet-file")

    args = parser.parse_args()

    # Verify dependencies are in place
    for tool in [SPLITTER_JAR, MKGMAP_JAR, OSMCONVERT_BIN]:
        if not tool.exists():
            print(f"Error: Missing tool {tool}. Did you run downloads/download.sh?")
            sys.exit(1)

    run_pipeline(args.planet_url, args.planet_file, args.bbox, args.work_dir, args.output, args.skip_download)

if __name__ == "__main__":
    main()
