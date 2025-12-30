import mock
import os
import pickle
import unittest

from Interceptor import Interceptor, PROXY_BIN, PROXY_PORT

TEST_MASTER_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'sample_master_data')
TEST_MASTER_FILE = os.path.join(TEST_MASTER_FOLDER, 'default_master.csv')
PREVIOUS_ERRORS_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), '.errors')


class TestInterceptorTestCase(unittest.TestCase):
    def setUp(self):
        self.traverse_obj = Interceptor()
        self.traverse_obj.robot_variables = {}

    def tearDown(self):
        try:
            os.remove(PREVIOUS_ERRORS_FILE)
        except OSError:
            pass

    @mock.patch('Interceptor.BuiltIn')
    def test_setup_interceptor_calls_setup_functions(self, builtin_mock):
        builtin_mock_obj = mock.MagicMock()
        builtin_mock_obj.get_variables.return_value = {'${SAMPLE_VAR}': 'VALUE'}
        builtin_mock.return_value = builtin_mock_obj
        self.traverse_obj.start_proxy = mock.MagicMock()
        self.traverse_obj.start_browser = mock.MagicMock()
        self.traverse_obj.set_screenshot_directory = mock.MagicMock()
        self.traverse_obj.setup_interceptor()
        self.assertEqual(builtin_mock.call_count, 1)
        self.assertEqual(self.traverse_obj.start_proxy.call_count, 1)
        self.assertEqual(self.traverse_obj.start_proxy.call_count, 1)
        self.assertEqual(self.traverse_obj.set_screenshot_directory.call_count, 1)

    # start_proxy
    @mock.patch('Interceptor.Server')
    def test_start_proxy_calls_proxy_server_with_default_bin_port(self, proxy_mock):
        self.traverse_obj.start_proxy()
        proxy_params, _ = proxy_mock.call_args_list[proxy_mock.call_count - 1]
        self.assertEqual(proxy_params, (PROXY_BIN, {'port': PROXY_PORT}))
        self.assertTrue(self.traverse_obj.server.start.called)
        self.assertTrue(self.traverse_obj.server.create_proxy.called)

    @mock.patch('Interceptor.Server')
    def test_start_proxy_calls_proxy_server_with_custom_bin_port(self, proxy_mock):
        self.traverse_obj.start_proxy('custom_bin', 'custom_port')
        proxy_params, _ = proxy_mock.call_args_list[proxy_mock.call_count - 1]
        self.assertEqual(proxy_params, ('custom_bin', {'port': 'custom_port'}))
        self.assertTrue(self.traverse_obj.server.start.called)
        self.assertTrue(self.traverse_obj.server.create_proxy.called)

    # start browser
    @mock.patch('Interceptor.webdriver')
    def test_start_browser_calls_webdriver_with_chrome_parameters_by_default(self, webdriver_mock):
        proxy_mock = mock.MagicMock(autospec=True)
        self.traverse_obj.proxy = proxy_mock
        self.traverse_obj.start_browser()
        self.assertTrue(webdriver_mock.ChromeOptions.called)
        self.assertTrue(webdriver_mock.Chrome.called)

    @mock.patch('Interceptor.webdriver')
    def test_start_browser_does_not_start_browser_when_non_chrome_param_passed(self, webdriver_mock):
        proxy_mock = mock.MagicMock(autospec=True)
        self.traverse_obj.proxy = proxy_mock
        self.traverse_obj.start_browser('ie')
        self.assertFalse(webdriver_mock.ChromeOptions.called)
        self.assertFalse(webdriver_mock.Chrome.called)

    # stop services
    def test_stop_services_stops_the_proxy_and_browser(self):
        self.traverse_obj.server = mock.MagicMock(autospec=True)
        self.traverse_obj.browser = mock.MagicMock(autospec=True)
        self.traverse_obj.stop_services()
        self.assertTrue(self.traverse_obj.server.stop.called)
        self.assertTrue(self.traverse_obj.browser.quit.called)

    # iterate_urls
    def test_iterate_urls_successfully_iterates_urls(self):
        self.traverse_obj.get_previous_errors = mock.MagicMock(return_value=[])
        self.traverse_obj.proxy = mock.MagicMock(auto_spec=True)
        self.traverse_obj.browser = mock.MagicMock(auto_spec=True)
        self.traverse_obj.verify_data = mock.MagicMock()
        self.traverse_obj.get_var = mock.MagicMock(return_value='false')
        self.traverse_obj.master_data['urlA'] = {}
        self.traverse_obj.iterate_urls()
        self.traverse_obj.proxy.new_har.assert_called_with('urlA')
        self.traverse_obj.browser.get.assert_called_with('urlA')
        self.traverse_obj.verify_data.assert_called_with('urlA')

    # verify_data
    @mock.patch('Interceptor.logging')
    def test_verify_data_successfully_iterates_all_data_calling_appropriate_helpers(self, mock_logging):
        self.traverse_obj.proxy = mock.MagicMock()
        self.traverse_obj.proxy.har = {'log': {'entries': [{'request': {'url': 'call_urlA'},
                                                            'response': {'status': 200}},
                                                           {'request': {'url': 'call_urlB'},
                                                            'response': {'status': 200}},
                                                           ]}}
        self.traverse_obj.master_data['urlA'] = {'call_urlA': {'status': 200, 'checked': False, 'queryString': {}}}
        self.traverse_obj._handle_request_params = mock.MagicMock()
        self.traverse_obj._handle_custom_params = mock.MagicMock()
        self.traverse_obj.verify_data('urlA')

        logging_param, _ = mock_logging.info.call_args_list[mock_logging.info.call_count - 1]
        request_param, _ = self.traverse_obj._handle_request_params.call_args_list[self.traverse_obj._handle_request_params.call_count-1]
        custom_param, _ = self.traverse_obj._handle_custom_params.call_args_list[self.traverse_obj._handle_custom_params.call_count-1]
        self.assertEqual(logging_param, ('\tConfirmed - Request Found for URL call_urlA',))
        self.assertEqual(request_param[1], {'request': {'url': 'call_urlA'}, 'response': {'status': 200}})
        self.assertEqual(custom_param, ({'status': 200, 'queryString': {}, 'checked': True}, {'request': {'url': 'call_urlA'}, 'response': {'status': 200}}))

    def test_verify_data_raises_exception_when_url_not_found(self):
        self.traverse_obj.proxy = mock.MagicMock()
        self.traverse_obj.proxy.har = {'log': {'entries': [{'request': {'url': 'call_urlA'},
                                                            'response': {'status': 200}},
                                                           {'request': {'url': 'call_urlB'},
                                                            'response': {'status': 200}},
                                                           ]}}
        self.traverse_obj.master_data['urlA'] = {'call_urlC': {'status': 200, 'checked': False, 'queryString': {}}}
        self.traverse_obj._handle_request_params = mock.MagicMock()
        self.traverse_obj._handle_custom_params = mock.MagicMock()
        try:
            self.traverse_obj.verify_data('urlA')
        except AssertionError as error:
            self.assertEquals(error.message, '\tERROR - Request NOT Found for URL call_urlC')

    # _handle_request_params
    @mock.patch('Interceptor.logging')
    def test_handle_request_params_checks_all_params_within_query_string_to_har(self, mock_logging):
        har_entry = {'request': {'url': 'call_urlA', 'queryString': [{'name': 'q1', 'value': 'v1'},
                                                                     {'name': 'q2', 'value': 'q2'},
                                                                     {'name': 'q3', 'value': 'v3'}]}}
        query_string_data = [{'name': 'q1', 'value': 'v1'},
                             {'name': 'q3', 'value': 'v3'}]
        self.traverse_obj._handle_request_params(query_string_data, har_entry)
        self.assertEqual(mock_logging.info.call_args_list[mock_logging.info.call_count - 2][0],
                         ('\t\tConfirmed - Param: q1 value matched Value: v1',))
        self.assertEqual(mock_logging.info.call_args_list[mock_logging.info.call_count - 1][0],
                         ('\t\tConfirmed - Param: q3 value matched Value: v3',))

    @mock.patch('Interceptor.logging')
    def test_handle_request_params_raises_exception_when_any_value_does_not_match(self, mock_logging):
        har_entry = {'request': {'url': 'call_urlA', 'queryString': [{'name': 'q1', 'value': 'v1'},
                                                                     {'name': 'q2', 'value': 'q2'},
                                                                     {'name': 'q3', 'value': 'v3'}]}}
        query_string_data = [{'name': 'q1', 'value': 'v1'},
                             {'name': 'q3', 'value': 'v5'}]

        try:
            self.traverse_obj._handle_request_params(query_string_data, har_entry)
        except AssertionError as error:
            self.assertEquals(error.message, '\t\tERROR - Param: q3 value did not match. Master Value: v5, '
                                             'Request Value: v3, Data: {"request": {"url": "call_urlA", "queryString": '
                                             '[{"name": "q1", "value": "v1"}, {"name": "q2", "value": "q2"}, '
                                             '{"name": "q3", "value": "v3"}]}}')

        self.assertEqual(mock_logging.info.call_args_list[mock_logging.info.call_count - 1][0],
                         ('\t\tConfirmed - Param: q1 value matched Value: v1',))

    # _handle_custom_params
    @mock.patch('Interceptor.logging')
    def test_handle_custom_params_all_custom_params_within_to_har(self, mock_logging):
        har_entry = {'request': {'url': 'call_urlA', 'queryString': [{'name': 'q1', 'value': 'v1'}]},
                     'response': {'custom_response': {'another_layer': 'value1'}}}
        url_data = {'custom': [{'key': 'response:custom_response:another_layer', 'data': 'value1'},
                               {'key': 'request:url', 'data': 'call_urlA'}]}
        self.traverse_obj._handle_custom_params(url_data, har_entry)
        self.assertEqual(mock_logging.info.call_args_list[mock_logging.info.call_count - 2][0],
                         ('\t\tConfirmed - Path: response:custom_response:another_layer value matched Value: value1',))
        self.assertEqual(mock_logging.info.call_args_list[mock_logging.info.call_count - 1][0],
                         ('\t\tConfirmed - Path: request:url value matched Value: call_urlA',))

    @mock.patch('Interceptor.logging')
    def test_handle_custom_params_raises_exception_when_custom_value_does_not_match(self, mock_logging):
        har_entry = {'request': {'url': 'call_urlA', 'queryString': [{'name': 'q1', 'value': 'v1'}]},
                     'response': {'custom_response': {'another_layer': 'value1'}}}
        url_data = {'custom': [{'key': 'response:custom_response:another_layer', 'data': 'value2'},
                               {'key': 'request:url', 'data': 'call_urlA'}]}
        try:
            self.traverse_obj._handle_custom_params(url_data, har_entry)
        except AssertionError as error:
            self.assertEquals(error.message, '\t\tERROR - Path: response:custom_response:another_layer. Master Value: '
                                             'value2, Actual Value: value1, Data: {"request": {"url": "call_urlA", '
                                             '"queryString": [{"name": "q1", "value": "v1"}]}, "response": '
                                             '{"custom_response": {"another_layer": "value1"}}}')

    # get_var tests
    def test_get_var_with_valid_variable_returns_variable_value_from_robot_framework(self):
        self.traverse_obj.robot_variables = {'${SAMPLE_VAR}': 'VALUE'}
        robot_var = self.traverse_obj.get_var('sample_var')
        self.assertEqual(robot_var, 'VALUE')

    def test_get_var_with_unrecognized_variable_returns_empty_from_robot_framework(self):
        robot_var = self.traverse_obj.get_var('random_var')
        self.assertEqual(robot_var, '')

    # update_previous_errors_marker_file tests
    def test_marker_file_gets_created_with_list_of_error_ids(self):

        self.traverse_obj.update_previous_errors_marker_file([1, 2, 3], PREVIOUS_ERRORS_FILE)
        with open(PREVIOUS_ERRORS_FILE, 'r') as error_file:
            error_file_contents = pickle.load(error_file)
            self.assertEqual(error_file_contents, [1, 2, 3])

    def test_marker_file_gets_created_when_empty_string_passed_in_as_error_ids(self):

        self.traverse_obj.update_previous_errors_marker_file('', PREVIOUS_ERRORS_FILE)
        with open(PREVIOUS_ERRORS_FILE, 'r') as error_file:
            error_file_contents = pickle.load(error_file)
            self.assertEqual(error_file_contents, '')

    # get_previous_errors tests
    def test_get_previous_errors_returns_error_file_contents(self):

        with open(PREVIOUS_ERRORS_FILE, 'w') as error_file:
            pickle.dump([100, 200, 300], error_file)
        error_file_contents = self.traverse_obj.get_previous_errors(PREVIOUS_ERRORS_FILE)
        self.assertEqual(error_file_contents, [100, 200, 300])

    def test_get_previous_errors_returns_empty_string_when_error_file_does_not_exist(self):

        tmp_error_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), '.tmp_error_file')
        error_file_contents = self.traverse_obj.get_previous_errors(previous_error_file=tmp_error_file)
        self.assertEqual(error_file_contents, '')

    # _set_trace tests
    @mock.patch('Interceptor.pdb')
    def test_set_trace_calls_pdb_set_trace(self, mock_pdb):

        mock_pdb.set_trace = mock.MagicMock()
        self.traverse_obj._set_trace()
        self.assertEquals(mock_pdb.set_trace.call_count, 1)
