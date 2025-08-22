from flask import Flask, request, jsonify
import subprocess
import json
import re
import codecs
from pydantic import ValidationError
from model import FormDefinition, Control, ControlType, Dimension, Column, Row, GridProperties, ParentProperties

app = Flask(__name__)

try:
    valid_controls = list(ControlType.__args__)
except AttributeError:
    valid_controls = []

def extract_json(text: str) -> str:
    # Remove markdown code fences and optional language tag
    text = re.sub(r"```", "", text)
    text = text.replace("```", "")

    # Try to find a balanced JSON object using regex
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return ""

    json_str = match.group(0)

    # Try unescaping multiple times to handle deeply escaped JSON strings
    for _ in range(2):
        try:
            json_str = codecs.decode(json_str, 'unicode_escape')
        except Exception:
            break

    return json_str.strip()

def run_llm(prompt: str):
    try:
        process = subprocess.Popen(
            ["ollama", "run", "deepseek-coder-v2:16b", prompt],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        output, _ = process.communicate()
        raw_output = output.strip()
        cleaned_output = extract_json(raw_output)
        return raw_output, cleaned_output
    except subprocess.CalledProcessError as e:
        return None, None

def safe_json_loads(s: str):
    try:
        return json.loads(s)
    except json.JSONDecodeError as e:
        print(f"JSONDecodeError: {e}")
        return None

def validate_formdefinition(payload):
    if hasattr(FormDefinition, "model_validate"):
        return FormDefinition.model_validate(payload)
    return FormDefinition.parse_obj(payload)

grid_props = GridProperties(
    columnGap=Dimension(size=20, unit="PX"),
    rowGap=Dimension(size=20, unit="PX"),
    columns=[Column(id=1, width=Dimension(size=1, unit="FR"))],
    rows=[
        Row(id=1, height=Dimension(size=50, unit="PX")),
        Row(id=2, height=Dimension(size=50, unit="PX")),
        Row(id=3, height=Dimension(size=50, unit="PX")),
        Row(id=4, height=Dimension(size=50, unit="PX")),
        Row(id=5, height=Dimension(size=100, unit="PX")),
    ]
)

example_controls = [
    Control(
        id="FORM001", name="BookingForm", type="Form", properties={}, templateId="Form1"
    ),
    Control(
        id="GRID001", name="BookingGrid", type="Grid", properties=grid_props, templateId="Grid1", parentId="FORM001"
    ),
    Control(
        id="LBL001", name="LabelFullName", type="TextBlock", templateId="TextBlock1", parentId="GRID001",
        parentProperties=ParentProperties(column=1, row=1),
        properties={"text": "Full Name:", "editable": False, "visible": "Visible"}
    ),
    Control(
        id="TXT001", name="TextBoxFullName", type="TextBox", templateId="TextBox1", parentId="GRID001",
        parentProperties=ParentProperties(column=2, row=1),
        properties={"placeholder": "Enter Full Name", "value": "", "valueType": "string", "visible": "Visible"}
    ),
    Control(
        id="LBL002", name="LabelEmail", type="TextBlock", templateId="TextBlock1", parentId="GRID001",
        parentProperties=ParentProperties(column=1, row=2),
        properties={"text": "Email:", "editable": False, "visible": "Visible"}
    ),
    Control(
        id="TXT002", name="TextBoxEmail", type="TextBox", templateId="TextBox1", parentId="GRID001",
        parentProperties=ParentProperties(column=2, row=2),
        properties={"placeholder": "Enter Email", "value": "", "valueType": "email", "visible": "Visible"}
    ),
]

example_form = FormDefinition(
    clientWorkflows=[],
    serverWorkflows=[],
    clientTriggers=[],
    serverTriggers=[],
    controls=example_controls
).model_dump()


@app.route('/generate', methods=['POST'])
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

    raw = cleaned = None
    MAX_RETRIES = 5
    for attempt in range(MAX_RETRIES):
        raw, cleaned = run_llm(instructions)
        print(f"Attempt {attempt + 1} raw output:", repr(raw))
        print(f"Attempt {attempt + 1} cleaned JSON:", repr(cleaned))

        if not cleaned:
            print("No JSON extracted, retrying...")
            continue

        json_output = safe_json_loads(cleaned)
        if not json_output:
            print("JSON parsing failed, retrying...")
            continue

        try:
            form_obj = validate_formdefinition(json_output)
            return jsonify(form_obj.model_dump() if hasattr(form_obj, "model_dump") else form_obj.dict())
        except ValidationError as e:
            print(f"Validation error on attempt {attempt + 1}: {e}")
            instructions += "\nEnsure output is STRICTLY valid JSON with all required fields exactly as in the example."
            continue

    return jsonify({"error": "Failed to generate valid form JSON after multiple attempts.", "last_raw_output": raw}), 500


if __name__ == '__main__':
    app.run(debug=True)
