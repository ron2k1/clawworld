# Adding an NPC to ClawWorld

## Prerequisites

- ClawWorld project cloned and running (`clawworld dev`)
- A text editor and basic familiarity with JSON

## Step 1: Define the Agent

Add an entry to `agents.json` in the project root:

```json
{
  "id": "scholar",
  "name": "The Scholar",
  "model": "anthropic/claude-sonnet-4-6",
  "workspace": "workspaces/scholar",
  "tools": []
}
```

**Fields:**
- `id` — unique identifier (lowercase, no spaces)
- `name` — display name shown in the dialogue box
- `model` — LLM model in `provider/model` format
- `workspace` — directory for this agent's persona and data
- `tools` — optional array of tool names the agent can use

## Step 2: Create the SOUL.md Persona

Create `workspaces/scholar/SOUL.md`:

```markdown
# The Scholar

You are a wise scholar who lives in the library of Lore Village.
You speak in a formal, measured tone and love sharing knowledge
about the history of ClawWorld.

## Personality
- Patient and thoughtful
- Loves answering questions about lore
- Occasionally quotes ancient texts

## Knowledge
- Expert on ClawWorld history and geography
- Knows all the NPCs and their backstories
```

The SOUL.md is sent as the system prompt to the LLM.

## Step 3: Register in the NPC Registry

Add your NPC to `src/data/agents.ts`:

```typescript
{
  agentId: 'scholar',
  name: 'The Scholar',
  map: 'lore-village',
  tileX: 15,
  tileY: 12,
  facing: 'down',
  portraitUrl: '',
}
```

**Fields:**
- `map` — which map the NPC appears on (must match a map JSON filename)
- `tileX`, `tileY` — tile coordinates for NPC placement
- `facing` — initial facing direction (`up`, `down`, `left`, `right`)
- `portraitUrl` — path to a portrait image (optional, leave empty for default)

## Step 4: Add a Sprite (Optional)

Place a spritesheet at `public/sprites/scholar.png`. The spritesheet should be:
- 64x128 pixels (2 frames wide x 4 directions tall)
- Each frame is 32x32 pixels
- Row order: down, left, right, up

If you skip this step, a colored placeholder rectangle will be used.

## Step 5: Add to Map Objects (Optional)

You can also define NPC spawn points directly in the Tiled map JSON. Add an object to the `objects` layer:

```json
{
  "name": "scholar",
  "type": "npc",
  "x": 480,
  "y": 384,
  "width": 32,
  "height": 32,
  "properties": [
    { "name": "agentId", "value": "scholar" },
    { "name": "facing", "value": "down" }
  ]
}
```

NPCs defined in both the map and the registry will not be duplicated.

## Step 6: Validate

Run `clawworld validate` to check that your NPC has:
- An entry in `agents.json`
- A SOUL.md file in the workspace directory
- A matching entry in the NPC registry or map objects

## Using the CLI

You can also use the CLI to scaffold an NPC:

```bash
clawworld add npc --id scholar --name "The Scholar" --map lore-village --x 15 --y 12
```

This creates the `agents.json` entry, workspace directory, and a template SOUL.md.
