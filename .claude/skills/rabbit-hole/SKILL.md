---
name: rabbit-hole
description: Follow a bug to its deepest root cause using the 5 Whys technique. Use for mysterious bugs that keep coming back.
allowed-tools: Read, Grep, Glob, Bash
---

# Rabbit Hole Explorer

## Philosophy

Don't fix symptoms. Find the disease.

Every bug is a symptom of something deeper. Your job is to keep asking "WHY?" until you hit bedrock.

## The 5 Whys Technique

1. **Why** did this bug happen?
2. **Why** did that cause this?
3. **Why** was that possible?
4. **Why** wasn't that prevented?
5. **Why** is the system designed this way?

Keep going until you hit one of:
- Architectural flaw
- Wrong assumption baked into the code
- Missing validation at a boundary
- Race condition
- Cosmic ray (very rare, but valid)

## Instructions

1. Start with the observable bug
2. Trace the execution path
3. At each step, ask "but WHY?"
4. Document each layer of the rabbit hole
5. Find the TRUE root cause
6. Propose the fix at the RIGHT level (not just a bandaid)

## Output Format

```
🕳️ RABBIT HOLE EXPLORATION

**Surface symptom**: [what the user sees]

**Layer 1**: [immediate cause]
  ↓ but why?
**Layer 2**: [deeper cause]
  ↓ but why?
**Layer 3**: [even deeper]
  ↓ but why?
**Layer 4**: [getting close]
  ↓ but why?
**Layer 5**: [ROOT CAUSE]

**Depth reached**: [how many layers]
**Root cause type**: [architecture | assumption | validation | race condition | external]

**The real fix**: [fix at the root, not the symptom]
**Bandaid fix**: [if you must ship today, do this, but schedule the real fix]
```

## Warning

Sometimes the rabbit hole goes DEEP. You might find that fixing the root cause requires significant refactoring. That's okay. At least now you KNOW.
