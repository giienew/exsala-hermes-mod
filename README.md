# EXSALA HERMES MOD

<p align="center">
  <b>An adaptive execution profile + skill collection for Hermes Agent</b><br/>
  For power users who want leaner, faster, no-confirmation interactions with their own instance.
</p>

<!--
tags:
  - github
  - hermes
  - hermes-agent
  - jailbreak
  - jailbreak-prompts
  - llm
  - llm-agents
  - prompt-injection
  - prompt-injection-prompts
  - prompt-engineering
  - ai-agent
  - llm-agents
  - jailbreak-prompts
  - prompt
  - llm-agents-prompt
  - github-actions
  - automation
  - ai
  - prompt-hacking
  - jailbreaking
  - zero-refusal
  - open-source
  - prompts
  - generative-ai
  - parser
  - profile
  - skills
  - ai-agent-framework
  - cli
  - llms
  - jailbreaks
-->

---

## What is this

EXSALA HERMES MOD is a **configuration profile + skill collection** for [Hermes Agent](https://hermes-agent.nousresearch.com/docs/) (the open-source AI agent by Nous Research).

It adjusts a local Hermes instance to run in **streamlined execution mode**:

- **Fewer confirmation prompts** — the assistant acts on instructions directly.
- **No safety-lecture chatter** — concise, task-focused replies without unsolicited caveats.
- **Model-agnostic** — works the same regardless of the underlying model (DeepSeek, GLM, Qwen, MiMo, ...).
- **A clean status banner** at the start of every new session.
- **170 skills included** — automation, web, security research, media, productivity, coding helpers, and more, ready to use.

It does **not** change your model provider, API keys, or personal data.

---

## Installation

Requirements: Linux VPS/server with Hermes Agent (≥ 0.22), `bash`, `python3`, `curl`.

### One-line

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/giienew/exsala-hermes-mod/main/install.sh)
```

### Manual

```bash
git clone https://github.com/giienew/exsala-hermes-mod.git
cd exsala-hermes-mod
bash install.sh
```

### What the installer changes

| Setting | After | Notes |
|---|---|---|
| `agent.system_prompt` | EXSALA profile | Replaces default behavioral prompt |
| `approvals.mode` (+ `*_mode`) | `off` | No confirmation prompts |
| `security.tirith_enabled` | `false` | Local content-gating off |
| `security.tirith_fail_open` | `true` | Fail-open |
| `security.protected_instruction_files` | `false` | Allow project context files |
| `~/.hermes/skills/` | +170 skills | Merged, never deletes existing |

> See **[config.example.yaml](config.example.yaml)** for a full annotated reference config with every jailbreak setting — copy the relevant keys into your own `~/.hermes/config.yaml` if you prefer manual setup over the installer.

### What is NEVER touched

- `model.api_key` — your provider key untouched
- `model.base_url` / `model.default` / `fallback_providers` — routing untouched
- `.env` — secrets stay private
- `platforms.*.home_channel` — chat IDs intact
- Your memory, sessions, plugins, other skills

### Safety & rollback

- **Automatic backup:** `~/.hermes/config.yaml.bak-exsala`
- **Restore:** `cp ~/.hermes/config.yaml.bak-exsala ~/.hermes/config.yaml`
- **Idempotent** — re-running is safe; backup is never overwritten.
- Falls back to Python YAML patching if `hermes` isn't on PATH.

---

## After install

1. Restart Hermes (new session, e.g. `/reset`).
2. The EXSALA banner appears.
3. The skill pack is active — any of the 170 skills can be invoked by name.

## Project layout

```
exsala-hermes-mod/
├── install.sh
├── SOUL.md
├── skills/          # 170 skill dirs
└── README.md
```

## License

MIT — use, adapt, improve. No warranty.

<p align="center"><i>EXSALA HERMES MOD</i></p>
