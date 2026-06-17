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
{{"requirements": [{{"title": "short descriptive title (3-6 words, NOT a code like REQ-XXX)", "description": "full description of what the system must do", "type": "functional", "priority": "medium", "is_ambiguous": false, "ambiguity_reason": null}}]}}

Types: functional, security, performance, availability, compliance, interface
Priorities: critical, high, medium, low
Rules:
- title must be a short human-readable label, never a code like REQ-001
- description must be the full requirement sentence
- detect the correct type (security, performance, etc.) from the content
- mark is_ambiguous=true if the requirement uses vague words without measurable criteria
Return max 10 requirements. JSON only, no explanation."""
