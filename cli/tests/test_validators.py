"""Tests for cli/validators.py."""

import json
import os
import tempfile

import pytest

from cli.validators import (
    get_map_names,
    load_agents,
    load_npc_registry,
    run_all_validations,
    validate_map_refs,
    validate_no_duplicate_ids,
    validate_no_overlapping_positions,
    validate_soul_files,
    validate_sprite_files,
)


@pytest.fixture
def project_dir():
    """Create a temporary project directory with minimal structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create agents.json
        agents_data = {
            "agents": {
                "list": [
                    {"id": "npc1", "name": "NPC One"},
                    {"id": "npc2", "name": "NPC Two"},
                ]
            }
        }
        with open(os.path.join(tmpdir, "agents.json"), "w") as f:
            json.dump(agents_data, f)

        # Create workspaces with SOUL.md
        for npc_id in ["npc1", "npc2"]:
            ws = os.path.join(tmpdir, "workspaces", npc_id)
            os.makedirs(ws)
            with open(os.path.join(ws, "SOUL.md"), "w") as f:
                f.write(f"# {npc_id}")

        # Create sprite dirs
        for npc_id in ["npc1", "npc2"]:
            os.makedirs(os.path.join(tmpdir, "public", "sprites", "npcs", npc_id))

        # Create maps
        maps_dir = os.path.join(tmpdir, "src", "data", "maps")
        os.makedirs(maps_dir)
        for map_name in ["town", "dungeon"]:
            with open(os.path.join(maps_dir, f"{map_name}.json"), "w") as f:
                json.dump({"width": 10, "height": 10}, f)

        # Create npcRegistry
        os.makedirs(os.path.join(tmpdir, "src", "data"), exist_ok=True)
        with open(os.path.join(tmpdir, "src", "data", "agents.ts"), "w") as f:
            f.write(
                """export const npcRegistry: NPCConfig[] = [
  {
    agentId: 'npc1',
    name: 'NPC One',
    map: 'town',
    tileX: 5,
    tileY: 5,
    facing: 'down',
    portraitUrl: '',
  },
  {
    agentId: 'npc2',
    name: 'NPC Two',
    map: 'dungeon',
    tileX: 10,
    tileY: 8,
    facing: 'left',
    portraitUrl: '',
  },
];
"""
            )

        yield tmpdir


class TestLoadAgents:
    def test_load_nested_format(self, project_dir):
        agents = load_agents(project_dir)
        assert agents is not None
        assert len(agents) == 2
        assert agents[0]["id"] == "npc1"

    def test_load_flat_format(self, project_dir):
        with open(os.path.join(project_dir, "agents.json"), "w") as f:
            json.dump([{"id": "a"}, {"id": "b"}], f)
        agents = load_agents(project_dir)
        assert len(agents) == 2

    def test_missing_file(self, tmp_path):
        assert load_agents(str(tmp_path)) is None


class TestLoadNpcRegistry:
    def test_parse_entries(self, project_dir):
        entries = load_npc_registry(project_dir)
        assert entries is not None
        assert len(entries) == 2
        assert entries[0]["agentId"] == "npc1"
        assert entries[0]["map"] == "town"
        assert entries[0]["tileX"] == 5
        assert entries[1]["agentId"] == "npc2"

    def test_missing_file(self, tmp_path):
        assert load_npc_registry(str(tmp_path)) is None


class TestGetMapNames:
    def test_returns_map_names(self, project_dir):
        names = get_map_names(project_dir)
        assert sorted(names) == ["dungeon", "town"]

    def test_missing_dir(self, tmp_path):
        assert get_map_names(str(tmp_path)) == []


class TestValidateNoDuplicateIds:
    def test_no_duplicates(self):
        assert validate_no_duplicate_ids([{"id": "a"}, {"id": "b"}]) == []

    def test_with_duplicates(self):
        errs = validate_no_duplicate_ids([{"id": "a"}, {"id": "a"}])
        assert len(errs) == 1
        assert "duplicate" in errs[0].lower()


class TestValidateSoulFiles:
    def test_all_present(self, project_dir):
        agents = load_agents(project_dir)
        assert validate_soul_files(agents, project_dir) == []

    def test_missing_soul(self, project_dir):
        os.remove(os.path.join(project_dir, "workspaces", "npc1", "SOUL.md"))
        agents = load_agents(project_dir)
        errs = validate_soul_files(agents, project_dir)
        assert len(errs) == 1
        assert "npc1" in errs[0]


class TestValidateSpriteFiles:
    def test_all_present(self, project_dir):
        agents = load_agents(project_dir)
        assert validate_sprite_files(agents, project_dir) == []

    def test_missing_sprites(self, project_dir):
        import shutil
        shutil.rmtree(
            os.path.join(project_dir, "public", "sprites", "npcs", "npc2")
        )
        agents = load_agents(project_dir)
        errs = validate_sprite_files(agents, project_dir)
        assert len(errs) == 1
        assert "npc2" in errs[0]


class TestValidateMapRefs:
    def test_valid_refs(self):
        entries = [{"agentId": "a", "map": "town"}]
        assert validate_map_refs(entries, ["town", "dungeon"]) == []

    def test_invalid_ref(self):
        entries = [{"agentId": "a", "map": "nonexistent"}]
        errs = validate_map_refs(entries, ["town"])
        assert len(errs) == 1
        assert "nonexistent" in errs[0]


class TestValidateNoOverlappingPositions:
    def test_no_overlap(self):
        entries = [
            {"agentId": "a", "map": "town", "tileX": 1, "tileY": 1},
            {"agentId": "b", "map": "town", "tileX": 2, "tileY": 1},
        ]
        assert validate_no_overlapping_positions(entries) == []

    def test_with_overlap(self):
        entries = [
            {"agentId": "a", "map": "town", "tileX": 1, "tileY": 1},
            {"agentId": "b", "map": "town", "tileX": 1, "tileY": 1},
        ]
        errs = validate_no_overlapping_positions(entries)
        assert len(errs) == 1
        assert "overlaps" in errs[0]

    def test_same_pos_different_maps(self):
        entries = [
            {"agentId": "a", "map": "town", "tileX": 1, "tileY": 1},
            {"agentId": "b", "map": "dungeon", "tileX": 1, "tileY": 1},
        ]
        assert validate_no_overlapping_positions(entries) == []


class TestRunAllValidations:
    def test_all_pass(self, project_dir):
        passes, failures = run_all_validations(project_dir)
        assert len(failures) == 0
        assert len(passes) >= 3

    def test_missing_agents_json(self, tmp_path):
        passes, failures = run_all_validations(str(tmp_path))
        assert len(failures) == 1
        assert "agents.json" in failures[0]
