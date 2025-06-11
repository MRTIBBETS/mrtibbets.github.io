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
        """Apply zone settings"""
        print("Applying zone settings...")
        
        # Define supported settings
        settings = {
            "ssl": {"value": "full"},
            "security_level": {"value": "medium"},
            "minify": {
                "value": {
                    "css": True,
                    "html": True,
                    "js": True
                }
            },
            "brotli": {"value": "on"},
            "http3": {"value": "on"},
            "early_hints": {"value": "on"},
            "always_use_https": {"value": "on"},
            "automatic_https_rewrites": {"value": "on"},
            "always_online": {"value": "on"},
            "rocket_loader": {"value": "on"}
        }
        
        # Apply each setting
        for setting, data in settings.items():
            print(f"Setting {setting}...")
            result = self._make_request("PATCH", f"/zones/{self.zone_id}/settings/{setting}", data)
            if result and result.get("success"):
                print(f"✓ {setting} applied successfully")
            else:
                print(f"✗ Failed to apply {setting}")

    def apply_page_rules(self) -> None:
        """Apply page rules"""
        print("\nApplying page rules...")
        print("Note: Page Rules require a zone-level API token. Skipping this step.")
        print("Please create a zone-level API token with the following permissions:")
        print("- Zone > Page Rules > Edit")
        print("Then run this script again with the new token.")

    def apply_firewall_rules(self) -> None:
        """Apply firewall rules using filters as required by Cloudflare API"""
        print("\nApplying firewall rules...")
        
        # Define firewall rules and their filter expressions
        rules = [
            {
                "description": "Block known bad bots",
                "expression": "(cf.client.bot)",
                "action": "block",
                "paused": False,
                "ref": "rule_block_known_bad_bots"
            },
            {
                "description": "Block high threat IPs",
                "expression": "(cf.threat_score gt 10)",
                "action": "block",
                "paused": False,
                "ref": "rule_block_high_threat_ips"
            }
        ]
        
        # Get existing rules
        existing_rules = self._make_request("GET", f"/zones/{self.zone_id}/firewall/rules")
        if existing_rules and "result" in existing_rules:
            for rule in existing_rules["result"]:
                print(f"Deleting existing firewall rule: {rule.get('id')}")
                self._make_request("DELETE", f"/zones/{self.zone_id}/firewall/rules/{rule['id']}")

        # Get existing filters
        existing_filters = self._make_request("GET", f"/zones/{self.zone_id}/filters")
        existing_filter_ids = set()
        if existing_filters and "result" in existing_filters:
            for f in existing_filters["result"]:
                existing_filter_ids.add(f["id"])

        # Create filters and collect their IDs
        filter_ids = []
        for rule in rules:
            filter_payload = {
                "expression": rule["expression"],
                "description": rule["description"]
            }
            filter_result = self._make_request("POST", f"/zones/{self.zone_id}/filters", [filter_payload])
            if filter_result and filter_result.get("success") and filter_result.get("result"):
                filter_id = filter_result["result"][0]["id"]
                filter_ids.append(filter_id)
                print(f"✓ Created filter for: {rule['description']}")
            else:
                print(f"✗ Failed to create filter for: {rule['description']}")
                filter_ids.append(None)

        # Create firewall rules referencing the filters
        firewall_payload = []
        for rule, filter_id in zip(rules, filter_ids):
            if filter_id:
                firewall_payload.append({
                    "filter": {"id": filter_id},
                    "action": rule["action"],
                    "description": rule["description"],
                    "paused": rule["paused"],
                    "ref": rule["ref"]
                })
        if firewall_payload:
            result = self._make_request("POST", f"/zones/{self.zone_id}/firewall/rules", firewall_payload)
            if result and result.get("success"):
                print(f"✓ Firewall rules created successfully")
            else:
                print(f"✗ Failed to create firewall rules")
        else:
            print("No valid filters to create firewall rules.")

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
        configurator.apply_page_rules()
        configurator.apply_firewall_rules()
        print("\nConfiguration completed!")
    except Exception as e:
        print(f"\nError applying settings: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 