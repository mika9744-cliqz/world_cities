import json
from docopt import docopt

from osm_xapi import FileManager, OSMXAPI

help = """About script.

Usage:
  extract_world_cities.py extract [--area=AREA --type=TYPE --merge]
  extract_world_cities.py merge

Options:
  -h --help
  -a --area=AREA  box sizes for api call [default: 10]
  -t --type=TYPE  which kind of place we extract [default: city,town,village]
  -m --merge  if set we merge the collected cities in one file
"""


def extract_cities_from_osm(area=10, types=["city", "town", "village"]):
    bbox = [(mlon, mlat, mlon + area, mlat + area) for mlon in range(-90, 90, area) for mlat in range(-90, 90, area)]
    for place_type in set(OSMXAPI.PLACE_TYPES).intersection(types):
        for mlon, mlat, Mlon, Mlat in bbox:
            extract_from_bbox(place_type, mlon, mlat, Mlon, Mlat)


def extract_from_bbox(_type, mlon, mlat, Mlon, Mlat, _try=0):
    print "place_type=%s" % _type, "bbox=[%s,%s,%s,%s]" % (mlon, mlat, Mlon, Mlat)
    data = OSMXAPI.call_api(_type, mlon, mlat, Mlon, Mlat)
    if data["status"] == "FAILED" and _try <= 3:  # cut bbox into 4 parts
        "failed to extract, retry on smaller boxes ..."
        av_lon, av_lat = (Mlon - mlon) / 2., (Mlat - mlat) / 2.
        extract_from_bbox(_type, mlon, mlat, Mlon - av_lon, Mlat - av_lat, _try=_try + 1)
        extract_from_bbox(_type, mlon, mlat + av_lat, Mlon - av_lon, Mlat, _try=_try + 1)
        extract_from_bbox(_type, mlon + av_lon, mlat, Mlon, Mlat - av_lat, _try=_try + 1)
        extract_from_bbox(_type, mlon + av_lon, mlat + av_lat, Mlon, Mlat, _try=_try + 1)
    else:
        filename = OSMXAPI.get_file_name(_type, mlon, mlat, Mlon, Mlat)
        FileManager.write(filename, json.dumps(data))


def merge_cities_files():
    print "merging cities files"
    OSMXAPI.merge_cities_file()


if __name__ == "__main__":
    arguments = docopt(help)
    if arguments["extract"] is True:
        area = int(arguments["--area"])
        types = arguments["--type"].split(",")
        extract_cities_from_osm(area=area, types=types)
        if arguments["--merge"] is True:
            merge_cities_files()
    elif arguments["merge"] is True:
        merge_cities_files()

