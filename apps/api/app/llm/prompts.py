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
