Usage: /improve-architecture

Run the improve-codebase-architecture skill.

1. Load the improve-codebase-architecture skill from .claude/skills/improve-codebase-architecture/SKILL.md.

2. Read CONTEXT.md (if present) and all ADRs in docs/adr/ before exploring anything.
   The domain language and recorded decisions constrain what you surface.

3. Use the Explore subagent to walk the codebase organically. Look for shallow modules,
   tightly-coupled seams, code that is hard to test through its current interface, and areas
   where understanding one concept requires bouncing between many small files.
   Apply the deletion test to anything you suspect is shallow.

4. Present a numbered list of deepening opportunities. For each: files involved, the problem
   (why it causes friction), the solution (plain English), and the benefits in terms of
   locality and leverage. Do NOT propose interfaces yet.

5. Ask the user which candidate to explore. Then drop into a grilling loop on that candidate —
   same discipline as /grill-with-docs.

6. Side effects happen inline as decisions crystallise:
   - New term named? Add it to CONTEXT.md.
   - Candidate rejected with a load-bearing reason? Offer an ADR.

Do not re-litigate decisions already captured in ADRs unless the friction clearly warrants reopening one.
Mark any such candidates explicitly: "contradicts ADR-NNNN — worth reopening because…"
