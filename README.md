# world_cities
World cities extractor from osm xapi or wiki_data.

Running this image will generate a csv or json file with cities. Each extracted city is provided in several languages.
For the wiki_data api env, the provided languages are en, de and fr.

# How to use
```bash
docker build -t world_cities
docker run -d \
-it \
-e API_NAME="wiki_data" \  # [or "osm_xapi" for using the osm data]
-v /path/where/to/store/data:/data \
world_cities --help
```

# Example
```bash
# First build the image
docker build . -t world_cities

# osm_xapi: extract the cities, and at the end of the process, merge them into one csv file.
# --overwrite=1 force to replace the existing files
docker run -d -it -v <location>:/data -e API_NAME="osm_xapi" world_cities extract --overwrite=1 --merge=csv

# get stats about the extracted cities
docker run -d -it -v <location>:/data -e API_NAME="osm_xapi" world_cities stats


# wiki_data: we can separate the extract process from the merge process.
# API_NAME default value is "wiki_data"
# Furthermore, not specifying the --overwrite parameter will not process the data we already have.
docker run -d -it -v <location>:/data world_cities extract

# merge the cities into one file. We can choose the format. Only two format are supported: csv, json
docker run -d -it -v <location>:/data world_cities merge --output-format=json

# Again it is also possible to get stats
docker run -d -it -v <location>:/data world_cities stats
```
