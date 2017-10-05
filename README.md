# world_cities
World cities extractor from osm xapi or wiki_data

```bash
docker build -t world_cities
docker run -d \
-it \
-e API_NAME="wiki_data" \  # [or "osm_xapi" for using the osm data]
-v <location>:/data \
world_cities --help
```
