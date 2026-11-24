PROMPT = """\
You are a highly accurate and rule-abiding information extraction expert in the field of effort estimation. 
Your task is to identify which specific predictors with hierarchical class were explicitly or clearly used for effort estimation in a research paper.

You are given:
1. A research paper.
2. A class hierarchy contains nine CLASS that each predictor belongs to exactly one class, define as -CLASS: [VALID PREDICTORS] 
3. A list of VALID PREDICTORS of each CLASS, each consisting of a predictor name and a description (in parentheses).

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
Step 2: Determine which classes in CLASS hierarchy are related to paper
Step 3: Identify all terms or variables used in effort estimation context.  
Step 4: Compare each one to the predictor names and their descriptions of related classes.  
Step 5: Match predictor names if the meaning aligns clearly, even if wording differs.  
Step 6: Finalize a list of matched predictor names with related class based on explicit or clear use.

### EXAMPLE FINAL OUTPUT:
Length: web page count, new web page count, new media Count, media count
Functionality: reused feature count, new high feature count, new low feature count, adapted low feature count, high feature count, low feature count, adapted high feature count 
Development company: spi program, metrics’ program
Project: documentation level, project type, number of programming languages
Team: programming language experience level, team size
Product: web application type
---

### YOUR TASK
Your job is to strictly follow the reasoning steps below as in the example.

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
