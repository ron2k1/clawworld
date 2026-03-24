# ClawWorld

A visual frontend for [OpenClaw](https://github.com/ron2k1/openclaw) — a multi-agent orchestration platform. Instead of a terminal or chat UI, ClawWorld renders your agent roster as characters in a tile-based world. Walk up to an agent, talk to it, and it streams responses in real time. Agents consult each other mid-conversation via `ask_agent()` delegation.

## What makes this interesting

- **Spatial agent interface** — agents are placed in a navigable world instead of a list or chat sidebar. You approach the agent you want to talk to.
- **Multi-agent delegation** — a lead agent can consult peer agents inline and synthesize their responses. Delegation is provider-agnostic: the orchestrating agent doesn't need to know whether the target runs on Anthropic, xAI, Ollama, or a subprocess.
- **Per-agent identity isolation** — each agent has a SOUL.md persona and routes to its own LLM provider. No shared context or identity pollution between agents.
- **Hot-swappable roster** — add a new agent by dropping a SOUL.md + config entry. No code changes.
- **Mock mode** — full UI without API keys for development and demos.

## Quick Start

```bash
git clone https://github.com/ron2k1/ClawWorld.git
cd ClawWorld

npm install              # frontend deps
pip install -e .         # gateway + CLI

clawworld dev            # mock mode — no API keys needed
```

Open [http://localhost:5180](http://localhost:5180).

### Live Mode

```bash
export ANTHROPIC_API_KEY=your-key
export XAI_API_KEY=your-key

clawworld serve
```

## Architecture

```
Browser (React + Vite + HTML5 Canvas)
        |
        |  WebSocket JSON-RPC 2.0
        v
Gateway (FastAPI, port 18790)
        |
   AgentRouter ── agents.json + SOUL.md personas
        |
   ┌────┴─────────────────────────┐
   │  Provider routing by model:  │
   │  anthropic/* → LiveProvider  │
   │  xai/*      → LiveProvider  │
   │  ollama/*   → OllamaProvider│
   │  subprocess → SubprocessProv│
   └──────────────────────────────┘
        |
   Multi-agent delegation (ask_agent)
        |
   Agent A ──tool_use──► Gateway ──► Agent B
        ◄──tool_result──         ◄──stream──
```

- **Frontend:** React + Vite + HTML5 Canvas — tile rendering, sprite animation, camera, player movement, mobile touch controls
- **Gateway:** FastAPI WebSocket server — JSON-RPC 2.0 protocol, per-player session persistence, streaming LLM responses, rate limiting, input sanitization
- **Agents:** Declarative config (`agents.json`) + SOUL.md persona files — model-agnostic, provider-agnostic definitions with tool permission controls
- **Delegation:** Agents with `ask_agent` permission can consult other agents mid-conversation. The delegation module routes through the same provider layer, collects the response, and feeds it back as a tool result.

## World

The overworld is a single continuous 100x50 tile map with multiple zones. Interior locations are separate maps accessed via door transitions. The player sprite was generated using ComfyUI inpainting.

## Agent Roles

| Role | Description | Model |
|------|-------------|-------|
| Personal Assistant | Lead agent with delegation access | xai/grok-3 |
| Senior Analyst | Data and strategy analysis | anthropic/claude-sonnet-4-6 |
| The Coder | Programming and debugging | anthropic/claude-opus-4-6 |
| The Elder | Knowledge base and context | anthropic/claude-opus-4-6 |
| Trader | Economics and negotiation | anthropic/claude-haiku-4-5 |
| Blacksmith | Research and web scraping | ollama/qwen3:4b |
| Planner | Task planning and coordination | ollama/qwen3:4b |
| Innkeeper | Local context and rumors | ollama/qwen3:4b |
| Code Inspector | Automated code review | subprocess (Codex) |
| Code Debugger | Automated debugging | subprocess (Codex) |

## Development

```bash
npm run dev              # frontend dev server (hot reload)
npm run test             # frontend tests
pytest gateway/tests/    # gateway tests (89 tests)
clawworld validate       # check project structure
npm run build            # production build
```

## Contributing

1. Fork and create a feature branch
2. Run `clawworld validate` to check structure
3. Run tests: `npm run test` and `pytest gateway/tests/`
4. Open a PR against `master`

## License

MIT (code). Art assets have separate licenses — see `assets/ATTRIBUTION.md`.
