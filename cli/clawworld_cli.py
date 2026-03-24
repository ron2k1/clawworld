"""ClawWorld project scaffolding CLI."""

import json
import os
import re
import subprocess
import sys

import click
from jinja2 import Environment, FileSystemLoader

from cli.validators import run_all_validations

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))


@click.group()
def cli():
    """ClawWorld project scaffolding CLI."""
    pass


@cli.command()
def init():
    """Scaffold the ClawWorld project directory structure."""
    directories = [
        "src/engine",
        "src/gateway",
        "src/ui",
        "src/data/maps",
        "src/data/community",
        "src/store",
        "public/tilesets",
        "public/sprites/npcs/community",
        "public/sprites/portraits",
        "public/audio",
        "workspaces/assistant",
        "workspaces/analyst",
        "workspaces/coder",
        "workspaces/lorekeeper",
        "workspaces/trader",
        "workspaces/townsfolk",
        "maps",
        "assets",
        "docs",
        "gateway",
        "gateway/mock_responses",
        "gateway/tests",
        "cli",
        "cli/templates",
    ]

    workspace_ids = ["assistant", "analyst", "coder", "lorekeeper", "trader", "townsfolk"]

    # Create directories
    for d in directories:
        os.makedirs(d, exist_ok=True)
        click.echo(f"created {d}/")

    # Create empty SOUL.md in each workspace
    for agent_id in workspace_ids:
        soul_path = os.path.join("workspaces", agent_id, "SOUL.md")
        if not os.path.exists(soul_path):
            open(soul_path, "a").close()
            click.echo(f"created {soul_path}")

    # Create agents.json if it doesn't exist
    agents_file = "agents.json"
    if not os.path.exists(agents_file):
        with open(agents_file, "w") as f:
            json.dump({"agents": {"list": []}}, f, indent=2)
        click.echo(f"created {agents_file}")

    # Create src/data/agents.ts if it doesn't exist
    agents_ts = os.path.join("src", "data", "agents.ts")
    if not os.path.exists(agents_ts):
        with open(agents_ts, "w") as f:
            f.write(
                """export type NPCConfig = {
  agentId: string;
  name: string;
  map: string;
  tileX: number;
  tileY: number;
  facing: 'up' | 'down' | 'left' | 'right';
  portraitUrl: string;
};

export const npcRegistry: NPCConfig[] = [];
"""
            )
        click.echo(f"created {agents_ts}")

    # Create src/main.tsx
    main_tsx = "src/main.tsx"
    if not os.path.exists(main_tsx):
        with open(main_tsx, "w") as f:
            f.write(
                """import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
"""
            )
        click.echo(f"created {main_tsx}")

    # Create src/App.tsx
    app_tsx = "src/App.tsx"
    if not os.path.exists(app_tsx):
        with open(app_tsx, "w") as f:
            f.write(
                """export default function App() {
  return (
    <div>
      <h1>ClawWorld</h1>
    </div>
  );
}
"""
            )
        click.echo(f"created {app_tsx}")

    # Create .env.example
    env_example = ".env.example"
    if not os.path.exists(env_example):
        with open(env_example, "w") as f:
            f.write("CLAWWORLD_MODE=mock\nANTHROPIC_API_KEY=\nXAI_API_KEY=\n")
        click.echo(f"created {env_example}")

    click.echo("\nProject scaffolded successfully!")


def _load_agents_json(agents_file="agents.json"):
    """Load and return the full agents.json data structure."""
    if not os.path.exists(agents_file):
        return {"agents": {"list": []}}
    with open(agents_file) as f:
        data = json.load(f)
    # Normalize to nested format
    if isinstance(data, list):
        return {"agents": {"list": data}}
    if isinstance(data, dict) and "agents" in data:
        return data
    return {"agents": {"list": []}}


def _save_agents_json(data, agents_file="agents.json"):
    """Save agents.json data structure."""
    with open(agents_file, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


@cli.command("add-npc")
@click.option("--id", "agent_id", required=True, help="Unique agent ID")
@click.option("--name", required=True, help="Display name")
@click.option("--map", "map_name", required=True, help="Map the NPC belongs to")
@click.option("--tile-x", type=int, required=True, help="X tile position")
@click.option("--tile-y", type=int, required=True, help="Y tile position")
@click.option(
    "--facing", default="down", help="Direction NPC faces (default: down)"
)
@click.option(
    "--model", default="anthropic/claude-haiku-4-5-20251001", help="LLM model"
)
def add_npc(agent_id, name, map_name, tile_x, tile_y, facing, model):
    """Add a new NPC: create SOUL.md, register in agents.json and npcRegistry."""
    # Check for duplicate ID
    data = _load_agents_json()
    existing_ids = [a["id"] for a in data["agents"]["list"]]
    if agent_id in existing_ids:
        click.echo(f"Error: agent '{agent_id}' already exists in agents.json")
        raise SystemExit(1)

    # 1. Create workspace directory and SOUL.md
    workspace_dir = os.path.join("workspaces", agent_id)
    os.makedirs(workspace_dir, exist_ok=True)

    soul_template = jinja_env.get_template("soul_md.j2")
    soul_content = soul_template.render(name=name, location=map_name)
    soul_path = os.path.join(workspace_dir, "SOUL.md")
    with open(soul_path, "w") as f:
        f.write(soul_content)
    click.echo(f"created {soul_path}")

    # 2. Create sprite directory placeholder
    sprite_dir = os.path.join("public", "sprites", "npcs", agent_id)
    os.makedirs(sprite_dir, exist_ok=True)
    click.echo(f"created {sprite_dir}/")

    # 3. Add to agents.json
    data["agents"]["list"].append(
        {
            "id": agent_id,
            "name": name,
            "workspace": f"workspaces/{agent_id}",
            "model": {"primary": model},
            "tools": {"deny": ["exec", "write", "browser", "canvas"]},
        }
    )
    _save_agents_json(data)
    click.echo(f"added {agent_id} to agents.json")

    # 4. Add to npcRegistry in src/data/agents.ts
    agents_ts = os.path.join("src", "data", "agents.ts")
    if os.path.exists(agents_ts):
        with open(agents_ts) as f:
            content = f.read()

        # Build the new entry
        new_entry = (
            f"  {{\n"
            f"    agentId: '{agent_id}',\n"
            f"    name: '{name}',\n"
            f"    map: '{map_name}',\n"
            f"    tileX: {tile_x},\n"
            f"    tileY: {tile_y},\n"
            f"    facing: '{facing}',\n"
            f"    portraitUrl: '',\n"
            f"  }},\n"
        )

        # Insert before the closing ];  (handles both empty [] and populated arrays)
        if "npcRegistry: NPCConfig[] = [];" in content:
            content = content.replace(
                "npcRegistry: NPCConfig[] = [];",
                "npcRegistry: NPCConfig[] = [\n" + new_entry + "];",
            )
        else:
            content = re.sub(
                r"(\n\];)",
                f"\n{new_entry}" + r"\1",
                content,
            )
        with open(agents_ts, "w") as f:
            f.write(content)
        click.echo(f"added {agent_id} to npcRegistry in {agents_ts}")

    click.echo(f"\nNPC '{name}' ({agent_id}) added successfully!")


@cli.command("add-map")
@click.option("--name", required=True, help="Map name (slug, e.g. 'my-dungeon')")
@click.option("--width", type=int, required=True, help="Map width in tiles")
@click.option("--height", type=int, required=True, help="Map height in tiles")
@click.option(
    "--type",
    "map_type",
    type=click.Choice(["outdoor", "indoor"]),
    default="outdoor",
    help="Map type (default: outdoor)",
)
def add_map(name, width, height, map_type):
    """Add a new Tiled-compatible map JSON."""
    map_dir = os.path.join("src", "data", "maps")
    os.makedirs(map_dir, exist_ok=True)

    map_path = os.path.join(map_dir, f"{name}.json")
    if os.path.exists(map_path):
        click.echo(f"Error: map '{name}' already exists at {map_path}")
        raise SystemExit(1)

    map_template = jinja_env.get_template("map_json.j2")
    map_content = map_template.render(
        name=name, width=width, height=height, type=map_type
    )
    with open(map_path, "w") as f:
        f.write(map_content)
    click.echo(f"created {map_path}")
    click.echo(f"\nMap '{name}' ({width}x{height}, {map_type}) added successfully!")


@cli.command()
def validate():
    """Validate project: sprites, SOUL.md, map refs, duplicate IDs, overlapping positions."""
    passes, failures = run_all_validations(".")

    for msg in passes:
        click.echo(f"PASS: {msg}")
    for msg in failures:
        click.echo(f"FAIL: {msg}")

    click.echo(f"\n{len(passes)} passed, {len(failures)} failed")
    if failures:
        raise SystemExit(1)


def _run_parallel(gateway_env, frontend_cmd):
    """Run gateway and frontend as parallel subprocesses."""
    gateway_proc = subprocess.Popen(
        [sys.executable, "-m", "gateway.server"],
        env={**os.environ, **gateway_env},
    )
    click.echo(f"gateway PID: {gateway_proc.pid}")

    frontend_proc = subprocess.Popen(frontend_cmd, shell=True)
    click.echo(f"frontend PID: {frontend_proc.pid}")

    try:
        gateway_proc.wait()
        frontend_proc.wait()
    except KeyboardInterrupt:
        click.echo("\nShutting down...")
        gateway_proc.terminate()
        frontend_proc.terminate()
        gateway_proc.wait()
        frontend_proc.wait()


@cli.command()
def dev():
    """Start gateway (mock mode) + vite dev server."""
    _run_parallel(
        gateway_env={"CLAWWORLD_MODE": "mock"},
        frontend_cmd="npm run dev",
    )


@cli.command()
def serve():
    """Start gateway (live mode) + vite preview server."""
    _run_parallel(
        gateway_env={"CLAWWORLD_MODE": "live"},
        frontend_cmd="npm run preview",
    )


def main():
    """Entry point for pyproject.toml console_scripts."""
    cli()


if __name__ == "__main__":
    main()
