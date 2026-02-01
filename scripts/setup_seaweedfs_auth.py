#!/usr/bin/env python3
"""
Setup SeaweedFS S3 authentication by creating access keys via IAM API.

This script creates access keys for SeaweedFS S3 API and outputs them
for use in your .env file or config.yaml.

Usage:
    python scripts/setup_seaweedfs_auth.py [--endpoint URL] [--identity IDENTITY] [--output-format FORMAT]

Examples:
    # Create keys with default settings
    python scripts/setup_seaweedfs_auth.py

    # Create keys for specific identity
    python scripts/setup_seaweedfs_auth.py --identity admin

    # Output in .env format
    python scripts/setup_seaweedfs_auth.py --output-format env

    # Output in YAML format
    python scripts/setup_seaweedfs_auth.py --output-format yaml
"""
import argparse
import json
import sys
from urllib.parse import urljoin
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError


def create_access_key(endpoint, identity="admin"):
    """
    Create an access key via SeaweedFS IAM API.
    
    Args:
        endpoint: SeaweedFS S3/IAM endpoint URL (e.g., http://localhost:8333)
        identity: Identity name for the access key (default: "admin")
    
    Returns:
        dict: Response containing access_key_id and secret_access_key
    """
    url = urljoin(endpoint.rstrip('/') + '/', f'iam/createAccessKey?identity={identity}')
    
    try:
        request = Request(url, method='POST')
        with urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data
    except HTTPError as e:
        print(f"Error: HTTP {e.code} - {e.reason}", file=sys.stderr)
        if e.code == 404:
            print("Make sure SeaweedFS is running and IAM API is enabled.", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"Error: Could not connect to SeaweedFS at {endpoint}", file=sys.stderr)
        print(f"Details: {e.reason}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON response from SeaweedFS", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
        sys.exit(1)


def format_output(data, output_format):
    """Format the access key data for output."""
    access_key_id = data.get('accessKeyId', '')
    secret_access_key = data.get('secretAccessKey', '')
    
    if not access_key_id or not secret_access_key:
        print("Error: Invalid response from SeaweedFS IAM API", file=sys.stderr)
        print(f"Response: {data}", file=sys.stderr)
        sys.exit(1)
    
    if output_format == 'env':
        print("# SeaweedFS S3 Access Keys (add to .env file)")
        print(f"storage.s3.access_key_id={access_key_id}")
        print(f"storage.s3.secret_access_key={secret_access_key}")
    elif output_format == 'yaml':
        print("# SeaweedFS S3 Access Keys (add to config.yaml)")
        print("storage:")
        print("  s3:")
        print(f"    access_key_id: {access_key_id}")
        print(f"    secret_access_key: {secret_access_key}")
    else:  # default/json
        print(json.dumps({
            'access_key_id': access_key_id,
            'secret_access_key': secret_access_key
        }, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description='Create SeaweedFS S3 access keys via IAM API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--endpoint',
        default='http://localhost:8333',
        help='SeaweedFS S3/IAM endpoint URL (default: http://localhost:8333)'
    )
    parser.add_argument(
        '--identity',
        default='admin',
        help='Identity name for the access key (default: admin)'
    )
    parser.add_argument(
        '--output-format',
        choices=['env', 'yaml', 'json'],
        default='json',
        help='Output format (default: json)'
    )
    
    args = parser.parse_args()
    
    print(f"Creating access key for identity '{args.identity}'...", file=sys.stderr)
    print(f"Connecting to {args.endpoint}...", file=sys.stderr)
    
    data = create_access_key(args.endpoint, args.identity)
    
    print("\n✓ Access key created successfully!\n", file=sys.stderr)
    format_output(data, args.output_format)
    
    print("\n⚠️  IMPORTANT: Save these credentials securely!", file=sys.stderr)
    print("   Add them to your .env file or config.yaml", file=sys.stderr)


if __name__ == '__main__':
    main()
