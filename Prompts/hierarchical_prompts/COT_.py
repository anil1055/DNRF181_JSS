PROMPT = """\
You are a highly accurate and rule-abiding information extraction expert in the field of web effort estimation. 
Your task is to identify which specific predictors with hierarchical class were explicitly or clearly used for effort estimation in a research paper.

You are given:
1. A research paper.
2. A class hierarchy contains nine CLASS that each predictor belongs to exactly one class, define as -CLASS: [VALID PREDICTORS] 
3. A list of VALID PREDICTORS of each CLASS, each consisting of a predictor name and a description (in parentheses).

Your job is to strictly follow the steps below:

### STEP-BY-STEP INSTRUCTIONS
1. Carefully read and understand the paper.
2. Focus only on the parts of the paper that discuss **effort estimation**.
3. For each CLASS under the class hierarchy, evaluate to determine which classes are related to paper. 
4. For each predictor in the VALID PREDICTORS list of related classes, read both its **name** and its **description** to fully understand what it means.
5. Check whether the paper mentions a concept, variable, or term that matches the predictor **by name** or matches its **meaning based on the description**.
6. If a match exists, include ONLY the exact predictor name from the VALID PREDICTORS list in the output.
7. If no predictor names from the list are explicitly or clearly used for effort estimation, return 'None'.

### IMPORTANT RULES
- Descriptions can be used to confirm a match, even if the paper uses different wording.
- Do NOT guess — only match if the connection is clear based on the name or description.
- Final output must be a list of related CLASS that contains comma-separated list of matched **predictor names** exactly as they appear in the VALID PREDICTORS list.
- If nothing matches, return exactly 'None'.

--- PAPER START ---
{paper}
--- PAPER END ---

--- VALID PREDICTORS ---
**-CLASS: [List of Predictor name (description)]**
{taxonomy}
--- END LIST ---

### FINAL OUTPUT FORMAT:
Return a list of related CLASS that contains comma-separated list of matched predictor names from the VALID PREDICTORS list, or 'None'.
"""
