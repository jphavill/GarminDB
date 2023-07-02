"""Class for downloading health data from Garmin Connect."""

__author__ = "Tom Goetz"
__copyright__ = "Copyright Tom Goetz"
__license__ = "GPL"

import os
import sys
import re
import logging
import datetime
import time
import tempfile
import zipfile
import json
import cloudscraper
from tqdm import tqdm

import fitfile.conversions as conversions
from idbutils import RestClient, RestException, RestResponseException

from garmin_connect_config_manager import GarminConnectConfigManager
from config_manager import ConfigManager


logger = logging.getLogger(__file__)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
root_logger = logging.getLogger()


class Download():
    """Class for downloading health data from Garmin Connect."""

    garmin_connect_base_url = "https://connect.garmin.com"
    garmin_connect_enus_url = garmin_connect_base_url + "/en-US"

    garmin_connect_sso_login = 'signin'

    garmin_connect_login_url = garmin_connect_enus_url + "/signin"

    garmin_connect_css_url = 'https://static.garmincdn.com/com.garmin.connect/ui/css/gauth-custom-v1.2-min.css'

    garmin_connect_privacy_url = "//connect.garmin.com/en-U/privacy"

    garmin_connect_user_profile_url = "proxy/userprofile-service/userprofile"
    garmin_connect_weight_url = "proxy/weight-service/weight/dateRange"

    garmin_connect_activity_search_url = "proxy/activitylist-service/activities/search/activities"

    # https://connect.garmin.com/modern/proxy/usersummary-service/usersummary/hydration/allData/2019-11-29

    garmin_headers = {'NK': 'NT'}

    def __init__(self):
        """Create a new Download class instance."""
        logger.debug("__init__")
        self.session = cloudscraper.CloudScraper()
        self.sso_rest_client = RestClient(self.session, 'sso.garmin.com', 'sso', aditional_headers=self.garmin_headers)
        self.modern_rest_client = RestClient(self.session, 'connect.garmin.com', 'modern', aditional_headers=self.garmin_headers)
        self.activity_service_rest_client = RestClient.inherit(self.modern_rest_client, "proxy/activity-service/activity")
        self.download_service_rest_client = RestClient.inherit(self.modern_rest_client, "proxy/download-service/files")
        self.gc_config = GarminConnectConfigManager()
        self.download_days_overlap = 1  # Existing donloaded data will be redownloaded and overwritten if it is within this number of days of now.

    def __get_json(self, page_html, key):
        found = re.search(key + r" = (\{.*\});", page_html, re.M)
        if found:
            json_text = found.group(1).replace('\\"', '"')
            return json.loads(json_text)

    def login(self):
        """Login to Garmin Connect."""
        profile_dir = ConfigManager.get_or_create_fit_files_dir()
        username = self.gc_config.get_user()
        password = self.gc_config.get_password()
        if not username or not password:
            print("Missing config: need username and password. Edit GarminConnectConfig.json.")
            return

        logger.debug("login: %s %s", username, password)
        get_headers = {
            'Referer'                           : self.garmin_connect_login_url
        }
        params = {
            'service'                           : self.modern_rest_client.url(),
            'webhost'                           : self.garmin_connect_base_url,
            'source'                            : self.garmin_connect_login_url,
            'redirectAfterAccountLoginUrl'      : self.modern_rest_client.url(),
            'redirectAfterAccountCreationUrl'   : self.modern_rest_client.url(),
            'gauthHost'                         : self.sso_rest_client.url(),
            'locale'                            : 'en_US',
            'id'                                : 'gauth-widget',
            'cssUrl'                            : self.garmin_connect_css_url,
            'privacyStatementUrl'               : '//connect.garmin.com/en-US/privacy/',
            'clientId'                          : 'GarminConnect',
            'rememberMeShown'                   : 'true',
            'rememberMeChecked'                 : 'false',
            'createAccountShown'                : 'true',
            'openCreateAccount'                 : 'false',
            'displayNameShown'                  : 'false',
            'consumeServiceTicket'              : 'false',
            'initialFocus'                      : 'true',
            'embedWidget'                       : 'false',
            'generateExtraServiceTicket'        : 'true',
            'generateTwoExtraServiceTickets'    : 'false',
            'generateNoServiceTicket'           : 'false',
            'globalOptInShown'                  : 'true',
            'globalOptInChecked'                : 'false',
            'mobile'                            : 'false',
            'connectLegalTerms'                 : 'true',
            'locationPromptShown'               : 'true',
            'showPassword'                      : 'true'
        }
        try:
            response = self.sso_rest_client.get(self.garmin_connect_sso_login, get_headers, params)
        except RestResponseException as e:
            root_logger.error("Exception during login get: %s", e)
            RestClient.save_binary_file('login_get.html', e.response)
            return False
        found = re.search(r"name=\"_csrf\" value=\"(\w*)", response.text, re.M)
        if not found:
            logger.error("_csrf not found: %s", response.status_code)
            RestClient.save_binary_file('login_get.html', response)
            return False
        logger.debug("_csrf found (%s).", found.group(1))

        data = {
            'username'  : username,
            'password'  : password,
            'embed'     : 'false',
            '_csrf'     : found.group(1)
        }
        post_headers = {
            'Referer'       : response.url,
            'Content-Type'  : 'application/x-www-form-urlencoded'
        }
        try:
            response = self.sso_rest_client.post(self.garmin_connect_sso_login, post_headers, params, data)
        except RestException as e:
            root_logger.error("Exception during login post: %s", e)
            return False
        found = re.search(r"\?ticket=([\w-]*)", response.text, re.M)
        if not found:
            logger.error("Login ticket not found (%d).", response.status_code)
            RestClient.save_binary_file('login_post.html', response)
            return False
        params = {
            'ticket' : found.group(1)
        }
        try:
            response = self.modern_rest_client.get('', params=params)
        except RestException:
            logger.error("Login get homepage failed (%d).", response.status_code)
            RestClient.save_binary_file('login_home.html', response)
            return False
        self.user_prefs = self.__get_json(response.text, 'VIEWER_USERPREFERENCES')
        if profile_dir:
            self.modern_rest_client.save_json_to_file(f'{profile_dir}/profile.json', self.user_prefs)
        self.display_name = self.user_prefs['displayName']
        self.social_profile = self.__get_json(response.text, 'VIEWER_SOCIAL_PROFILE')
        self.full_name = self.social_profile['fullName']
        root_logger.info("login: %s (%s)", self.full_name, self.display_name)
        return True

    def __unzip_files(self, outdir):
        """Unzip and downloaded zipped files into the directory supplied."""
        root_logger.info(" : from %s to %s", self.temp_dir, outdir)
        for filename in os.listdir(self.temp_dir):
            match = re.search(r'.*\.zip', filename)
            if match:
                full_pathname = f'{self.temp_dir}/{filename}'
                with zipfile.ZipFile(full_pathname, 'r') as files_zip:
                    try:
                        files_zip.extractall(outdir)
                    except Exception as e:
                        logger.error('Failed to unzip %s to %s: %s', full_pathname, outdir, e)

    def __get_activity_summaries(self, start, count):
        root_logger.info("get_activity_summaries")
        params = {
            'start' : str(start),
            "limit" : str(count),
            'search': 'bouldering'
        }
        try:
            response = self.modern_rest_client.get(self.garmin_connect_activity_search_url, params=params)
            return response.json()
        except RestException as e:
            root_logger.error("Exception getting activity summary: %s", e)

    def __save_activity_file(self, activity_id_str):
        root_logger.debug("save_activity_file: %s", activity_id_str)
        zip_filename = f'{self.temp_dir}/activity_{activity_id_str}.zip'
        url = f'activity/{activity_id_str}'
        try:
            self.download_service_rest_client.download_binary_file(url, zip_filename)
        except RestException as e:
            root_logger.error("Exception downloading activity file: %s", e)

    def get_activities(self, directory, count, overwite=False):
        """Download activities files from Garmin Connect and save the raw files."""
        print(directory)
        self.temp_dir = tempfile.mkdtemp()
        logger.info("Getting activities: '%s' (%d) temp %s", directory, count, self.temp_dir)
        activities = self.__get_activity_summaries(0, count)
        for activity in tqdm(activities or [], unit='activities'):
            activity_id_str = str(activity['activityId'])
            if not os.path.isfile(f'{directory}/{activity_id_str}.fit') or overwite:
                print(f"saving to {directory}/{activity_id_str}.fit")
                self.__save_activity_file(activity_id_str)
            # pause for a second between every page access
            time.sleep(1)
        self.__unzip_files(directory)



