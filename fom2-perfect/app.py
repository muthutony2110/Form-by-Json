# app.py
from flask import Flask, request, jsonify
import subprocess
import json
import re
from pydantic import ValidationError
from model import FormDefinition, Control, ControlType, Dimension, Column, Row, GridProperties, ParentProperties


app = Flask(__name__)

try:
    valid_controls = list(ControlType.__args__)
except AttributeError:
    valid_controls = []


def extract_json(text: str) -> str:
    # Clean up and extract JSON object from LLM output text
    text = re.sub(r"```", "", text)
    text = text.replace("```", "")
    start = text.find("{")
    if start == -1:
        return text.strip()
    depth = 0
    for i, ch in enumerate(text[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start:i+1].strip()
    return text.strip()


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
    except json.JSONDecodeError:
        # Attempt to fix mismatched braces, a best effort
        s += "}" * (s.count("{") - s.count("}"))
        return json.loads(s)


def validate_formdefinition(payload):
    if hasattr(FormDefinition, "model_validate"):
        return FormDefinition.model_validate(payload)
    return FormDefinition.parse_obj(payload)


# Example Grid layout for prompt guidance
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

# Full example form controls for LLM prompt guidance - structure and properties highlighting
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
    # Add more controls as desired matching your example JSON structure
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
0. Output ONLY pure JSON without any explanations or extra text.
1. The root must be a Form or FormViewer control.
2. Include a Grid container with a layout of at least 5 rows and 1 column inside the root.
3. All other controls must be children of the Grid with parentId 'GRID001' and have explicit parentProperties showing the column and row.
4. Use only these control types: {', '.join(valid_controls)}
5. Follow exactly this schema and control layout sample:
{json.dumps(example_form, indent=2)}
6. Controls should include labels, textboxes, dropdowns, date pickers, buttons as shown.
7. All controls must be visible with 'visible': 'Visible'.
8. Fill all control properties meaningfully and relevant to the user prompt.
9. The number of controls can be adjusted but must keep the given structure and alignment.

User Prompt:
{user_prompt}
"""

    raw = cleaned = None
    MAX_RETRIES = 3
    for attempt in range(MAX_RETRIES):
        try:
            raw, cleaned = run_llm(instructions)
            if not raw:
                return jsonify({"error": "LLM timed out"}), 504
            
            json_output = safe_json_loads(cleaned)
            form_obj = validate_formdefinition(json_output)
            return jsonify(form_obj.model_dump() if hasattr(form_obj, "model_dump") else form_obj.dict())

        except (json.JSONDecodeError, ValidationError) as e:
            print(f"Attempt {attempt+1} JSON/Validation error: {e}")
            if attempt == MAX_RETRIES - 1:
                return jsonify({"error": "Model output not valid JSON or validation failed", "raw_output": raw}), 500
            
            instructions += "\nEnsure output is STRICTLY valid JSON according to the provided schema without any text."
        except subprocess.CalledProcessError as e:
            return jsonify({"error": "LLM command failed", "details": e.stderr}), 500


if __name__ == '__main__':
    app.run(debug=True)

