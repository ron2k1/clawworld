"""Validation functions for ClawWorld CLI."""

import json
import os
from typing import Any


def load_agents(project_root: str = ".") -> list[dict[str, Any]] | None:
    """Load agents list from agents.json, supporting both flat and nested formats."""
    agents_file = os.path.join(project_root, "agents.json")
    if not os.path.exists(agents_file):
        return None
    with open(agents_file) as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "agents" in data:
        return data["agents"].get("list", [])
    return []


def load_npc_registry(project_root: str = ".") -> list[dict[str, Any]] | None:
    """Parse npcRegistry entries from src/data/agents.ts."""
    agents_ts = os.path.join(project_root, "src", "data", "agents.ts")
    if not os.path.exists(agents_ts):
        return None
    with open(agents_ts) as f:
        content = f.read()
    # Simple extraction: find objects in the npcRegistry array
    import re
    entries = []
    for match in re.finditer(
        r"\{\s*agentId:\s*['\"](\w+)['\"].*?map:\s*['\"]([^'\"]+)['\"].*?"
        r"tileX:\s*(\d+).*?tileY:\s*(\d+)",
        content,
        re.DOTALL,
    ):
        entries.append({
            "agentId": match.group(1),
            "map": match.group(2),
            "tileX": int(match.group(3)),
            "tileY": int(match.group(4)),
        })
    return entries


def get_map_names(project_root: str = ".") -> list[str]:
    """Return list of available map names from public/data/maps/ and src/data/maps/."""
    names: set[str] = set()
    for subdir in ["public/data/maps", "src/data/maps"]:
        maps_dir = os.path.join(project_root, subdir)
        if os.path.isdir(maps_dir):
            for f in os.listdir(maps_dir):
                if f.endswith(".json"):
                    names.add(os.path.splitext(f)[0])
    return list(names)


def validate_no_duplicate_ids(agents: list[dict]) -> list[str]:
    """Check for duplicate agent IDs. Returns list of error messages."""
    ids = [a["id"] for a in agents]
    duplicates = [aid for aid in set(ids) if ids.count(aid) > 1]
    if duplicates:
        return [f"duplicate agent IDs: {', '.join(sorted(duplicates))}"]
    return []


def validate_soul_files(agents: list[dict], project_root: str = ".") -> list[str]:
    """Check every agent has a SOUL.md file. Returns list of error messages."""
    errors = []
    for agent in agents:
        agent_id = agent["id"]
        soul_path = os.path.join(project_root, "workspaces", agent_id, "SOUL.md")
        if not os.path.exists(soul_path):
            errors.append(f"{agent_id} missing SOUL.md at {soul_path}")
    return errors


def validate_sprite_files(agents: list[dict], project_root: str = ".") -> list[str]:
    """Check every agent has a sprite directory. Returns list of error messages."""
    errors = []
    for agent in agents:
        agent_id = agent["id"]
        sprite_dir = os.path.join(
            project_root, "public", "sprites", "npcs", agent_id
        )
        if not os.path.isdir(sprite_dir):
            errors.append(f"{agent_id} missing sprite directory at {sprite_dir}")
    return errors


def validate_map_refs(
    npc_entries: list[dict], available_maps: list[str]
) -> list[str]:
    """Check every NPC map reference points to a valid map. Returns errors."""
    errors = []
    for entry in npc_entries:
        if entry["map"] not in available_maps:
            errors.append(
                f"{entry['agentId']} references unknown map '{entry['map']}'"
            )
    return errors


def validate_no_overlapping_positions(npc_entries: list[dict]) -> list[str]:
    """Check no two NPCs occupy the same tile on the same map. Returns errors."""
    seen: dict[tuple[str, int, int], str] = {}
    errors = []
    for entry in npc_entries:
        key = (entry["map"], entry["tileX"], entry["tileY"])
        if key in seen:
            errors.append(
                f"{entry['agentId']} overlaps with {seen[key]} "
                f"at ({entry['tileX']}, {entry['tileY']}) on map '{entry['map']}'"
            )
        else:
            seen[key] = entry["agentId"]
    return errors


def run_all_validations(project_root: str = ".") -> tuple[list[str], list[str]]:
    """Run all validations. Returns (passes, failures)."""
    passes = []
    failures = []

    # Load agents
    agents = load_agents(project_root)
    if agents is None:
        return passes, ["agents.json not found"]

    # Duplicate IDs
    errs = validate_no_duplicate_ids(agents)
    if errs:
        failures.extend(errs)
    else:
        passes.append("no duplicate agent IDs")

    # SOUL.md files
    errs = validate_soul_files(agents, project_root)
    if errs:
        failures.extend(errs)
    else:
        passes.append("all agents have SOUL.md")

    # Sprite directories
    errs = validate_sprite_files(agents, project_root)
    if errs:
        failures.extend(errs)
    else:
        passes.append("all agents have sprite directories")

    # NPC registry checks
    npc_entries = load_npc_registry(project_root)
    available_maps = get_map_names(project_root)

    if npc_entries is not None:
        # Map refs
        errs = validate_map_refs(npc_entries, available_maps)
        if errs:
            failures.extend(errs)
        else:
            passes.append("all NPC map references are valid")

        # Overlapping positions
        errs = validate_no_overlapping_positions(npc_entries)
        if errs:
            failures.extend(errs)
        else:
            passes.append("no overlapping NPC positions")

    return passes, failures
