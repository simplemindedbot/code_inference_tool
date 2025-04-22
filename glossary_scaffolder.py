import json
from pathlib import Path

def scaffold_glossary(features, output_path='domain_terms.json'):
    terms = set(features.get("variables", []) + features.get("strings", []))
    glossary = {term: f"Describe what `{term}` represents." for term in terms if isinstance(term, str)}

    with open(output_path, 'w') as f:
        json.dump(glossary, f, indent=2)
    print(f"✅ Glossary scaffold written to {output_path}")
