import json
import secrets
import argparse
from datetime import datetime
from pathlib import Path

class APIKeyManager:
    def __init__(self, keys_file='api_keys.json'):
        self.keys_file = Path(keys_file)
        self.keys = self._load_keys()

    def _load_keys(self):
        if self.keys_file.exists():
            with open(self.keys_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_keys(self):
        with open(self.keys_file, 'w') as f:
            json.dump(self.keys, f, indent=4)

    def create_key(self, name, rate_limit=100):
        """Create a new API key"""
        if name in self.keys:
            raise ValueError(f"Key with name '{name}' already exists")

        api_key = secrets.token_hex(32)
        self.keys[api_key] = {
            "name": name,
            "created_at": datetime.now().isoformat(),
            "rate_limit": rate_limit,
            "total_requests": 0
        }
        self._save_keys()
        return api_key

    def delete_key(self, api_key):
        """Delete an API key"""
        if api_key in self.keys:
            del self.keys[api_key]
            self._save_keys()
            return True
        return False

    def list_keys(self):
        """List all API keys"""
        return self.keys

    def update_rate_limit(self, api_key, new_limit):
        """Update rate limit for an API key"""
        if api_key in self.keys:
            self.keys[api_key]["rate_limit"] = new_limit
            self._save_keys()
            return True
        return False

def main():
    parser = argparse.ArgumentParser(description='API Key Manager')
    parser.add_argument('action', choices=['create', 'delete', 'list', 'update'])
    parser.add_argument('--name', help='Name for the API key')
    parser.add_argument('--key', help='API key to delete or update')
    parser.add_argument('--rate-limit', type=int, help='Rate limit for the API key')

    args = parser.parse_args()
    manager = APIKeyManager()

    try:
        if args.action == 'create':
            if not args.name:
                print("Error: --name is required for create action")
                return
            rate_limit = args.rate_limit or 100
            api_key = manager.create_key(args.name, rate_limit)
            print(f"\nAPI Key created successfully!")
            print(f"Name: {args.name}")
            print(f"Key: {api_key}")
            print(f"Rate Limit: {rate_limit} requests per minute")

        elif args.action == 'delete':
            if not args.key:
                print("Error: --key is required for delete action")
                return
            if manager.delete_key(args.key):
                print(f"API key deleted successfully")
            else:
                print(f"API key not found")

        elif args.action == 'list':
            keys = manager.list_keys()
            print("\nAPI Keys:")
            for key, details in keys.items():
                print(f"\nName: {details['name']}")
                print(f"Key: {key}")
                print(f"Created: {details['created_at']}")
                print(f"Rate Limit: {details['rate_limit']} requests per minute")
                print(f"Total Requests: {details['total_requests']}")

        elif args.action == 'update':
            if not args.key or args.rate_limit is None:
                print("Error: --key and --rate-limit are required for update action")
                return
            if manager.update_rate_limit(args.key, args.rate_limit):
                print(f"Rate limit updated successfully")
            else:
                print(f"API key not found")

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
