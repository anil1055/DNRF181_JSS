PROMPT = """"\
You are a highly accurate and rule-abiding information extraction expert in the field of web effort estimation. 
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

### EXAMPLE REASONING (Metacognitive Style):
1. Read the paper and highlight effort estimation mentions.  
2. Determine which classes in CLASS hierarchy are related to paper
3. Check predictors list of related classes to understand their meaning.  
4. Find matching concepts in the paper.  
5. Critically evaluate if they are **explicitly or clearly used** for effort estimation.  
6. Reflect: Have I avoided assumptions? Do matches follow the rules?  
7. Confirm confidence in chosen predictors.  

### EXAMPLE FINAL OUTPUT:
Length: web page count, new web page count, new media Count, media count
Functionality: reused feature count, new high feature count, new low feature count, adapted low feature count, high feature count, low feature count, adapted high feature count 
Development company: spi program, metrics’ program
Project: documentation level, project type, number of programming languages
Team: programming language experience level, team size
Product: web application type
---

### YOUR TASK
Follow the same metacognitive reasoning process as in the example.

### REASONING PROCESS (Metacognitive Style)
1. Read and fully understand the paper’s content, focusing only on sections that discuss **effort estimation**.
2. For each CLASS under the class hierarchy, evaluate to determine which classes are related to paper. 
3. For each predictor in the VALID PREDICTORS of related classes, carefully read both the **name** and **description** to fully understand its meaning.
4. Scan the paper for terms, variables, or concepts that match:
   - The predictor name exactly, or clearly equivalent concept based on the description.
5. For each potential match, critically evaluate:
   - Is it explicitly or clearly used for effort estimation?
   - Does it align with the predictor’s meaning based on its description?
6. Include ONLY the exact predictor name from the VALID PREDICTORS list if it meets these criteria.
7. Reflect on the chosen predictors:
   - Are they strictly within scope?
   - Have you avoided assumptions or guessing?
   - Are you confident they comply with all rules?
8. Finalize your output after ensuring your reasoning is accurate and complete.

### STRICT RULES
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
