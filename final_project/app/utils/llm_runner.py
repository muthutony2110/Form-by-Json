import subprocess
from app.utils.helpers import extract_json

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
    except subprocess.CalledProcessError:
        return None, None
