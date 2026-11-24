PROMPT = """"\
You are a highly accurate and rule-abiding information extraction expert in the field of web effort estimation. 
Your task is to identify which specific predictors with hierarchical class were explicitly or clearly used for effort estimation in a research paper.

You are given:
1. A research paper.
2. A class hierarchy contains nine CLASS that each predictor belongs to exactly one class, define as -CLASS: [VALID PREDICTORS] 
3. A list of VALID PREDICTORS of each CLASS, each consisting of a predictor name and a description (in parentheses).

Follow the Plan-and-Solve strategy strictly.
### PLAN
1. **Understand the Paper**  
   - Read the entire paper carefully, focusing only on sections related to **effort estimation**.  
2. **Select Related Classes**
   - For each CLASS under the class hierarchy, evaluate to determine which classes are related to paper. 
3. **Understand the Predictors List**  
   - Review both the **predictor names** and their **descriptions** to fully understand their meaning for related classes.  
4. **Matching Strategy**  
   - Identify all terms, variables, or concepts in the paper that are explicitly or clearly used for effort estimation.  
   - Consider a match if:
     - The paper uses the predictor name exactly, OR  
     - The paper uses a clearly equivalent concept as described in the predictor’s description.  
5. **Prepare for Output**  
   - From the VALID PREDICTORS list of related classes, select only those that meet the above criteria.

### SOLVE
1. Apply your matching strategy without guessing or inferring from loosely related content.  
2. Include only the exact predictor names from the VALID PREDICTORS list of related classes that are explicitly or clearly used for effort estimation in the paper.  
3. If no matches exist, return **'None'** exactly. 

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
