import ast
import tokenize
import difflib
import json
from io import StringIO
import re
import sys

def extract_features_from_code(code: str):
    features = {
        "functions": [],
        "variables": [],
        "strings": [],
        "comments": []
    }

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return features

    try:
        tokens = tokenize.generate_tokens(StringIO(code).readline)
        for token_type, token_string, *_ in tokens:
            if token_type == tokenize.COMMENT:
                features["comments"].append(token_string.strip())
    except tokenize.TokenError:
        pass

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            doc = ast.get_docstring(node)
            features["functions"].append({
                "name": node.name,
                "doc": doc.splitlines()[0] if doc else ""
            })
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    features["variables"].append(target.id)
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            features["strings"].append(node.value.value)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            features["strings"].append(node.value.value)

    return features

def load_glossary(glossary_path):
    try:
        with open(glossary_path, 'r') as f:
            return json.load(f)
    except Exception:
        return {}

def fuzzy_match(term, glossary):
    matches = difflib.get_close_matches(term.lower(), glossary.keys(), n=1, cutoff=0.6)
    if matches:
        return matches[0], glossary[matches[0]]
    return None, None

def infer_requirements(features, glossary):
    requirements = []
    glossary_keys = glossary.keys()

    def score_confidence(evidence_count):
        return round(min(1.0, 0.5 + 0.1 * evidence_count), 2)

    for func in features["functions"]:
        if re.search(r"fee|penalt", func["name"], re.IGNORECASE):
            requirements.append({
                "text": "The system calculates a penalty or fee for a condition.",
                "confidence": score_confidence(2),
                "evidence": f"Function: `{func['name']}`"
            })

    for var in features["variables"]:
        match, desc = fuzzy_match(var, glossary)
        if match:
            requirements.append({
                "text": f"The system uses `{match}`: {desc}.",
                "confidence": score_confidence(2),
                "evidence": f"Variable: `{var}` matched glossary: `{match}`"
            })

    for comment in features["comments"]:
        if 'validate' in comment.lower():
            requirements.append({
                "text": "The system includes validation logic.",
                "confidence": score_confidence(1),
                "evidence": f"Comment: `{comment}`"
            })

    return requirements

def explain_and_write_output(features, requirements, output_path):
    with open(output_path, 'w') as out:
        out.write("# Code Analysis Summary\n\n## 📌 Extracted Features\n\n")
        out.write("**Functions**:\n")
        for f in features["functions"]:
            out.write(f"- `{f['name']}`: {f['doc']}\n")
        out.write("\n**Variables**:\n")
        for v in features["variables"]:
            out.write(f"- `{v}`\n")
        out.write("\n**Strings**:\n")
        for s in features["strings"]:
            out.write(f"- \"{s}\"\n")
        out.write("\n**Comments**:\n")
        for c in features["comments"]:
            out.write(f"- {c}\n")
        out.write("\n---\n\n## 💡 Inferred Business Requirements\n\n")
        for i, req in enumerate(requirements, 1):
            out.write(f"### BR-{i:03}\n")
            out.write(f"**{req['text']}**  \n")
            out.write(f"Confidence: {req['confidence']}  \n")
            out.write(f"Evidence: {req['evidence']}\n\n")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Infer business requirements from Python code.")
    parser.add_argument('--input', type=str, help="Path to Python file")
    parser.add_argument('--glossary', type=str, help="Path to glossary JSON file")
    parser.add_argument('--output', type=str, default="summary.md", help="Path to output markdown file")
    args = parser.parse_args()

    default_code = """
# Calculate late fees
def calculate_late_fee(days_overdue):
    if days_overdue > 0:
        return days_overdue * 5
    return 0

customer_id = "ABC123"
"""
    default_glossary = {
        "customer_id": "A unique identifier for each customer",
        "late_fee": "Penalty applied after the payment due date",
        "overdue": "Past the expected time for action or payment"
    }

    code = open(args.input, 'r').read() if args.input else default_code
    glossary = load_glossary(args.glossary) if args.glossary else default_glossary

    features = extract_features_from_code(code)
    requirements = infer_requirements(features, glossary)
    explain_and_write_output(features, requirements, args.output)
    print(f"✅ Analysis complete. See: {args.output}")

if __name__ == "__main__":
    main()
