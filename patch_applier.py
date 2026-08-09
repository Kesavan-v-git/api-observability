def apply_change_to_file(original_content: str, start_line: int, end_line: int, replacement_code: str) -> str:
    """
    Takes the full original file content, and replaces lines start_line to end_line
    (1-indexed, inclusive) with replacement_code.
    """
    lines = original_content.split("\n")
    
    # Convert to 0-indexed
    before = lines[:start_line - 1]
    after = lines[end_line:]
    
    new_lines = before + replacement_code.split("\n") + after
    return "\n".join(new_lines)