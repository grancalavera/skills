# Fix skills-ref validation

## Problem

The `npm run validate` script uses `npx skills-ref`, which resolves to an npm package published by an unrelated maintainer (`yc.ma <yanchaoma@foxmail.com>`). It is not the official reference library from the Agent Skills spec.

The official `skills-ref` is a Python package maintained in the [agentskills repo](https://github.com/agentskills/agentskills/tree/main/skills-ref). The npm package happens to share the name and happens to produce valid-looking output, but it's not guaranteed to track the spec as it evolves.

## Fix

1. Remove the `validate` script from `package.json` — validation should not go through npm.

2. Configure `skills-ref` as a tool in mise. Read the [official README](https://github.com/agentskills/agentskills/tree/main/skills-ref) to understand the API and installation options. Use `skills-ref --help` to understand available commands and flags.

3. Create a mise task that validates all skills in one go.
