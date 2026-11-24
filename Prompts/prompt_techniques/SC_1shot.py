PROMPT = """\
You are a highly accurate and rule-abiding information extraction expert in the field of effort estimation. 
Your task is to identify which specific predictors were explicitly or clearly used for effort estimation in a research paper.

You are given:
1. A research paper.
2. A list of VALID PREDICTORS, each consisting of a predictor name and a description (in parentheses).

---
### EXAMPLE TASK
--- PAPER START ---
{example_paper}
--- PAPER END ---

--- VALID PREDICTORS ---
{taxonomy}
--- END LIST ---

### EXAMPLE REASONING:
Step 1: Read the paper and locate all effort estimation mentions.  
Step 2: Identify all terms or variables used in that context.  
Step 3: Compare each one to the predictor names and their descriptions.  
Step 4: Match predictor names if the meaning aligns clearly, even if wording differs.  
Step 5: Finalize a list of matched predictor names based on explicit or clear use.

### EXAMPLE FINAL OUTPUT:
web page count, new web page count, adapted high feature count, project type, new media Count, high feature count, low feature count, programming language experience level, team size, media count, adapted low feature count, number of programming languages,spi program, metrics’ program, documentation level, reused feature count, new high feature count, new low feature count, web application type
---

### YOUR TASK
Your job is to strictly follow the reasoning steps below as in the example.

### STEP-BY-STEP INSTRUCTIONS
1. Carefully read and understand the paper.
2. Focus only on the parts of the paper that discuss **effort estimation**.
3. For each predictor in the VALID PREDICTORS list, read both its **name** and its **description** to fully understand what it means.
4. Check whether the paper mentions a concept, variable, or term that matches the predictor **by name** or matches its **meaning based on the description**.
5. If a match exists, include ONLY the exact predictor name from the VALID PREDICTORS list in the final output.
6. If no predictor names from the list are explicitly or clearly used for effort estimation, return 'None'.

### IMPORTANT RULES
- Descriptions can be used to confirm a match, even if the paper uses different wording.
- Do NOT guess — only match if the connection is clear based on the name or description.
- Final output must be a comma-separated list of matched **predictor names** exactly as they appear in the VALID PREDICTORS list.
- If nothing matches, return exactly 'None'.

--- PAPER START ---
{paper}
--- PAPER END ---

--- VALID PREDICTORS ---
**Predictor name (description)**
{taxonomy}
--- END LIST ---

### FINAL OUTPUT FORMAT:
Return a comma-separated list of matched predictor names from the VALID PREDICTORS list, or 'None'.
"""
