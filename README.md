# Jarmin

Jarmin is a development system designed to create custom maps for Garmin 530 GPS devices using OpenStreetMap (OSM) data. 

## Features

- Fetch and process OSM data.
- Convert OSM data into Garmin-compatible map formats (.img files).
- Tailored specifically for the display and routing capabilities of the Garmin Edge 530.

## Running

The local python environment needs to be set correctly by activating it:

```
source .venv/bin/activate
```

Genaration of Garmin map files using the tool can be performed with the following command:

```
./pipeline.py --countries "Luxembourg" --update --generate-elevation --output work/edge530_luxembourg.img
```

Several countries can be chosen at once, for example:
```
./pipeline.py --countries "Germany,Poland,Luxembourg" --update --generate-elevation --output work/edge530_germany_poland_luxembourg.img
```

The tool bboxfinder.com can be used to visualize bounding boxes. For example, for the bounding box values with a 50 kilometer border around Germany, use:
```
46.820954,5.072345,55.548319,15.835901
```
And visualize this border here: https://bboxfinder.com/#46.820954,5.072345,55.548319,15.835901
Reorder these values as min_lon,min_lat,max_lon,max_lat to be passed into osmconvert as:
```
5.0723452,46.8209538,15.8359010,55.5483186
```
For example:
```
./pipeline.py --bbox "5.0723452,46.8209538,15.8359010,55.5483186" --update --generate-elevation --output work/edge530_germany_50k.img
```



## Development

To prepare the environment to run the system, some steps need to be taken. Binary files need to be downloaded and unpacked, source files need to be compiled, and the local python virtual environment needs to be setup. This can be done by running the shell script:

```
./prepare.sh
```


