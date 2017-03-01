import json
from docopt import docopt

from osm_xapi import OSMXAPI
from file_manager import FileManager
from stats_manager import StatsManager

help = """About script.

Usage:
  extract_world_cities.py extract [--area=AREA --type=TYPE --merge=FORMAT]
  extract_world_cities.py merge [--output-format=FORMAT]
  extract_world_cities.py stats

Options:
  -h --help
  -a --area=AREA  box sizes for api call [default: 10]
  -t --type=TYPE  which kind of place we extract [default: city,town,village]
  -m --merge=FORMAT  if set we merge the collected cities in one file
  -o --output-format=FORMAT  the format of the output merged file [default: csv]
"""


def extract_cities_from_osm(area=10, types=["city", "town", "village"]):
    bbox = [(mlon, mlat, mlon + area, mlat + area) for mlon in range(-90, 90, area) for mlat in range(-90, 90, area)]
    for place_type in set(OSMXAPI.PLACE_TYPES).intersection(types):
        for mlon, mlat, Mlon, Mlat in bbox:
            extract_from_bbox(place_type, mlon, mlat, Mlon, Mlat)


def extract_from_bbox(_type, mlon, mlat, Mlon, Mlat, _try=0):
    print "place_type=%s" % _type, "bbox=[%s,%s,%s,%s]" % (mlon, mlat, Mlon, Mlat)
    filename = OSMXAPI.get_file_name(_type, mlon, mlat, Mlon, Mlat)
    if not OSMXAPI.has_already_data(_type, mlon, mlat, Mlon, Mlat, _try=_try):
        try:
            data = OSMXAPI.call_api(_type, mlon, mlat, Mlon, Mlat)
        except KeyboardInterrupt:
            raise
        except:
            data = {'status': 'FAILED'}
        if data["status"] == "FAILED" and _try <= OSMXAPI.MAX_TRY:  # cut bbox into 4 parts
            print "failed to extract, retry on smaller boxes ..."
            av_lon, av_lat = (Mlon - mlon) / 2., (Mlat - mlat) / 2.
            extract_from_bbox(_type, mlon, mlat, Mlon - av_lon, Mlat - av_lat, _try=_try + 1)
            extract_from_bbox(_type, mlon, mlat + av_lat, Mlon - av_lon, Mlat, _try=_try + 1)
            extract_from_bbox(_type, mlon + av_lon, mlat, Mlon, Mlat - av_lat, _try=_try + 1)
            extract_from_bbox(_type, mlon + av_lon, mlat + av_lat, Mlon, Mlat, _try=_try + 1)
        elif _try > 3:
            print "Max try exceeded: failed to extract data"
        else:
            FileManager.write(filename, json.dumps(data))


if __name__ == "__main__":
    arguments = docopt(help)
    if arguments["extract"] is True:
        area = int(arguments["--area"])
        types = arguments["--type"].split(",")
        _format = arguments["--merge"]
        extract_cities_from_osm(area=area, types=types)
        if _format is not None:
            OSMXAPI.merge_cities_file(_format=_format)
    elif arguments["merge"] is True:
        _format = arguments["--output-format"]
        print "merging cities files"
        OSMXAPI.merge_cities_file(_format=_format)
    elif arguments['stats'] is True:
        print "computing stats"
        print StatsManager.get_osm_extracted_cities_stats()
