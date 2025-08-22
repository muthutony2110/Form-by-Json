# model.py
from typing import List, Optional, Dict, Any, Literal, Union
from pydantic import BaseModel


ControlType = Literal[
    "Button", "Grid", "TextBox", "Dropdown", "StackPanel", "TextBlock", "ToggleButton",
    "CheckBox", "CheckBoxGroup", "Radio", "RadioGroup", "Form", "FormViewer", "Icon",
    "Hyperlink", "Tab", "TableViewer", "DatePicker", "InputMask", "Image", "Password",
    "TextArea", "Rating", "Webviewer", "ValidationPlaceholder", "AutoCompleteTextbox",
    "FileUpload", "Repeater", "Header", "Canvas", "RichTextBox", "RichText", "HtmlViewer",
    "ConditionalViewer", "Label", "FormRouter", "Chips", "DataGrid"
]


# --- Layout models ---
class Dimension(BaseModel):
    size: Optional[int] = None
    unit: Optional[str] = None


class Column(BaseModel):
    id: int
    width: Dimension


class Row(BaseModel):
    id: int
    height: Dimension


class GridProperties(BaseModel):
    columnGap: Optional[Dimension]
    rowGap: Optional[Dimension]
    columns: List[Column]
    rows: List[Row]


class ParentProperties(BaseModel):
    column: Optional[int] = None
    row: Optional[int] = None


# --- Common property models ---
class TextBoxProperties(BaseModel):
    placeholder: Optional[str] = None
    value: Optional[str] = ""
    valueType: Optional[str] = "string"
    visible: str = "Visible"


class TextBlockProperties(BaseModel):
    text: str
    editable: bool
    visible: str = "Visible"


class ButtonProperties(BaseModel):
    text: str
    visible: str = "Visible"


class DropdownProperties(BaseModel):
    options: List[str]
    selectedOption: Optional[str] = ""
    visible: str = "Visible"


class DatePickerProperties(BaseModel):
    value: Optional[str] = ""
    visible: str = "Visible"


class GenericProperties(BaseModel):
    data: Optional[Dict[str, Any]] = {}
    visible: str = "Visible"


# --- Union for dynamic properties ---
ControlPropertiesType = Union[
    GridProperties,
    TextBoxProperties,
    TextBlockProperties,
    ButtonProperties,
    DropdownProperties,
    DatePickerProperties,
    GenericProperties,
    Dict[str, Any]  # fallback to allow any other properties
]


# --- Core control model ---
class Control(BaseModel):
    id: str
    name: str
    type: ControlType
    properties: ControlPropertiesType
    templateId: str
    parentId: Optional[str] = None
    parentProperties: Optional[ParentProperties] = None


# --- Root form definition ---
class FormDefinition(BaseModel):
    clientWorkflows: List[Any] = []
    serverWorkflows: List[Any] = []
    clientTriggers: List[Any] = []
    serverTriggers: List[Any] = []
    controls: List[Control]


