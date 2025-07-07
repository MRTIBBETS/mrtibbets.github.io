#!/usr/bin/env python3

import json
import os
import requests
from typing import Dict, Any
import sys

class CloudflareConfigurator:
    def __init__(self, api_token: str, zone_id: str):
        self.api_token = api_token
        self.zone_id = zone_id
        self.base_url = "https://api.cloudflare.com/client/v4"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }

    def _make_request(self, method: str, endpoint: str, data: Dict[str, Any] = None) -> Dict:
        """Make a request to the Cloudflare API"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.request(method, url, headers=self.headers, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error making request to {endpoint}: {str(e)}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return None

    def apply_zone_settings(self) -> None:
        """Apply essential zone settings for a static website"""
        print("Applying zone settings...")
        
        # Essential settings for static website - Less restrictive for search engines
        settings = {
            "ssl": {"value": "full"},
            "security_level": {"value": "low"},  # Changed from medium to low
            "minify": {
                "value": {
                    "css": True,
                    "html": True,
                    "js": True
                }
            },
            "brotli": {"value": "on"},
            "http3": {"value": "on"},
            "always_use_https": {"value": "on"},
            "automatic_https_rewrites": {"value": "on"},
            "always_online": {"value": "on"},
            "rocket_loader": {"value": "off"},  # Changed from on to off for better compatibility
            "cache_level": {"value": "standard"},  # Changed from aggressive to standard
            "browser_cache_ttl": {"value": 14400},  # 4 hours
            "development_mode": {"value": "off"},
            "challenge_ttl": {"value": 2700},  # 45 minutes for challenges
            "privacy_pass": {"value": "on"},  # Enable Privacy Pass
            "opportunistic_encryption": {"value": "on"},  # Enable opportunistic encryption
            "tls_client_auth": {"value": "off"},  # Disable client certificate requirement
            "websockets": {"value": "on"}  # Enable WebSockets
        }
        
        # Apply each setting
        for setting, data in settings.items():
            print(f"Setting {setting}...")
            result = self._make_request("PATCH", f"/zones/{self.zone_id}/settings/{setting}", data)
            if result and result.get("success"):
                print(f"✓ {setting} applied successfully")
            else:
                print(f"✗ Failed to apply {setting}")

    def apply_firewall_rules(self) -> None:
        """Apply essential firewall rules for a static website"""
        print("\nApplying firewall rules...")
        
        # Less restrictive firewall rules for better search engine access
        rules = [
            {
                "description": "Block only known malicious bots",
                "expression": "(cf.client.bot and not cf.client.bot.category in {\"search engine crawler\" \"search engine bot\" \"search engine\"})",
                "action": "block",
                "paused": False,
                "ref": "rule_block_malicious_bots_only"
            },
            {
                "description": "Allow all search engines",
                "expression": "(cf.client.bot.category in {\"search engine crawler\" \"search engine bot\" \"search engine\"})",
                "action": "allow",
                "paused": False,
                "ref": "rule_allow_search_engines"
            }
        ]
        
        # Get existing rules
        existing_rules = self._make_request("GET", f"/zones/{self.zone_id}/firewall/rules")
        if existing_rules and "result" in existing_rules:
            for rule in existing_rules["result"]:
                print(f"Deleting existing firewall rule: {rule.get('id')}")
                self._make_request("DELETE", f"/zones/{self.zone_id}/firewall/rules/{rule['id']}")

        # Create filters and rules
        for rule in rules:
            filter_payload = {
                "expression": rule["expression"],
                "description": rule["description"]
            }
            filter_result = self._make_request("POST", f"/zones/{self.zone_id}/filters", [filter_payload])
            if filter_result and filter_result.get("success") and filter_result.get("result"):
                filter_id = filter_result["result"][0]["id"]
                firewall_payload = [{
                    "filter": {"id": filter_id},
                    "action": rule["action"],
                    "description": rule["description"],
                    "paused": rule["paused"],
                    "ref": rule["ref"]
                }]
                result = self._make_request("POST", f"/zones/{self.zone_id}/firewall/rules", firewall_payload)
                if result and result.get("success"):
                    print(f"✓ Created firewall rule: {rule['description']}")
                else:
                    print(f"✗ Failed to create firewall rule: {rule['description']}")

    def apply_page_rules(self) -> None:
        """Apply page rules for better performance and security"""
        print("\nApplying page rules...")
        
        # Page rules for better performance
        page_rules = [
            {
                "description": "Force HTTPS for all traffic",
                "targets": [{"target": "url", "constraint": {"operator": "matches", "value": "http://*/*"}}],
                "actions": [{"id": "always_use_https"}],
                "priority": 1,
                "status": "active"
            },
            {
                "description": "Cache static assets aggressively",
                "targets": [{"target": "url", "constraint": {"operator": "matches", "value": "*.css"}}],
                "actions": [
                    {"id": "cache_level", "value": "cache_everything"},
                    {"id": "edge_cache_ttl", "value": 31536000}
                ],
                "priority": 2,
                "status": "active"
            }
        ]
        
        # Get existing page rules
        existing_rules = self._make_request("GET", f"/zones/{self.zone_id}/pagerules")
        if existing_rules and "result" in existing_rules:
            for rule in existing_rules["result"]:
                print(f"Deleting existing page rule: {rule.get('id')}")
                self._make_request("DELETE", f"/zones/{self.zone_id}/pagerules/{rule['id']}")

        # Create page rules
        for rule in page_rules:
            result = self._make_request("POST", f"/zones/{self.zone_id}/pagerules", rule)
            if result and result.get("success"):
                print(f"✓ Created page rule: {rule['description']}")
            else:
                print(f"✗ Failed to create page rule: {rule['description']}")

def main():
    # Check for required environment variables
    api_token = os.getenv("CLOUDFLARE_API_TOKEN")
    zone_id = os.getenv("CLOUDFLARE_ZONE_ID")
    
    if not api_token or not zone_id:
        print("Error: Please set CLOUDFLARE_API_TOKEN and CLOUDFLARE_ZONE_ID environment variables")
        sys.exit(1)
    
    # Initialize configurator
    configurator = CloudflareConfigurator(api_token, zone_id)
    
    # Apply settings
    try:
        configurator.apply_zone_settings()
        configurator.apply_firewall_rules()
        configurator.apply_page_rules()
        print("\nConfiguration completed!")
    except Exception as e:
        print(f"\nError applying settings: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 