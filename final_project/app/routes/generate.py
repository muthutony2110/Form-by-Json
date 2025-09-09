import json
from flask import Blueprint, request, jsonify
from app.utils.helpers import (
    extract_json, safe_json_loads, validate_formdefinition,
    example_form, valid_controls
)
from app.utils.llm_runner import run_llm

generate_blueprint = Blueprint('generate', __name__)

@generate_blueprint.route('/generate', methods=['POST'])
def generate_json():
    data = request.get_json()
    user_prompt = (data.get("prompt") or "").strip()
    if not user_prompt:
        return jsonify({"error": "Please provide a 'prompt'"}), 400

    instructions = f"""
You are a JSON UI generator for NextGenForms Studio.

STRICT RULES:
0. Output ONLY valid pure JSON, no extra text or formatting.
1. The root control must be a Form or FormViewer.
2. Include a Grid container child with layout at least 5 rows and 1 column.
3. All other controls must be direct children of the Grid with parentId 'GRID001' and proper parentProperties for layout.
4. Use only these control types: {', '.join(valid_controls)}
5. Follow exactly this example schema and control layout:

{json.dumps(example_form, indent=2)}

6. Controls should have meaningful filled properties and all must have 'visible' set to 'Visible'.
7. Adapt control count and specific control types logically to user prompt, but keep structure.
8. DO NOT output any text besides pure JSON.

User Prompt:
{user_prompt}
"""

    raw, cleaned = None, None
    for _ in range(5):
        raw, cleaned = run_llm(instructions)
        if not cleaned:
            continue
        json_output = safe_json_loads(cleaned)
        if not json_output:
            continue
        try:
            form_obj = validate_formdefinition(json_output)
            return jsonify(form_obj.model_dump() if hasattr(form_obj, "model_dump") else form_obj.dict())
        except Exception:
            instructions += "\nEnsure output is STRICTLY valid JSON."
            continue

    return jsonify({"error": "Failed to generate valid form JSON after multiple attempts."}), 500
