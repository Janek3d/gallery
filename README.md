# SmartGallery

Intelligent Photo Gallery with AI Tagging, built with Django and SeaweedFS.

## Features

- 📷 **Photo Gallery Management**: Organize photos into galleries and albums
- 🤖 **AI-Powered Tagging**: Automatic image tagging using YOLO
- 🔍 **OCR Support**: Extract text from images using PaddleOCR
- 🔐 **Secure File Access**: Signed URLs for media files
- 👥 **Sharing**: Share galleries with other users
- 🏷️ **Tagging System**: User-defined and AI-generated tags
- 🌐 **REST API**: Full REST API using Django REST Framework
- 📦 **SeaweedFS Storage**: Scalable distributed file storage

## Quick Start

See [QUICK_START.md](QUICK_START.md) for detailed setup instructions.

### Basic Setup

1. **Clone and configure:**
   ```bash
   git clone <your-repo>
   cd gallery
   cp .env.example .env
   # Edit .env with your settings
   ```

2. **Install dependencies:**
   ```bash
   make install-dev
   ```

3. **Start services:**
   ```bash
   make docker-up
   ```

4. **Run migrations:**
   ```bash
   make migrate
   ```

5. **Create superuser:**
   ```bash
   make superuser
   ```

## Documentation

- **[QUICK_START.md](QUICK_START.md)** - Quick setup guide
- **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Production deployment guide
- **[docs/SEAWEEDFS_AUTH.md](docs/SEAWEEDFS_AUTH.md)** - SeaweedFS authentication setup
- **[docs/NGINX_SIGNED_URLS.md](docs/NGINX_SIGNED_URLS.md)** - Nginx signed URL configuration
- **[docs/WIREGUARD_SETUP.md](docs/WIREGUARD_SETUP.md)** - WireGuard VPN setup for split deployment
- **[README_TESTING.md](README_TESTING.md)** - Testing guide

## SeaweedFS Authentication

To enable SeaweedFS S3 storage with authentication:

1. **Start SeaweedFS:**
   ```bash
   make docker-up
   ```

2. **Create access keys:**
   ```bash
   make seaweedfs-auth
   ```

3. **Add credentials to `.env`:**
   ```bash
   storage.use_s3=True
   storage.s3.access_key_id=<generated-key>
   storage.s3.secret_access_key=<generated-secret>
   ```

See [docs/SEAWEEDFS_AUTH.md](docs/SEAWEEDFS_AUTH.md) for detailed instructions.

## Development

### Running Tests

```bash
make test              # Run all tests
make test-cov          # Run with coverage
make test-fast         # Run in parallel
```

### Code Quality

```bash
make lint              # Run linters
make format            # Format code
```

### Django Commands

```bash
make runserver         # Start development server
make migrate           # Run migrations
make makemigrations    # Create migrations
make shell             # Django shell
make superuser         # Create superuser
```

## Project Structure

```
gallery/
├── app/               # Django application
│   ├── config/       # Django settings and configuration
│   ├── gallery/      # Gallery app (models, views, serializers)
│   └── tests/        # Test suite
├── docs/             # Documentation
├── scripts/          # Utility scripts
├── nginx/            # Nginx configuration
├── docker-compose.yml        # Local development
├── docker-compose.vps.yml    # VPS deployment
├── docker-compose.gpu.yml    # GPU worker deployment
└── Makefile          # Common commands
```

## License

[Add your license here]
