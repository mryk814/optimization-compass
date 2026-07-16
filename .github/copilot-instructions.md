# Optimization Compass coding-agent instructions

Before modifying this repository, read and follow:

1. [`../AGENTS.md`](../AGENTS.md)
2. [`../docs/adding-knowledge.md`](../docs/adding-knowledge.md)
3. [`../.agents/skills/optimization-compass-maintenance/SKILL.md`](../.agents/skills/optimization-compass-maintenance/SKILL.md)

Key rules:

- edit canonical inputs, never generated SQLite/site/release/Trace artifacts by hand;
- classify the change before editing;
- preserve stable IDs and explicit `unknown` / `not_applicable` / `unsupported` states;
- keep methods and implementations distinct;
- use authoritative sources and never use Qiita or Zenn as evidence;
- run the validation tier required by the change;
- stop rather than inventing identity, schema, source, release, or renderer-contract decisions.
