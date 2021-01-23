#!/usr/bin/env python3

"""Script for importing into a DB and summarizing CSV formatted FitBit export data."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import sys
import argparse
import logging


import FitBitDB
from import_fitbit_csv import FitBitData
from analyze_fitbit import Analyze
from garmin_db_config_manager import GarminDBConfigManager
from version import format_version


logging.basicConfig(filename='fitbit.log', filemode='w', level=logging.DEBUG)
logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
root_logger = logging.getLogger()


def usage(program):
    """Print the usage info for the script."""
    print('%s -i <inputfile> ...' % program)
    sys.exit()


def main(argv):
    """Import into a DB and summarize CSV formatted FitBit export data."""
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--version", help="print the program's version", action='version', version=format_version(sys.argv[0]))
    parser.add_argument("-t", "--trace", help="Turn on debug tracing", type=int, default=0)
    modes_group = parser.add_argument_group('Modes')
    modes_group.add_argument("-i", "--input_file", help="Specifiy the CSV file to import into the database")
    modes_group.add_argument("--delete_db", help="Delete FitBit db file.", action="store_true", default=False)
    args = parser.parse_args()

    root_logger = logging.getLogger()
    if args.trace > 0:
        root_logger.setLevel(logging.DEBUG)
    else:
        root_logger.setLevel(logging.INFO)

    db_params = GarminDBConfigManager.get_db_params()

    if args.delete_db:
        FitBitDB.FitBitDB.delete_db(db_params)
        sys.exit()

    fitbit_dir = GarminDBConfigManager.get_or_create_fitbit_dir()
    metric = GarminDBConfigManager.get_metric()
    fd = FitBitData(args.input_file, fitbit_dir, db_params, metric, args.trace)
    if fd.file_count() > 0:
        fd.process_files()

    analyze = Analyze(db_params)
    analyze.get_years()
    analyze.summary()


if __name__ == "__main__":
    main(sys.argv[1:])
