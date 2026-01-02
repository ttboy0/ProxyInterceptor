import collections
import csv
import httplib
import json
import logging
import os
import pdb
import pickle
import sys
from selenium.webdriver.common.proxy import *

from browsermobproxy import Server
from selenium import webdriver
from Selenium2Library import Selenium2Library
from robot.libraries.BuiltIn import BuiltIn

PARENT_DIRECTORY = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)
SCREENSHOTS_DIRECTORY = os.path.join(PARENT_DIRECTORY, 'screenshots')
CONFIG_FILE = os.path.join(PARENT_DIRECTORY, 'resources', 'master.csv')
PROXY_PORT = 8082
PROXY_BIN = os.path.join(os.getcwd(), 'bin', 'browsermob-proxy', 'bin', 'browsermob-proxy')
PREVIOUS_ERRORS_FILE = os.path.join(PARENT_DIRECTORY, '.errors')
FIREFOX_PROFILE = os.path.join(PARENT_DIRECTORY, 'firefox_profile')

MASTER_DATA_INDEX = {'URL': 0, 'CALL_URL': 1, 'QUERYSTRING_LOC': 2, 'STATUS': 3,
                     'CUSTOM_KEY': 4}


class Interceptor(Selenium2Library):
    def __init__(self):
        super(Interceptor, self).__init__()
        self.master_data = collections.OrderedDict()
        self.log_prefix = ''
        self.num_cards_tested = 0
        self.robot_variables = {}

    def setup_interceptor(self):
        self.start_proxy()
        self.start_browser()
        self.set_screenshot_directory(SCREENSHOTS_DIRECTORY)
        self.robot_variables = BuiltIn().get_variables()

    def start_proxy(self, proxy_binary=PROXY_BIN, proxy_port=PROXY_PORT):
        self.server = Server(proxy_binary, {'port': proxy_port})
        self.server.start()
        self.proxy = self.server.create_proxy()

    def start_browser(self, browser_type="chrome"):
        if browser_type == "chrome":
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument(
                "--proxy-server={0}".format(self.proxy.proxy))
            self.browser = webdriver.Chrome(chrome_options=chrome_options)
        if browser_type == "firefox":
            profile = webdriver.FirefoxProfile(profile_directory=FIREFOX_PROFILE)
            profile.set_proxy(self.proxy.selenium_proxy())
            profile.accept_untrusted_certs = True
            profile.assume_untrusted_cert_issuer = False
            profile.set_preference('security.ssl.enable_ocsp_stapling', False)
            profile.set_preference('security.tls.insecure_fallback_hosts', 'www.bmo.com')
            profile.update_preferences()
            self.browser = webdriver.Firefox(firefox_profile=profile, proxy=self.proxy)
        if browser_type == 'ie':
            desired_capabilities = webdriver.DesiredCapabilities.INTERNETEXPLORER
            desired_capabilities['acceptSslCerts'] = True
            desired_capabilities['INTRODUCE_FLAKINESS_BY_IGNORING_SECURITY_DOMAINS'] = True
            desired_capabilities['ignoreProtectedModeSettings'] = True
            desired_capabilities["ie.ensureCleanSession"] = True
            desired_capabilities['proxy'] = {"httpProxy": self.proxy.proxy, "ftpProxy": self.proxy.proxy,
                                             "sslProxy": self.proxy.proxy,
                                             "noProxy": None,
                                             "proxyType": "MANUAL",
                                             "class": "org.openqa.selenium.Proxy",
                                             "autodetect": False
                                             }
            self.browser = webdriver.Ie(capabilities=desired_capabilities)

    def stop_services(self):
        self.server.stop()
        self.browser.quit()

    def update_master_data(self, config_file=CONFIG_FILE):
        url_key = ""
        with open(config_file, 'rb') as csvfile:
            reader = csv.reader(csvfile)
            for index, row in enumerate(reader):
                if index > 0:
                    if row[MASTER_DATA_INDEX['URL']] != "":
                        url_key = row[MASTER_DATA_INDEX['URL']]

                    if row[MASTER_DATA_INDEX['CALL_URL']] != "":
                        call_url = row[MASTER_DATA_INDEX['CALL_URL']]

                    if url_key not in self.master_data.keys():
                        self.master_data[url_key] = {}

                    if call_url not in self.master_data[url_key].keys():
                        self.master_data[url_key][call_url] = {
                            "queryString": [], "checked": False, "custom": []}

                    if row[MASTER_DATA_INDEX['QUERYSTRING_LOC']] != "":
                        query_param = row[MASTER_DATA_INDEX['QUERYSTRING_LOC']].split(":", 1)
                        self.master_data[url_key][call_url][
                            "queryString"].append({'name': query_param[0], 'value': query_param[1]})

                    if row[MASTER_DATA_INDEX['STATUS']] != "":
                        self.master_data[url_key][call_url]['status'] = row[MASTER_DATA_INDEX['STATUS']]

                    if len(row) > MASTER_DATA_INDEX['CUSTOM_KEY'] + 1 and row[MASTER_DATA_INDEX['CUSTOM_KEY']] != "":
                        self.master_data[url_key][call_url]["custom"].append(
                            {'key': row[MASTER_DATA_INDEX['CUSTOM_KEY']],
                             'data': row[MASTER_DATA_INDEX['CUSTOM_KEY'] + 1]})

    def iterate_urls(self):
        error_row_ids = []
        previous_errors = self.get_previous_errors()
        for url, url_data in self.master_data.iteritems():
            if all([self.get_var('rerun_failed').lower() == 'true', previous_errors, url not in previous_errors]):
                continue
            logging.info("Checking Source URL: {}".format(url))
            try:
                self.proxy.new_har(url)
                self.browser.get(url)
                self.verify_data(url)
            except Exception as e:
                error_row_ids.append(url)
                logging.error(e)

        if len(error_row_ids) > 0:
            self.update_previous_errors_marker_file(error_row_ids)
            raise AssertionError('Several errors have occurred. Please review the Failed test cases above')
        logging.info('Successfully Tested: {num_cards} Cards'.format(num_cards=self.num_cards_tested))
        # remove the error file if we've run the tests successfully.
        if os.path.isfile(PREVIOUS_ERRORS_FILE):
            os.remove(PREVIOUS_ERRORS_FILE)

    def update_previous_errors_marker_file(self, error_row_ids, previous_error_file=PREVIOUS_ERRORS_FILE):
        if os.path.isfile(previous_error_file):
            os.remove(previous_error_file)
        with open(previous_error_file, 'w') as error_file:
            pickle.dump(error_row_ids, error_file)

    def get_previous_errors(self, previous_error_file=PREVIOUS_ERRORS_FILE):
        try:
            with open(previous_error_file, 'r') as error_file:
                return pickle.load(error_file)
        except IOError:
            return ''

    def get_var(self, var_name):
        var_name = '${{{0}}}'.format(var_name)
        return self.robot_variables.get(var_name.upper(), "")

    def verify_data(self, url):
        for call_url, url_data in self.master_data[url].iteritems():
            url_found = False
            for har_entry in self.proxy.har['log']['entries']:
                valid_har_entry = [har_entry['request']['url'].startswith(call_url),
                                   har_entry['response']['status'] == int(url_data.get('status', httplib.OK)),
                                   not url_data['checked']]
                if all(valid_har_entry):
                    url_found = True
                    url_data['checked'] = True
                    logging.info("\tConfirmed - Request Found for URL {}".format(call_url))
                    self._handle_request_params(url_data.get('queryString'), har_entry)
                    self._handle_custom_params(url_data, har_entry)
            if not url_found:
                raise AssertionError("\tERROR - Request NOT Found for URL {}".format(call_url))

    def _handle_request_params(self, query_string_data, har_entry):
        for query_param in query_string_data:
            param_check = False
            actual_param_value = ""
            for actual_query_param in har_entry['request']['queryString']:
                if actual_query_param['name'] == query_param['name']:
                    actual_param_value = actual_query_param['value']
                    if actual_param_value == query_param['value']:
                        param_check = True
            if param_check:
                logging.info("\t\tConfirmed - Param: {} value matched Value: {}".format(query_param['name'],
                                                                                        query_param['value']))
            else:
                raise AssertionError(
                    "\t\tERROR - Param: {} value did not match. Master Value: {}, Request Value: {}, Data: {}".format(
                        query_param['name'],
                        query_param['value'],
                        actual_param_value,
                        json.dumps(har_entry)))

    def _handle_custom_params(self, url_data, har_entry):
        for custom_data in url_data['custom']:
            custom_key_path = custom_data['key'].split(":")
            custom_path_length = len(custom_key_path) - 1
            custom_key_value = custom_data['data']
            current_path = har_entry
            for index, key in enumerate(custom_key_path):
                if (type(current_path) is dict and key in current_path.keys()) or \
                        (type(current_path) is str and index == custom_path_length):
                    if index == custom_path_length:
                        current_path_value = str(current_path[key])
                        if custom_key_value in current_path_value:
                            logging.info("\t\tConfirmed - Path: {} value matched Value: {}".format(custom_data['key'],
                                                                                                   custom_key_value))
                        else:
                            raise AssertionError(
                                "\t\tERROR - Path: {}. Master Value: {}, Actual Value: {}, Data: {}".format(
                                    custom_data['key'],
                                    custom_key_value,
                                    current_path_value,
                                    json.dumps(har_entry)))
                    else:
                        current_path = current_path[key]
                else:
                    raise AssertionError("\t\tERROR - Path '{}' does not exist, Data: {}".format(custom_data['key'],
                                                                                                 json.dumps(har_entry)))

    def _handle_ie_alert(self):
        try:
            self.browser.switch_to.alert.accept()
        except Exception as e:
            pass

    def _handle_ssl_warning(self):
        try:
            self.browser.find_element_by_id('overridelink').click()
            self._handle_ie_alert()
        except:
            pass

    def _set_trace(self):
        for attr in ('stdin', 'stdout', 'stderr'):
            setattr(sys, attr, getattr(sys, '__%s__' % attr))
        pdb.set_trace()
