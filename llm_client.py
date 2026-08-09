from google import genai
import json

def analyze_error(stack_trace: str, endpoint: str, status_code: int, 
                    file_path: str, source_code: str, api_key: str) -> dict:
    
    client = genai.Client(api_key=api_key)
    
    prompt = f"""You are a senior software debugging engineer.

Analyze the provided API failure and relevant source code.
Identify the most likely root cause.
Identify the exact affected file and line range.
Generate a production-ready code patch.
Do not invent files or code that are not supported by the provided context.
The patch must preserve existing application behavior unless the error requires a behavioral change.

Return ONLY valid JSON, with no markdown formatting, no code fences, matching exactly this schema:

{{
  "root_cause": "string explaining the root cause",
  "confidence": 0-100 integer,
  "affected_files": [
    {{"file": "path", "start_line": int, "end_line": int}}
  ],
  "explanation": "string",
  "changes": [
    {{"file": "path", "start_line": int, "end_line": int, "replacement_code": "string"}}
  ]
}}

--- ERROR DETAILS ---
Endpoint: {endpoint}
Status Code: {status_code}
Stack Trace:
{stack_trace}

--- SOURCE CODE ---
File: {file_path}
{source_code}
"""

    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=prompt
    )
    
    raw_text = response.text.strip()
    
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
    
    return json.loads(raw_text)