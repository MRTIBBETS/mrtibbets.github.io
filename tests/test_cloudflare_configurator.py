import unittest
from unittest.mock import patch, MagicMock, ANY

from apply_cloudflare_settings import CloudflareConfigurator


class TestMakeRequest(unittest.TestCase):
    @patch('apply_cloudflare_settings.requests.request')
    def test_make_request_builds_url_and_headers(self, mock_request):
        cfg = CloudflareConfigurator('token', 'zone')
        mock_response = MagicMock()
        mock_response.json.return_value = {'ok': True}
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response

        result = cfg._make_request('GET', '/endpoint', {'k': 'v'})

        mock_request.assert_called_once_with(
            'GET',
            'https://api.cloudflare.com/client/v4/endpoint',
            headers=cfg.headers,
            json={'k': 'v'}
        )
        self.assertEqual(result, {'ok': True})


class TestApplyMethods(unittest.TestCase):
    @patch.object(CloudflareConfigurator, '_make_request', return_value={'success': True})
    def test_apply_zone_settings_invokes_each_endpoint(self, mock_request):
        cfg = CloudflareConfigurator('token', 'zone')
        cfg.apply_zone_settings()

        expected_settings = {
            'ssl',
            'security_level',
            'minify',
            'brotli',
            'http3',
            'always_use_https',
            'automatic_https_rewrites',
            'always_online',
            'rocket_loader',
            'cache_level',
            'browser_cache_ttl',
            'development_mode',
            'challenge_ttl',
            'privacy_pass',
            'opportunistic_encryption',
            'tls_client_auth',
            'websockets'
        }
        called_endpoints = {call.args[1] for call in mock_request.call_args_list}
        self.assertEqual(
            called_endpoints,
            {f'/zones/zone/settings/{setting}' for setting in expected_settings}
        )
        for call in mock_request.call_args_list:
            self.assertEqual(call.args[0], 'PATCH')

    @patch.object(CloudflareConfigurator, '_make_request')
    def test_apply_firewall_rules_invokes_api_sequence(self, mock_request):
        mock_request.side_effect = [
            {'result': [{'id': '1'}], 'success': True},  # GET existing rules
            {'success': True},  # DELETE existing rule
            {'success': True, 'result': [{'id': 'filter-id-1'}]},  # filter for rule 1
            {'success': True},  # firewall rule 1
            {'success': True, 'result': [{'id': 'filter-id-2'}]},  # filter for rule 2
            {'success': True}  # firewall rule 2
        ]
        cfg = CloudflareConfigurator('token', 'zone')
        cfg.apply_firewall_rules()

        expected = [
            ('GET', f'/zones/zone/firewall/rules'),
            ('DELETE', f'/zones/zone/firewall/rules/1'),
            ('POST', f'/zones/zone/filters'),
            ('POST', f'/zones/zone/firewall/rules'),
            ('POST', f'/zones/zone/filters'),
            ('POST', f'/zones/zone/firewall/rules')
        ]
        actual = [(c.args[0], c.args[1]) for c in mock_request.call_args_list]
        self.assertEqual(actual, expected)


if __name__ == '__main__':
    unittest.main()
