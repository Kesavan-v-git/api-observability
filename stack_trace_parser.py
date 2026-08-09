import re
import os

def extract_file_and_line(stack_trace: str):
    """
    Looks for all 'File "...", line N' entries in a traceback,
    then returns the LAST one that isn't inside a venv/site-packages/
    stdlib folder, converted to a repo-relative filename.
    """
    matches = re.findall(r'File[,]?\s*"?([^",\n]+\.\w+)"?,?\s*line\s*(\d+)', stack_trace)

    if not matches:
        return None, None

    ignore_markers = ("site-packages", "venv", "lib\\python", "lib/python")

    for file_path, line_number in reversed(matches):
        normalized = file_path.replace("\\", "/").lower()
        if not any(marker in normalized for marker in ignore_markers):
            return os.path.basename(file_path.strip()), int(line_number)

    file_path, line_number = matches[-1]
    return os.path.basename(file_path.strip()), int(line_number)