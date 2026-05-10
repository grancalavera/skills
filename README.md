# Skills

Personal agent skills repository following the [Agent Skills specification](https://agentskills.io/specification).

## Structure

```
skills/
├── AGENTS.md
├── package.json
├── README.md
└── skills/
    └── <skill-name>/
        └── SKILL.md
```

Each skill lives in its own directory under `skills/` with a `SKILL.md` file containing frontmatter (`name`, `description`) and instructions.

## Usage

Install as a pi package:

```bash
pi install git:github.com/grancalavera/skills
```

Or add to settings:

```json
{
  "packages": ["git:github.com/grancalavera/skills"]
}
```
