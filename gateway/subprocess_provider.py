"""SubprocessProvider — routes NPC dialogue to local CLI scripts (Codex inspector/debugger)."""

import asyncio
import os
import re
import shlex
from typing import AsyncGenerator

from gateway.provider import BaseLLMProvider
from gateway.router import AgentRouter

# Lines to strip from codex CLI output (header, metadata, repeated sections)
_SKIP_PATTERNS = re.compile(
    r"^(?:"
    r"OpenAI Codex v[\d.]+"
    r"|Claude Code v[\d.]+"
    r"|[-]{4,}"
    r"|workdir:"
    r"|model:"
    r"|provider:"
    r"|approval:"
    r"|sandbox:"
    r"|reasoning effort:"
    r"|reasoning summaries:"
    r"|session id:"
    r"|tokens used"
    r"|mcp startup:"
    r"|user$"
    r"|codex$"
    r"|assistant$"
    r"|[\d,]+$"
    r"|\[cost\]"
    r"|input tokens:"
    r"|output tokens:"
    r")",
    re.IGNORECASE,
)


class SubprocessProvider(BaseLLMProvider):
    """Spawns a subprocess from the agent's runner config and streams stdout as dialogue."""

    def __init__(self, router: AgentRouter):
        self._router = router

    async def generate_stream(
        self, agent_id: str, messages: list[dict], **kwargs
    ) -> AsyncGenerator[str, None]:
        agent_cfg = self._router.get_agent(agent_id)
        if agent_cfg is None:
            yield f"[error] Unknown agent: {agent_id}"
            return

        runner = agent_cfg.get("runner", {})
        command_template = runner.get("command", "")
        if not command_template:
            yield f"[error] No runner command configured for {agent_id}"
            return

        timeout = runner.get("timeout", 300)

        # Extract the latest user message as the task
        task = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                task = msg.get("content", "")
                break
        if not task:
            yield "[error] No user message found"
            return

        # Expand ~ in command
        command_template = command_template.replace("~", os.path.expanduser("~"))

        # Build the full command with the task as argument
        cmd = f'{command_template} {shlex.quote(task)}'

        # Merge runner env vars
        env = os.environ.copy()
        for k, v in runner.get("env", {}).items():
            if v.startswith("${") and v.endswith("}"):
                env[k] = os.environ.get(v[2:-1], "")
            else:
                env[k] = v

        try:
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env=env,
            )

            # Collect full output, then filter and deduplicate
            raw_output = b""
            try:
                while True:
                    chunk = await asyncio.wait_for(
                        proc.stdout.read(4096), timeout=timeout
                    )
                    if not chunk:
                        break
                    raw_output += chunk
            except asyncio.TimeoutError:
                proc.kill()
                yield "[error] Command timed out"
                return

            await proc.wait()

            # Filter output: strip codex headers, deduplicate repeated response
            text = raw_output.decode("utf-8", errors="replace")
            lines = text.split("\n")

            filtered: list[str] = []
            seen_content: set[str] = set()

            for line in lines:
                stripped = line.strip()
                # Skip empty lines at the start
                if not stripped and not filtered:
                    continue
                # Skip codex metadata lines
                if stripped and _SKIP_PATTERNS.match(stripped):
                    continue
                # Skip the user's own message echoed back
                if stripped == task.strip():
                    continue
                # Deduplicate: skip if we've seen this exact line already
                if stripped and stripped in seen_content:
                    continue
                if stripped:
                    seen_content.add(stripped)
                filtered.append(line)

            # Trim trailing blank lines
            while filtered and not filtered[-1].strip():
                filtered.pop()

            result = "\n".join(filtered).strip()
            if result:
                yield result
            else:
                yield "[No response from agent]"

        except FileNotFoundError:
            yield f"[error] Command not found: {command_template}"
        except Exception as exc:
            yield f"[error] Subprocess failed: {str(exc)[:200]}"
