Usage: /handoff [next session focus]

Run the handoff skill.

1. Load the handoff skill from .claude/skills/handoff/SKILL.md.

2. Survey what exists in the project that a fresh agent can reference directly — do not duplicate:
   - specs/<feature-name>/requirements.md, design.md, tasks.md, status.md
   - bugs/<feature-name>/report.md
   - CONTEXT.md and docs/adr/
   - Recent commits or diffs

3. Write a handoff document covering only what those files do not: decisions made but not yet
   written down, things tried and rejected mid-session, the next concrete step, and any gotchas
   discovered during this session.

4. Include a "Suggested skills" section naming the skills and commands the next agent should invoke
   (e.g. "/spec-execute 3 <name> — use test-first for the parser").

5. If the user passed an argument, tailor the document to that next-session focus.

6. Save to the OS temp directory — not the project workspace.

7. Redact any sensitive information: API keys, credentials, PII, internal hostnames.
