"""Ollama provider — streams responses from local Ollama models."""

import json
import re
from typing import AsyncGenerator

import httpx

from gateway.provider import BaseLLMProvider
from gateway.router import AgentRouter

OLLAMA_BASE_URL = "http://localhost:11434"

# Match <think>...</think> blocks (may span multiple lines)
_THINK_BLOCK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
# Match unclosed <think> blocks (thinking continues to end of text)
_THINK_UNCLOSED_RE = re.compile(r"<think>.*", re.DOTALL | re.IGNORECASE)
# Match everything before a stray </think> (model leaked close tag without open)
_THINK_CLOSE_ONLY_RE = re.compile(r"^.*?</think>\s*", re.DOTALL | re.IGNORECASE)

# Meta-reasoning indicators — if a paragraph contains ANY of these, it's thinking
_META_PHRASES = [
    r"the user",
    r"they('ve| have| are| said| want| asked| just| seem| were| need)",
    r"(my|the) (role|character|persona|task|response|job) is",
    r"I (need to|should|must|will|'ll) \w+",  # any "I need to <verb>" is meta-reasoning
    r"I can add",
    r"in.character",
    r"stay(ing)? in character",
    r"(avoid|no) (inner |any )?(monologue|reasoning|narrat|explain|thinking)",
    r"(sound|respond|act) like",
    r"per my (style|instructions|persona)",
    r"keep it (to )?\d+",
    r"\d+(-| )\d+ sentences",
    r"looking at (the |this )?(context|conversation|question|message)",
    r"(clearly|probably|seems|apparently) (trying|testing|asking|want)",
    r"(important|critical|must|need) to (avoid|remember|keep|stay|not)",
    r"let me (think|consider|respond|formulate|count|write|rephrase|try)",
    r"let's (unpack|think|break|consider|analyze)",
    r"encourage (collaborat|engag|interact)",
    r"open.ended question",
    r"end with (a|an) (question|open)",
    r"for example,? \"",  # meta example of what to say
    r"crafting (a |my |the )?response",
    r"(show|add|mention|include).*(credib|detail|example|context)",
    r"(concrete|specific) example",
    r"(start|begin|open) with",
    r"(my|a) (greeting|intro|response|answer|opening)",
    r"^so I need to",
    r"^(now|okay|alright|right),? (I |let)",
    r"^perfect\.?\s*$",
    # Self-referential meta-reasoning about format/length/rules
    r"wait,? that'?s (a bit|too) (long|short|much|many)",
    r"(let me|I('ll| will)) (count|rewrite|redo|rephrase|shorten|reformat)",
    r"\d+ (sentence|word|line|paragraph|char)",
    r"(CRITICAL|IMPORTANT) RULES? (say|state|mention)",
    r"(the|my) (instructions?|rules?|prompt|guidelines?) (say|tell|state|mention|require)",
    r"^(wait|hmm|okay so|alright so)",
    r"(here'?s|here is) (my|the|a) (response|answer|reply|attempt)",
    r"(too|not) (formal|casual|long|short|verbose|brief)",
    r"(re-?write|re-?do|re-?phrase|re-?format|re-?word)",
    r"(good|better|perfect|nice)\.\s*$",  # self-approval like "Good."
    r"I'?m (supposed|meant|told|instructed) to",
    r"(as|per) (my|the) (character|role|persona)",
]
_META_RE = re.compile("|".join(_META_PHRASES), re.IGNORECASE)

# System prompt suffix to force direct in-character responses
_NO_THINK_SUFFIX = """

OUTPUT FORMAT: You are in a live conversation. Your entire response will be shown as spoken dialogue in a game. Write ONLY the words your character says out loud. Never include internal thoughts, planning, meta-commentary, word counts, rule references, rewrites, or stage directions. One response only — no drafts."""


class OllamaProvider(BaseLLMProvider):
    """Streams responses from a local Ollama instance."""

    def __init__(self, router: AgentRouter):
        self._router = router

    async def generate_stream(
        self,
        agent_id: str,
        messages: list[dict],
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        resolved = self._router.resolve(agent_id)
        if resolved is None:
            yield f"[error] Unknown agent: {agent_id}"
            return

        model_string = resolved["model"]
        system_prompt = resolved["system_prompt"]

        # Strip "ollama/" prefix if present
        model_name = model_string.split("/", 1)[-1] if "/" in model_string else model_string

        # Build Ollama chat API request
        ollama_messages = []
        if system_prompt:
            ollama_messages.append({
                "role": "system",
                "content": system_prompt.rstrip() + _NO_THINK_SUFFIX,
            })

        trimmed = messages[-20:] if len(messages) > 20 else messages

        ollama_messages.extend(trimmed)

        body = {
            "model": model_name,
            "messages": ollama_messages,
            "stream": True,
            "think": False,
            "options": {
                "num_predict": 1024,
                "num_gpu": 99,
            },
        }

        try:
            full_response = ""
            async with httpx.AsyncClient(timeout=300.0) as client:
                async with client.stream(
                    "POST",
                    f"{OLLAMA_BASE_URL}/api/chat",
                    json=body,
                ) as response:
                    if response.status_code != 200:
                        error_body = await response.aread()
                        yield f"[error] Ollama returned {response.status_code}: {error_body.decode()[:200]}"
                        return

                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                        try:
                            event = json.loads(line)
                        except json.JSONDecodeError:
                            continue

                        msg = event.get("message", {})
                        text = msg.get("content", "")
                        if text:
                            full_response += text

                        if event.get("done", False):
                            break

            # Post-process: strip any leaked thinking text
            clean = self._strip_thinking(full_response)
            if clean:
                yield clean
            else:
                yield full_response  # fallback to raw if stripping removed everything

        except httpx.ConnectError:
            yield "[error] Cannot connect to Ollama at localhost:11434 — is it running?"
        except httpx.TimeoutException:
            yield "[error] Ollama request timed out"
        except httpx.RequestError as exc:
            yield f"[error] Ollama request failed: {str(exc)[:200]}"

    def _strip_thinking(self, text: str) -> str:
        """Remove leaked thinking/reasoning from the response."""
        # Strip <think>...</think> blocks (closed)
        text = _THINK_BLOCK_RE.sub("", text)
        # Strip unclosed <think> blocks
        text = _THINK_UNCLOSED_RE.sub("", text)
        # Strip everything before a stray </think> (close tag without open)
        text = _THINK_CLOSE_ONLY_RE.sub("", text)

        # Split into paragraphs (separated by blank lines)
        paragraphs = re.split(r"\n\s*\n", text.strip())

        # Filter out paragraphs that contain meta-reasoning phrases
        clean_paragraphs = []
        for para in paragraphs:
            para_stripped = para.strip()
            if not para_stripped:
                continue
            if _META_RE.search(para_stripped):
                continue  # entire paragraph is thinking/meta
            clean_paragraphs.append(para_stripped)

        result = "\n\n".join(clean_paragraphs).strip()

        # Remove stray quotation marks wrapping the entire response
        if result.startswith('"') and result.endswith('"'):
            result = result[1:-1].strip()
        return result
