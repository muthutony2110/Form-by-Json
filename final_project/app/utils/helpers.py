import re
import codecs
import json
from pydantic import ValidationError
from models.schema import FormDefinition, ControlType, Control, GridProperties, Dimension, Column, Row, ParentProperties

def extract_json(text: str) -> str:
    text = re.sub(r"```", "", text)
    text = text.replace("```", "")
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return ""
    json_str = match.group(0)
    for _ in range(2):
        try:
            json_str = codecs.decode(json_str, 'unicode_escape')
        except Exception:
            break
    return json_str.strip()

def safe_json_loads(s: str):
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return None

def validate_formdefinition(payload):
    if hasattr(FormDefinition, "model_validate"):
        return FormDefinition.model_validate(payload)
    return FormDefinition.parse_obj(payload)

try:
    valid_controls = list(ControlType.__args__)
except AttributeError:
    valid_controls = []

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
    Control(id="FORM001", name="BookingForm", type="Form", properties={}, templateId="Form1"),
    Control(id="GRID001", name="BookingGrid", type="Grid", properties=grid_props, templateId="Grid1", parentId="FORM001"),
    Control(id="LBL001", name="LabelFullName", type="TextBlock", templateId="TextBlock1", parentId="GRID001",
            parentProperties=ParentProperties(column=1, row=1),
            properties={"text": "Full Name:", "editable": False, "visible": "Visible"}),
    Control(id="TXT001", name="TextBoxFullName", type="TextBox", templateId="TextBox1", parentId="GRID001",
            parentProperties=ParentProperties(column=2, row=1),
            properties={"placeholder": "Enter Full Name", "value": "", "valueType": "string", "visible": "Visible"}),
    Control(id="LBL002", name="LabelEmail", type="TextBlock", templateId="TextBlock1", parentId="GRID001",
            parentProperties=ParentProperties(column=1, row=2),
            properties={"text": "Email:", "editable": False, "visible": "Visible"}),
    Control(id="TXT002", name="TextBoxEmail", type="TextBox", templateId="TextBox1", parentId="GRID001",
            parentProperties=ParentProperties(column=2, row=2),
            properties={"placeholder": "Enter Email", "value": "", "valueType": "email", "visible": "Visible"}),
]

example_form = FormDefinition(
    clientWorkflows=[],
    serverWorkflows=[],
    clientTriggers=[],
    serverTriggers=[],
    controls=example_controls
).model_dump()
