# Skill: handoff-doc-update

Update the `HANDOFF.md` of the current project (or create it if it doesn't exist yet) following the fixed format and rules below.

---

## Purpose of a Handoff

A handoff is a signpost, not a log. Written for a fresh reader (human or AI session) who knows nothing of the session history. Guideline: keep it under 150 lines. Full history belongs in commits and code, not in this document.

---

## Fixed Structure (top to bottom)

1. **Title + "Last updated: `<date>`"**
2. **Session blocks, newest on top.** Each block starts with:
   ```
   ► TOPIC (session <date>, PUSHED <commit-hash> / NOT PUSHED)
   ```
   followed by bullets describing what was completed.
3. **A block "▶️ START HERE (fresh session)"**: one paragraph stating what the most recent work was, what the next action is, and whether there are any blockers.
4. **"Outstanding actions owner/others"**: actions that do NOT belong to the next work session but to a specific person.
5. **"NEXT SESSION — pick up here"**: numbered, prioritized list.
6. **Below a `---` divider**: stable reference that rarely changes (what & why, locations, stack, how to run, key files, backlog, loose notes).

---

## Writing Rules (hard rules)

1. **Every claim anchored to evidence**: commit hash, filename, test count, URL. Not "reviews work" but "review chain complete, pushed through a5b940c, 65 tests green".
2. **Status always explicit**: pushed or not, deployed or not, blockers yes/no.
3. **Next steps with order and dependencies**: note when a step depends on another ("do step 2 first, because without X you can't measure step 1").
4. **Decisions always with the reason**, marked with words like "deliberate", "owner choice", "NOT in this commit" — so a future session doesn't undo an intentional decision.
5. **Compress old session blocks**: anything older than the last 2–3 sessions gets compressed to one line per session in a "Done" list at the bottom. Detail points to commits or a separate document, not repeated here.
6. **Below the fold only stable reference**: if a section changes every session it belongs at the top in the session blocks.

---

## Workflow

Execute these steps in order:

1. **Read the existing `HANDOFF.md`** if it exists.
2. **Fetch the git log** since the previous "Last updated" date:
   ```bash
   git log --oneline --since="<previous date>"
   ```
   If there is no existing HANDOFF.md, fetch the last 20 commits:
   ```bash
   git log --oneline -20
   ```
3. **Determine push status** of recent commits:
   ```bash
   git log --oneline origin/main..HEAD
   ```
4. **Write a new session block at the top** with the commits and work from this session.
5. **Update "▶️ START HERE"** with the current state of affairs.
6. **Update "NEXT SESSION"** with prioritized actions.
7. **Compress session blocks** older than 2–3 sessions to one line per session.
8. **Remove nothing from the stable reference** without reporting it.
9. **Check at the end**:
   - Is every commit hash correct?
   - Is push status included?
   - Is the document under ~150 lines?
   - Are all hard writing rules followed?

---

## Template for new HANDOFF.md

If `HANDOFF.md` does not yet exist, use this as a starting point:

```markdown
# HANDOFF — <Project name>
Last updated: <date>

## ▶️ START HERE (fresh session)
<One paragraph: what is the most recent work, what is the next action, are there any blockers?>

---

## Session Blocks

► <TOPIC> (session <date>, PUSHED <commit-hash> / NOT PUSHED)
- <bullet of what was completed>
- <bullet of what was completed>

---

## Outstanding actions owner/others

- [ ] <action> — @<name>

---

## NEXT SESSION — pick up here

1. <step 1>
2. <step 2> (depends on step 1)
3. <step 3>

---

## Stable Reference

### What & Why
<Short description of the project and its goal.>

### Stack & Locations
<Tech stack, important directories, entry points.>

### How to run
<Commands to start/test the project locally.>

### Key files
<List of the most critical files with one-line explanation each.>

### Backlog
<Known open items not yet being picked up.>

### Loose notes
<Gotchas, technical debt, decisions that need explanation.>
```
