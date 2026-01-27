# SeaweedFS S3 Authentication Setup

This guide explains how to set up authentication for SeaweedFS S3 API in the Gallery application.

## Overview

SeaweedFS provides S3-compatible API with embedded IAM (Identity and Access Management) for authentication. Unlike traditional S3 services, SeaweedFS doesn't have default credentials - you need to create access keys via the IAM API after starting the service.

## Quick Start

### 1. Start SeaweedFS

Start your Docker services:

```bash
# For VPS deployment
make docker-up-vps

# Or for local development
make docker-up
```

Wait for SeaweedFS to be ready (check with `docker-compose ps` or `make docker-ps`).

### 2. Create Access Keys

Use the provided script to create access keys:

```bash
# Using the script (recommended)
python scripts/setup_seaweedfs_auth.py

# Or with custom endpoint
python scripts/setup_seaweedfs_auth.py --endpoint http://localhost:8333

# Output in .env format
python scripts/setup_seaweedfs_auth.py --output-format env

# Output in YAML format
python scripts/setup_seaweedfs_auth.py --output-format yaml
```

### 3. Configure Credentials

Add the generated credentials to your configuration:

**Option A: Using .env file**

```bash
# Add to .env file
storage.s3.access_key_id=your-access-key-id
storage.s3.secret_access_key=your-secret-access-key
storage.use_s3=True
```

**Option B: Using config.yaml**

```yaml
storage:
  use_s3: true
  s3:
    access_key_id: "your-access-key-id"
    secret_access_key: "your-secret-access-key"
    endpoint_url: "http://seaweedfs:8333"
    bucket_name: "gallery"
    region_name: "us-east-1"
    use_ssl: false
```

### 4. Restart Services

Restart your web service to apply the new credentials:

```bash
docker-compose restart web
# Or
make docker-up-vps
```

## Manual Setup (Alternative)

If you prefer to create access keys manually:

### Using curl

```bash
# Create access key for 'admin' identity
curl -X POST "http://localhost:8333/iam/createAccessKey?identity=admin"

# Response will be JSON:
# {
#   "accessKeyId": "your-access-key-id",
#   "secretAccessKey": "your-secret-access-key"
# }
```

### Using Python

```python
import requests

response = requests.post("http://localhost:8333/iam/createAccessKey?identity=admin")
data = response.json()
print(f"Access Key ID: {data['accessKeyId']}")
print(f"Secret Access Key: {data['secretAccessKey']}")
```

## IAM API Endpoints

SeaweedFS IAM API provides several endpoints for managing access keys:

- **Create Access Key**: `POST /iam/createAccessKey?identity=<identity>`
- **List Access Keys**: `GET /iam/listAccessKeys?identity=<identity>`
- **Delete Access Key**: `DELETE /iam/deleteAccessKey?identity=<identity>&accessKeyId=<key-id>`

For more details, see [SeaweedFS IAM API documentation](https://github.com/seaweedfs/seaweedfs/wiki/Amazon-IAM-API).

## Security Considerations

1. **Store Credentials Securely**: Never commit access keys to version control. Use `.env` files (which are in `.gitignore`) or secure secret management.

2. **Network Security**: 
   - SeaweedFS is only accessible within the Docker network (`gallery_network`)
   - For VPS deployment, use WireGuard VPN to secure access
   - Don't expose SeaweedFS ports publicly

3. **Identity Management**: 
   - Use different identities for different applications or environments
   - Rotate access keys periodically
   - Delete unused access keys

4. **Production Setup**:
   - Use strong, randomly generated access keys
   - Consider using environment variables from a secrets manager
   - Enable SSL/TLS if accessing SeaweedFS over untrusted networks

## Troubleshooting

### Error: "Could not connect to SeaweedFS"

- Ensure SeaweedFS container is running: `docker-compose ps`
- Check if the endpoint URL is correct (default: `http://localhost:8333`)
- For Docker network access, use `http://seaweedfs:8333` from within containers

### Error: "HTTP 404 - IAM API not found"

- Ensure you're using SeaweedFS version 3.x or later (IAM is enabled by default)
- Check that the S3 port (8333) is correctly exposed
- Verify the IAM API is enabled (it should be by default)

### Access Keys Not Working

- Verify credentials are correctly set in `.env` or `config.yaml`
- Ensure `storage.use_s3=True` is set
- Check Django logs for authentication errors
- Verify the bucket exists: `curl http://localhost:8333/s3/buckets`

### Creating Bucket

If the bucket doesn't exist, create it:

```bash
# Using curl
curl -X PUT "http://localhost:8333/s3/bucket?name=gallery"

# Or using AWS CLI (if configured)
aws --endpoint-url=http://localhost:8333 s3 mb s3://gallery
```

## Makefile Commands

For convenience, you can use:

```bash
# Create SeaweedFS access keys
make seaweedfs-auth

# Create keys with custom endpoint
make seaweedfs-auth ENDPOINT=http://seaweedfs:8333
```

## References

- [SeaweedFS S3 API Documentation](https://github.com/seaweedfs/seaweedfs/wiki/Amazon-S3-API)
- [SeaweedFS IAM API Documentation](https://github.com/seaweedfs/seaweedfs/wiki/Amazon-IAM-API)
- [Django Storages Documentation](https://django-storages.readthedocs.io/)
