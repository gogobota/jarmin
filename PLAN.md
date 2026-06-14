# Jarmin Development Plan

Based on research into the OpenStreetMap (OSM) to Garmin map creation process, here is the architectural plan to automate this workflow specifically for the Garmin Edge 530.

## Required Software Dependencies
To process the map generation pipeline locally, the following programs must be installed or available in the environment:

*   **Java Runtime Environment (JRE/JDK)**: Required to run the Java-based `mkgmap` and `splitter` tools.
*   **mkgmap**: Compiles the OSM data into the proprietary Garmin `.img` format and generates routing data.
*   **splitter**: Breaks the massive OpenStreetMap files into smaller, Garmin-friendly tiles before compilation.
*   **osmconvert**: A fast C-based command-line utility used for manipulating, merging (e.g., injecting contour lines), and filtering OSM data.
*   **osmium-tool** (osmium): A highly efficient C++ tool ideal for extracting specific regional bounding boxes from the official full planet `.osm.pbf` file.
*   **wget / curl**: Used in the automation scripts to download the planet file, elevation data, and tool binaries.
*   **make**: Recommended for running the automation pipeline (`Makefile`).

## Phase 1: Toolchain & Environment Setup
We will write a bootstrap script (or a `Makefile`/`Dockerfile`) to automatically fetch and configure the required binaries:
*   **Java Runtime** (required for `mkgmap` and `splitter`)
*   **mkgmap & splitter** (latest releases)
*   **osmconvert** (C-based tool for manipulating and merging OSM data)

## Phase 2: The Automation Pipeline
We will build an automated pipeline with configurable parameters (e.g., Region="Germany" or "Europe"). The pipeline will run the following sequence:
1.  **Fetch Data**: Download official map data directly from OpenStreetMap infrastructure (e.g., `planet.openstreetmap.org`). To target specific regions, we will extract the area locally from the official planet file using bounding boxes and a tool like `osmium` or `osmconvert`, avoiding reliance on third-party extract providers like Geofabrik.
2.  **Fetch Elevation**: Download matching SRTM (elevation) `.hgt` files and pre-processed contour data.
3.  **Merge**: Use `osmconvert` to inject the contour data into the primary map data.
4.  **Split**: Run `splitter` with parameters optimized for the Garmin Edge's memory limits.
5.  **Compile**: Run `mkgmap` with routing enabled and point it to our custom `.TYP` files and styling rules to generate the final `gmapsupp.img` file.

## Phase 3: Garmin Edge 530 Specific Tuning
The Edge 530 has a non-touch screen and a specific resolution/color palette. Cluttered maps are very hard to read while riding. We will create a custom map style within `jarmin` focusing on:
*   **High Contrast**: Making cycleways, unpaved roads, and trails visually distinct from primary roads.
*   **Decluttering**: Stripping out unnecessary data (like complex building polygons or motorway signs) that distract from navigation.
*   **Cycling POIs**: Prioritizing drinking water, cafes, bicycle repair shops, and public restrooms so they show up prominently.
*   **Routing Preferences**: Tuning the routing rules to prefer bike networks and avoid major highways. (We can use the `Openfietsmap` styles as a starting foundation and strip them down).

## Phase 4: Deployment
The final output of the pipeline will be a single `gmapsupp.img` file. The final step is simply connecting the Garmin Edge 530 via USB and dragging this file into the `Garmin` folder on the device.
