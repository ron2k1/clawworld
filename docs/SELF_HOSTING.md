# Self-Hosting ClawWorld

## Requirements

- **Node.js** 18+ (for the frontend build)
- **Python** 3.10+ (for the gateway server)
- **API keys** for at least one LLM provider (Anthropic or xAI)

## Setup

### 1. Clone and Install

```bash
git clone https://github.com/your-org/clawworld.git
cd clawworld

# Frontend
npm install

# Gateway
pip install -e .
```

### 2. Configure API Keys

Create a `.env` file in the project root (see `.env.example`):

```env
CLAWWORLD_MODE=live
ANTHROPIC_API_KEY=sk-ant-...
XAI_API_KEY=xai-...
```

- `ANTHROPIC_API_KEY` is required for NPCs using Anthropic models (analyst, coder, lorekeeper, trader)
- `XAI_API_KEY` is required for Personal Assistant (uses Grok)
- You only need keys for the providers your NPCs use

### 3. Build the Frontend

```bash
npm run build
```

This produces a static site in `dist/`.

### 4. Start the Gateway

```bash
python -m gateway.server
```

The gateway runs on port 18789 by default.

### 5. Serve the Frontend

Use any static file server to serve `dist/`. The frontend connects to the gateway via WebSocket.

**With Vite preview:**
```bash
npm run preview
```

**With the CLI:**
```bash
clawworld serve
```

## Production Deployment

### Option A: Single Server

Run both the gateway and a static file server on the same machine:

```bash
# Terminal 1: Gateway
CLAWWORLD_MODE=live python -m gateway.server

# Terminal 2: Frontend
npx serve dist -l 5180
```

### Option B: Separate Services

1. Deploy `dist/` to any static hosting (Vercel, Netlify, S3 + CloudFront)
2. Deploy the gateway as a Python service (Railway, Fly.io, a VPS)
3. Update the WebSocket URL in the frontend to point to your gateway

### Reverse Proxy (nginx)

```nginx
server {
    listen 80;
    server_name clawworld.example.com;

    location / {
        root /var/www/clawworld/dist;
        try_files $uri $uri/ /index.html;
    }

    location /gateway-ws {
        proxy_pass http://127.0.0.1:18789;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `CLAWWORLD_MODE` | No | `mock` (default) or `live` |
| `ANTHROPIC_API_KEY` | For live mode | Anthropic API key |
| `XAI_API_KEY` | For Personal Assistant NPC | xAI API key |
| `GATEWAY_PORT` | No | Gateway port (default: 18789) |

## Troubleshooting

- **WebSocket connection fails:** Ensure the gateway is running and the proxy is configured for WebSocket upgrade
- **NPC responses are empty:** Check that API keys are set and valid
- **Mock mode works but live doesn't:** Verify `CLAWWORLD_MODE=live` is set for the gateway process
