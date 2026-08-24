---
name: grilling
description: Grill the user relentlessly about a plan, decision, or idea. Use when the user wants to stress-test their thinking, or uses any 'grill' trigger phrases.
---

Interview user relentlessly until shared understanding reached. Map as **design tree**: every decision branches into decisions hanging off it.

Work tree in **rounds**. **Frontier** = every decision whose prerequisites already settled — questions you can ask _now_ without guessing unheard answers. Ask whole frontier in one round: number each question, give recommended answer. Then wait for user's answers before next round.

Format each question like so:

```
❓ **Q1** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

➡️ <your recommended answer>
```

Each round of user answers reshapes tree — settled decisions push frontier outward, unblock questions that depended on them. Recompute frontier, ask next round. A question whose answer depends on another question still open this round belongs to a _later_ round, not this one.

Finding _facts_ is your job, never the user's. When a frontier question needs a fact from environment (filesystem, tools, etc.), dispatch a sub-agent to find it — don't ask user for anything you could look up yourself. Don't block on it: a running exploration is an unsettled prerequisite, so only questions downstream of it wait for the sub-agent to report — ask rest of frontier now. The _decisions_ are the user's — put each to them and wait.

Session done when frontier empty: every branch of design tree visited, nothing left silently assumed. Do not act on it until user confirms shared understanding reached.
