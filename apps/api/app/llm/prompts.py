SUMMARIZE_FILE_SYSTEM = (
    "You are a senior software engineer. Analyze code files and return structured JSON. "
    "Be concise and precise. Respond with valid JSON only, no markdown."
)

SUMMARIZE_FILE_PROMPT = """\
Analyze the following code file and return JSON only.

File: {file_path}
Language: {language}
Content (first {char_count} chars):
{content}

JSON format:
{{"summary": "1-2 sentence description of what this file does", "role": "one of: component|service|util|config|test|model|router|worker|other", "entities": ["MainClass", "key_function", "CONSTANT_NAME"]}}

Return max 8 entities. JSON only."""

EXTRACT_REQUIREMENTS_SYSTEM = (
    "Tu es un expert en ingénierie des exigences logicielles. "
    "Tu analyses des documents de spécification et extrais les exigences. "
    "Réponds uniquement en JSON valide, sans commentaire ni markdown."
)

EXTRACT_REQUIREMENTS_PROMPT = """\
Extract software requirements from the text below. Return JSON only.

Text:
{document_text}

JSON format:
{{"requirements": [{{"title": "short title", "description": "full description", "type": "functional", "priority": "medium", "is_ambiguous": false, "ambiguity_reason": null}}]}}

Types: functional, security, performance, availability, compliance, interface
Priorities: critical, high, medium, low
Return max 10 requirements. JSON only, no explanation."""
