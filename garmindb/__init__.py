"""A database and database objects for storing health data from Garmin Connect."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

# flake8: noqa

from .version_info import version_string

__version__ = version_string()

from .garmin_connect_config_manager import GarminConnectConfigManager
from .config_manager import ConfigManager
from .garmin_stats import Statistics
from .copy import Copy
from .download import Download

