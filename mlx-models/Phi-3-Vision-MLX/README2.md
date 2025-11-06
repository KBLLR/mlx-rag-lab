# Phi-3-Vision-MLX API Documentation

conda activate image_organizer
console: phi3v = phi_3_vision_mlx.phi_3_vision_mlx:chat_ui

## Table of Contents
1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Security Features](#security-features)
4. [API Key Management](#api-key-management)
5. [API Endpoints](#api-endpoints)
6. [Rate Limiting](#rate-limiting)
7. [Error Handling](#error-handling)
8. [Examples](#examples)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

## Introduction
Phi-3-Vision-MLX is a secure API server implementation for running the Phi-3 Vision model on Apple Silicon. It provides text generation capabilities with robust security features and API key management.

### Features
- Secure HTTPS endpoints
- API key authentication
- Rate limiting
- Request validation
- Comprehensive logging
- Error handling
- Content length limits

## Installation

### Prerequisites
- Python 3.12.3 or higher
- MLX framework
- OpenSSL (for SSL/TLS certificates)

### Setup
1. Clone the repository:
```bash
git clone https://github.com/YourRepo/Phi-3-Vision-MLX.git
cd Phi-3-Vision-MLX
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Generate SSL certificates (automatic on first run or manual):
```bash
openssl req -x509 -newkey rsa:4096 -nodes \
    -out server.crt -keyout server.key \
    -days 365 -subj '/CN=localhost'
```

4. Start the server:
```bash
python secure_server.py
```

## Security Features

### SSL/TLS Encryption
All communications are encrypted using SSL/TLS. The server can be configured to use custom certificates for production environments.

### API Key Authentication
All requests must include a valid API key in the `X-API-Key` header.

### Request Validation
- Maximum content length: 1MB
- Input sanitization
- Rate limiting per API key

## API Key Management

### Managing API Keys
Use the `api_key_manager.py` utility to manage API keys:

1. Create a new key:
```bash
python api_key_manager.py create --name "MyApp" --rate-limit 100
```

2. List all keys:
```bash
python api_key_manager.py list
```

3. Update rate limit:
```bash
python api_key_manager.py update --key YOUR_API_KEY --rate-limit 200
```

4. Delete a key:
```bash
python api_key_manager.py delete --key YOUR_API_KEY
```

## API Endpoints

### POST /v1/completions
Generate text completions based on input prompts.

#### Request Headers
- `Content-Type: application/json`
- `X-API-Key: YOUR_API_KEY`

#### Request Body
```json
{
    "prompt": "string or array of strings",
    "max_tokens": integer (default: 512, max: 1024)
}
```

#### Response Format
```json
{
    "model": "phi-3-vision",
    "responses": ["generated text"],
    "timestamp": "ISO timestamp"
}
```

## Rate Limiting
- Default: 100 requests per minute per API key
- Configurable per API key
- 429 error response when exceeded

## Error Handling

### HTTP Status Codes
- 200: Successful request
- 400: Invalid request
- 401: Missing API key
- 403: Invalid API key
- 413: Request too large
- 429: Rate limit exceeded
- 500: Server error

### Error Response Format
```json
{
    "error": {
        "code": "status_code",
        "message": "error description"
    }
}
```

## Examples

### Single Prompt Request
```bash
curl -X POST https://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -k \
  -d '{
    "prompt": "Hello, world!",
    "max_tokens": 50
  }'
```

### Multiple Prompts Request
```bash
curl -X POST https://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -k \
  -d '{
    "prompt": [
      "Hello, world!",
      "Guten tag!"
    ],
    "max_tokens": 50
  }'
```

## Best Practices

### Security
1. Always use HTTPS in production
2. Rotate API keys periodically
3. Set appropriate rate limits
4. Monitor API usage
5. Keep certificates up to date

### Performance
1. Batch requests when possible
2. Monitor response times
3. Set appropriate max_tokens
4. Handle errors gracefully
5. Implement client-side caching

## Troubleshooting

### Common Issues

1. SSL Certificate Errors
```bash
# Generate new certificates
openssl req -x509 -newkey rsa:4096 -nodes \
    -out server.crt -keyout server.key \
    -days 365 -subj '/CN=localhost'
```

2. Rate Limit Exceeded
- Check current rate limit: `python api_key_manager.py list`
- Update if needed: `python api_key_manager.py update --key YOUR_KEY --rate-limit NEW_LIMIT`

3. Server Logs
- Check `server.log` for detailed error information
- Increase log level for debugging

### Support
For additional support:
- Open an issue on GitHub
- Check the example implementations
- Review the security documentation

## License
This project is licensed under the MIT License - see the LICENSE file for details.
