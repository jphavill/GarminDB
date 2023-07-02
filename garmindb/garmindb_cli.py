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
import datetime
import os
import tempfile
import zipfile
import glob

from download import Download

from garmin_connect_config_manager import GarminConnectConfigManager
from config_manager import ConfigManager
from garmin_stats import Statistics



logging.basicConfig(filename='garmindb.log', filemode='w', level=logging.INFO)
logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
root_logger = logging.getLogger()

gc_config = GarminConnectConfigManager()
db_params_dict = ConfigManager.get_db_params()


def download_data(overwite, latest, stats):
    """Download selected activity types from Garmin Connect and save the data in files. Overwrite previously downloaded data if indicated."""
    logger.info("___Downloading %s Data___", 'Latest' if latest else 'All')

    download = Download()
    if not download.login():
        logger.error("Failed to login!")
        sys.exit()
    if latest:
        activity_count = gc_config.latest_activity_count()
    else:
        activity_count = gc_config.all_activity_count()
    activities_dir = ConfigManager.get_or_create_activities_dir()
    root_logger.info("Fetching %d activities to %s", activity_count, activities_dir) 
    download.get_activities(activities_dir, activity_count, overwite)



def main(argv):
    """Manage Garmin device data."""

    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--trace", help="Turn on debug tracing", type=int, default=0)
    modes_group = parser.add_argument_group('Modes')
    modes_group.add_argument("-b", "--backup", help="Backup the database files.", dest='backup_dbs', action="store_true", default=False)
    modes_group.add_argument("-d", "--download", help="Download data from Garmin Connect for the chosen stats.", dest='download_data', action="store_true", default=False)
    modes_group.add_argument("-c", "--copy", help="copy data from a connected device", dest='copy_data', action="store_true", default=False)
    modes_group.add_argument("-i", "--import", help="Import data for the chosen stats", dest='import_data', action="store_true", default=False)
    modes_group.add_argument("--analyze", help="Analyze data in the db and create summary and derived tables.", dest='analyze_data', action="store_true", default=False)
    modes_group.add_argument("--rebuild_db", help="Delete Garmin DB db files and rebuild the database.", action="store_true", default=False)
    modes_group.add_argument("--delete_db", help="Delete Garmin DB db files for the selected activities.", action="store_true", default=False)
    modes_group.add_argument("-e", "--export-activity", help="Export an activity to a TCX file based on the activity\'s id", type=int)
    modes_group.add_argument("--basecamp-activity", help="Export an activity to Garmin BaseCamp", type=int)
    modes_group.add_argument("-g", "--google-earth-activity", help="Export an activity to Google Earth", type=int)
    # stat types to operate on
    stats_group = parser.add_argument_group('Statistics')
    stats_group.add_argument("-A", "--all", help="Download and/or import data for all enabled stats.", action='store_const', dest='stats',
                             const=gc_config.enabled_stats(), default=[])
    stats_group.add_argument("-a", "--activities", help="Download and/or import activities data.", dest='stats', action='append_const', const=Statistics.activities)
    stats_group.add_argument("-m", "--monitoring", help="Download and/or import monitoring data.", dest='stats', action='append_const', const=Statistics.monitoring)
    stats_group.add_argument("-r", "--rhr", help="Download and/or import resting heart rate data.", dest='stats', action='append_const', const=Statistics.rhr)
    stats_group.add_argument("-s", "--sleep", help="Download and/or import sleep data.", dest='stats', action='append_const', const=Statistics.sleep)
    stats_group.add_argument("-w", "--weight", help="Download and/or import weight data.", dest='stats', action='append_const', const=Statistics.weight)
    modifiers_group = parser.add_argument_group('Modifiers')
    modifiers_group.add_argument("-l", "--latest", help="Only download and/or import the latest data.", action="store_true", default=False)
    modifiers_group.add_argument("-o", "--overwrite", help="Overwite existing files when downloading. The default is to only download missing files.",
                                 action="store_true", default=False)
    args = parser.parse_args()

    if args.trace > 0:
        root_logger.setLevel(logging.DEBUG)
    else:
        root_logger.setLevel(logging.INFO)

    root_logger.info("Enabled statistics: %r", args.stats)

    if args.download_data:
        download_data(args.overwrite, args.latest, args.stats)

    


if __name__ == "__main__":
    main(sys.argv[1:])
