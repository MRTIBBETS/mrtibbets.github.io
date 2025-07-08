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
        """MAKE HTTP REQUEST TO CLOUDFLARE API WITH ERROR HANDLING"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.request(method, url, headers=self.headers, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"ERROR MAKING REQUEST TO {endpoint}: {str(e)}")
            if hasattr(e.response, 'text'):
                print(f"RESPONSE: {e.response.text}")
            return None

    def apply_zone_settings(self) -> None:
        """APPLY ESSENTIAL ZONE SETTINGS FOR STATIC WEBSITE WITH SEARCH ENGINE OPTIMIZATION"""
        print("APPLYING ZONE SETTINGS...")
        
        # ESSENTIAL SETTINGS FOR STATIC WEBSITE - OPTIMIZED FOR SEARCH ENGINES
        settings = {
            "ssl": {"value": "full"},
            "security_level": {"value": "low"},  # LOW SECURITY TO ALLOW SEARCH ENGINES
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
            "rocket_loader": {"value": "off"},  # DISABLED FOR BETTER COMPATIBILITY
            "cache_level": {"value": "standard"},  # STANDARD CACHING FOR BETTER PERFORMANCE
            "browser_cache_ttl": {"value": 14400},  # 4 HOURS BROWSER CACHE
            "development_mode": {"value": "off"},
            "challenge_ttl": {"value": 2700},  # 45 MINUTES FOR CHALLENGES
            "privacy_pass": {"value": "on"},  # ENABLE PRIVACY PASS
            "opportunistic_encryption": {"value": "on"},  # ENABLE OPPORTUNISTIC ENCRYPTION
            "tls_client_auth": {"value": "off"},  # DISABLE CLIENT CERTIFICATE REQUIREMENT
            "websockets": {"value": "on"}  # ENABLE WEBSOCKETS
        }
        
        # APPLY EACH SETTING INDIVIDUALLY
        for setting, data in settings.items():
            print(f"SETTING {setting}...")
            result = self._make_request("PATCH", f"/zones/{self.zone_id}/settings/{setting}", data)
            if result and result.get("success"):
                print(f"✓ {setting} APPLIED SUCCESSFULLY")
            else:
                print(f"✗ FAILED TO APPLY {setting}")

    def apply_firewall_rules(self) -> None:
        """APPLY FIREWALL RULES THAT ALLOW SEARCH ENGINES WHILE BLOCKING MALICIOUS BOTS"""
        print("\nAPPLYING FIREWALL RULES...")
        
        # FIREWALL RULES OPTIMIZED FOR SEARCH ENGINE ACCESS
        rules = [
            {
                "description": "BLOCK ONLY KNOWN MALICIOUS BOTS",
                "expression": "(cf.client.bot and not cf.client.bot.category in {\"search engine crawler\" \"search engine bot\" \"search engine\"})",
                "action": "block",
                "paused": False,
                "ref": "rule_block_malicious_bots_only"
            },
            {
                "description": "ALLOW ALL SEARCH ENGINES",
                "expression": "(cf.client.bot.category in {\"search engine crawler\" \"search engine bot\" \"search engine\"})",
                "action": "allow",
                "paused": False,
                "ref": "rule_allow_search_engines"
            }
        ]
        
        # REMOVE EXISTING FIREWALL RULES
        existing_rules = self._make_request("GET", f"/zones/{self.zone_id}/firewall/rules")
        if existing_rules and "result" in existing_rules:
            for rule in existing_rules["result"]:
                print(f"DELETING EXISTING FIREWALL RULE: {rule.get('id')}")
                self._make_request("DELETE", f"/zones/{self.zone_id}/firewall/rules/{rule['id']}")

        # CREATE NEW FILTERS AND FIREWALL RULES
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
                    print(f"✓ CREATED FIREWALL RULE: {rule['description']}")
                else:
                    print(f"✗ FAILED TO CREATE FIREWALL RULE: {rule['description']}")

    def apply_page_rules(self) -> None:
        """APPLY PAGE RULES FOR BETTER PERFORMANCE AND SECURITY"""
        print("\nAPPLYING PAGE RULES...")
        
        # PAGE RULES FOR OPTIMIZED PERFORMANCE
        page_rules = [
            {
                "description": "FORCE HTTPS FOR ALL TRAFFIC",
                "targets": [{"target": "url", "constraint": {"operator": "matches", "value": "http://*/*"}}],
                "actions": [{"id": "always_use_https"}],
                "priority": 1,
                "status": "active"
            },
            {
                "description": "CACHE STATIC ASSETS AGGRESSIVELY",
                "targets": [{"target": "url", "constraint": {"operator": "matches", "value": "*.css"}}],
                "actions": [
                    {"id": "cache_level", "value": "cache_everything"},
                    {"id": "edge_cache_ttl", "value": 31536000}
                ],
                "priority": 2,
                "status": "active"
            }
        ]
        
        # REMOVE EXISTING PAGE RULES
        existing_rules = self._make_request("GET", f"/zones/{self.zone_id}/pagerules")
        if existing_rules and "result" in existing_rules:
            for rule in existing_rules["result"]:
                print(f"DELETING EXISTING PAGE RULE: {rule.get('id')}")
                self._make_request("DELETE", f"/zones/{self.zone_id}/pagerules/{rule['id']}")

        # CREATE NEW PAGE RULES
        for rule in page_rules:
            result = self._make_request("POST", f"/zones/{self.zone_id}/pagerules", rule)
            if result and result.get("success"):
                print(f"✓ CREATED PAGE RULE: {rule['description']}")
            else:
                print(f"✗ FAILED TO CREATE PAGE RULE: {rule['description']}")

def main():
    # CHECK FOR REQUIRED ENVIRONMENT VARIABLES
    api_token = os.getenv("CLOUDFLARE_API_TOKEN")
    zone_id = os.getenv("CLOUDFLARE_ZONE_ID")
    
    if not api_token or not zone_id:
        print("ERROR: PLEASE SET CLOUDFLARE_API_TOKEN AND CLOUDFLARE_ZONE_ID ENVIRONMENT VARIABLES")
        sys.exit(1)
    
    # INITIALIZE CONFIGURATOR AND APPLY SETTINGS
    configurator = CloudflareConfigurator(api_token, zone_id)
    
    try:
        configurator.apply_zone_settings()
        configurator.apply_firewall_rules()
        configurator.apply_page_rules()
        print("\nCONFIGURATION COMPLETED SUCCESSFULLY!")
    except Exception as e:
        print(f"\nERROR APPLYING SETTINGS: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 