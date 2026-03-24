"""Tests for CLI commands using Click's CliRunner."""

import json
import os
import tempfile

import pytest
from click.testing import CliRunner

from cli.clawworld_cli import cli


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def project_dir():
    """Create a temporary project directory and chdir into it."""
    with tempfile.TemporaryDirectory() as tmpdir:
        old_cwd = os.getcwd()
        os.chdir(tmpdir)
        yield tmpdir
        os.chdir(old_cwd)


class TestInit:
    def test_creates_directories(self, runner, project_dir):
        result = runner.invoke(cli, ["init"])
        assert result.exit_code == 0
        assert os.path.isdir("src/engine")
        assert os.path.isdir("src/data/maps")
        assert os.path.isdir("public/sprites/npcs/community")
        assert os.path.isdir("gateway/mock_responses")
        assert os.path.isdir("cli/templates")

    def test_creates_soul_files(self, runner, project_dir):
        result = runner.invoke(cli, ["init"])
        assert result.exit_code == 0
        for agent_id in ["assistant", "analyst", "coder", "lorekeeper", "trader", "townsfolk"]:
            assert os.path.exists(f"workspaces/{agent_id}/SOUL.md")

    def test_creates_agents_json(self, runner, project_dir):
        result = runner.invoke(cli, ["init"])
        assert result.exit_code == 0
        assert os.path.exists("agents.json")
        with open("agents.json") as f:
            data = json.load(f)
        assert "agents" in data
        assert "list" in data["agents"]

    def test_creates_agents_ts(self, runner, project_dir):
        result = runner.invoke(cli, ["init"])
        assert result.exit_code == 0
        agents_ts = os.path.join("src", "data", "agents.ts")
        assert os.path.exists(agents_ts)
        with open(agents_ts) as f:
            content = f.read()
        assert "npcRegistry" in content

    def test_creates_source_files(self, runner, project_dir):
        result = runner.invoke(cli, ["init"])
        assert result.exit_code == 0
        assert os.path.exists("src/main.tsx")
        assert os.path.exists("src/App.tsx")

    def test_creates_env_example(self, runner, project_dir):
        result = runner.invoke(cli, ["init"])
        assert result.exit_code == 0
        assert os.path.exists(".env.example")

    def test_idempotent(self, runner, project_dir):
        """Running init twice should not fail or overwrite files."""
        runner.invoke(cli, ["init"])
        # Write something to App.tsx
        with open("src/App.tsx", "w") as f:
            f.write("custom content")
        result = runner.invoke(cli, ["init"])
        assert result.exit_code == 0
        # Should not have overwritten
        with open("src/App.tsx") as f:
            assert f.read() == "custom content"


class TestAddNpc:
    def _setup_project(self, runner):
        """Run init and set up templates."""
        runner.invoke(cli, ["init"])
        # Copy templates to local cli/templates (init creates the dir)
        import shutil
        src_templates = os.path.join(os.path.dirname(__file__), "..", "templates")
        src_templates = os.path.abspath(src_templates)
        if os.path.isdir(src_templates):
            dest = os.path.join("cli", "templates")
            os.makedirs(dest, exist_ok=True)
            for f in os.listdir(src_templates):
                shutil.copy2(os.path.join(src_templates, f), dest)

    def test_adds_npc(self, runner, project_dir):
        self._setup_project(runner)
        result = runner.invoke(
            cli,
            [
                "add-npc",
                "--id", "guard",
                "--name", "Town Guard",
                "--map", "world",
                "--tile-x", "10",
                "--tile-y", "20",
            ],
        )
        assert result.exit_code == 0

        # Check SOUL.md created
        assert os.path.exists("workspaces/guard/SOUL.md")

        # Check sprite dir created
        assert os.path.isdir("public/sprites/npcs/guard")

        # Check agents.json updated
        with open("agents.json") as f:
            data = json.load(f)
        ids = [a["id"] for a in data["agents"]["list"]]
        assert "guard" in ids

        # Check npcRegistry updated
        with open(os.path.join("src", "data", "agents.ts")) as f:
            content = f.read()
        assert "'guard'" in content
        assert "'Town Guard'" in content

    def test_duplicate_id_rejected(self, runner, project_dir):
        self._setup_project(runner)
        runner.invoke(
            cli,
            [
                "add-npc",
                "--id", "guard",
                "--name", "Guard",
                "--map", "town",
                "--tile-x", "1",
                "--tile-y", "1",
            ],
        )
        result = runner.invoke(
            cli,
            [
                "add-npc",
                "--id", "guard",
                "--name", "Guard 2",
                "--map", "town",
                "--tile-x", "2",
                "--tile-y", "2",
            ],
        )
        assert result.exit_code != 0
        assert "already exists" in result.output


class TestAddMap:
    def test_creates_map(self, runner, project_dir):
        result = runner.invoke(
            cli,
            ["add-map", "--name", "test-cave", "--width", "20", "--height", "15", "--type", "indoor"],
        )
        assert result.exit_code == 0
        map_path = os.path.join("src", "data", "maps", "test-cave.json")
        assert os.path.exists(map_path)
        with open(map_path) as f:
            data = json.load(f)
        assert data["width"] == 20
        assert data["height"] == 15

    def test_duplicate_map_rejected(self, runner, project_dir):
        runner.invoke(
            cli,
            ["add-map", "--name", "cave", "--width", "10", "--height", "10"],
        )
        result = runner.invoke(
            cli,
            ["add-map", "--name", "cave", "--width", "10", "--height", "10"],
        )
        assert result.exit_code != 0
        assert "already exists" in result.output


class TestValidate:
    def test_passes_on_valid_project(self, runner, project_dir):
        """Set up a valid mini-project and validate it."""
        # Create agents.json
        agents_data = {
            "agents": {
                "list": [{"id": "npc1", "name": "NPC"}]
            }
        }
        with open("agents.json", "w") as f:
            json.dump(agents_data, f)

        # Create workspace
        os.makedirs("workspaces/npc1")
        with open("workspaces/npc1/SOUL.md", "w") as f:
            f.write("# NPC")

        # Create sprite dir
        os.makedirs("public/sprites/npcs/npc1")

        # Create map
        os.makedirs("src/data/maps")
        with open("src/data/maps/town.json", "w") as f:
            json.dump({"width": 10}, f)

        # Create npcRegistry
        os.makedirs("src/data", exist_ok=True)
        with open("src/data/agents.ts", "w") as f:
            f.write(
                """export const npcRegistry: NPCConfig[] = [
  {
    agentId: 'npc1',
    name: 'NPC',
    map: 'town',
    tileX: 5,
    tileY: 5,
    facing: 'down',
    portraitUrl: '',
  },
];
"""
            )

        result = runner.invoke(cli, ["validate"])
        assert result.exit_code == 0
        assert "FAIL" not in result.output

    def test_fails_on_missing_soul(self, runner, project_dir):
        agents_data = {
            "agents": {"list": [{"id": "ghost", "name": "Ghost"}]}
        }
        with open("agents.json", "w") as f:
            json.dump(agents_data, f)

        result = runner.invoke(cli, ["validate"])
        assert result.exit_code != 0
        assert "FAIL" in result.output

    def test_fails_on_missing_agents_json(self, runner, project_dir):
        result = runner.invoke(cli, ["validate"])
        assert result.exit_code != 0
