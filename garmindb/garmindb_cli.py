#!/usr/bin/env python3

"""
A script that imports and analyzes Garmin health device data into a database.

The data is either copied from a USB mounted Garmin device or downloaded from Garmin Connect.
"""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import logging
import sys
import argparse
import os


from download import Download




logging.basicConfig(filename='garmindb.log', filemode='w', level=logging.INFO)
logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
root_logger = logging.getLogger()


def download_data(overwite, latest):
    """Download selected activity types from Garmin Connect and save the data in files. Overwrite previously downloaded data if indicated."""
    logger.info("___Downloading %s Data___", 'Latest' if latest else 'All')

    download = Download()
    if not download.login():
        logger.error("Failed to login!")
        sys.exit()
    if latest:
        activity_count = 2
    else:
        activity_count = 30
    dir = "data/zip"
    if not os.path.exists("data"):
            os.makedirs("data")
    if not os.path.exists(dir):
            os.makedirs(dir)
    activities_dir = dir
    root_logger.info("Fetching %d activities to %s", activity_count, activities_dir) 
    download.get_activities(activities_dir, activity_count, overwite)



def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--trace", help="Turn on debug tracing", type=int, default=0)
    modes_group = parser.add_argument_group('Modes')
    modes_group.add_argument("-d", "--download", help="Download data from Garmin Connect for the chosen stats.", dest='download_data', action="store_true", default=False)
    modifiers_group = parser.add_argument_group('Modifiers')
    modifiers_group.add_argument("-l", "--latest", help="Only download and/or import the latest data.", action="store_true", default=False)
    modifiers_group.add_argument("-o", "--overwrite", help="Overwite existing files when downloading. The default is to only download missing files.",
                                 action="store_true", default=False)
    args = parser.parse_args()

    if args.trace > 0:
        root_logger.setLevel(logging.DEBUG)
    else:
        root_logger.setLevel(logging.INFO)


    if args.download_data:
        download_data(args.overwrite, args.latest)

    


if __name__ == "__main__":
    main(sys.argv[1:])
