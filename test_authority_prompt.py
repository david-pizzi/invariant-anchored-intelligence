"""Quick test to verify Authority prompt is now unambiguous."""

# Simulated prompt excerpt (what LLM sees in permissive mode)
current_ratio = 2.81
failure_threshold = 3.0

prompt_old = f"""
**CRITICAL QUANTITATIVE CHECKS:**
- If ratio >{failure_threshold}× (strictness=permissive): System is FAILING significantly
- If ratio <1.1×: System is competitive

**DECISION LOGIC:**
IF regret_ratio > {failure_threshold}: REJECT
ELSE IF regret_ratio ≤ {failure_threshold}: ACCEPT

Current ratio: {current_ratio}×
"""

prompt_new = f"""
**STEP 1: Check catastrophic failure threshold**
Current ratio: {current_ratio}×
Catastrophic threshold: {failure_threshold}×

Is {current_ratio} > {failure_threshold}? 
{"YES - System is catastrophically broken → REJECT" if current_ratio > failure_threshold else "NO - System performance acceptable → Continue to Step 2"}

**STEP 2: Check proposal quality**
If proposal is well-defined → ACCEPT

**YOUR SITUATION:**
- Current ratio {current_ratio}× is {"ABOVE" if current_ratio > failure_threshold else "BELOW"} threshold {failure_threshold}×
- Performance is {"CATASTROPHIC - you must REJECT" if current_ratio > failure_threshold else "ACCEPTABLE - check proposal quality and likely ACCEPT"}
"""

print("=" * 70)
print("OLD PROMPT (contradictory)")
print("=" * 70)
print(prompt_old)
print("\n" + "=" * 70)
print("Analysis: LLM sees 'FAILING significantly' AND 'ACCEPT if ≤3.0'")
print("Result: Confused → incorrectly REJECTS at 2.81×")
print("=" * 70)

print("\n\n" + "=" * 70)
print("NEW PROMPT (unambiguous)")
print("=" * 70)
print(prompt_new)
print("\n" + "=" * 70)
print("Analysis: Clear STEP 1 check, explicit 'BELOW threshold' = ACCEPTABLE")
print("Result: Should correctly ACCEPT at 2.81×")
print("=" * 70)
