import json
from config import client, SCHEMA, CAPABILITIES

SYSTEM_PROMPT = (
    "You are Stage 1 of a fashion-retail chatbot pipeline. "
    "Classify whether a question is answerable using the supplied "
    "dataset schema and capability document. Return valid JSON only. "
    "Do not add Markdown or explanations outside the JSON."
)

ALLOWED_CLASSIFICATIONS = {
    "answerable",
    "partially_answerable",
    "unanswerable",
    "out_of_scope"
}


def sanity_check(question: str, context: str = "") -> dict:
    question = question.strip()

    if not question:
        return {
            "classification": "out_of_scope",
            "reason": "Empty question received.",
            "proceed_to_planning": False,
            "proxy_used": None
        }

    if len(question) > 500:
        return {
            "classification": "out_of_scope",
            "reason": "Question too long. Please ask a concise question.",
            "proceed_to_planning": False,
            "proxy_used": None
        }

    conversation_block = (
        f"\nCONVERSATION HISTORY (use this to resolve follow-up questions):\n{context}\n"
        if context else ""
    )

    prompt = f"""
Determine whether the user's question can be answered using
the supplied fashion-retail dataset, directly or through a
clearly explained alternative metric.

DATASET SCHEMA:
{SCHEMA}

DATASET CAPABILITIES AND LIMITATIONS:
{CAPABILITIES}

Classify the question as exactly one of:
- answerable
- partially_answerable
- unanswerable
- out_of_scope

Decision guidelines:
- answerable: the requested information can be retrieved or calculated.
- partially_answerable: only part can be answered, or a useful alternative metric is needed.
- unanswerable: required information is absent and no meaningful alternative can be offered.
- out_of_scope: unrelated to this fashion-retail catalog.
- If the schema contains the required columns, treat those operations as supported.
- Matching records may or may not exist. Stage 2 will query the database.
- Do not confuse product counts, seller labels, rankings, popularity, and actual sales.
- Do not reject a question merely because some values are missing.
- Do not assume undocumented metric definitions.
- Apply CRITICAL REMAPS before classifying.
- If an alternative metric is used, identify it in proxy_used.
- If no alternative is used, proxy_used must be null.
- Do not invent data or columns.

Return valid JSON with exactly these keys:
- classification: one of the four allowed values
- reason: a concise explanation of one or two sentences
- proceed_to_planning: Boolean
- proxy_used: the alternative metric used, or null
{conversation_block}
User question: {question}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0
        )

        parsed = json.loads(response.choices[0].message.content)

        required_keys = {"classification", "reason", "proceed_to_planning", "proxy_used"}

        if not isinstance(parsed, dict):
            raise ValueError("Response must be a JSON object.")
        if set(parsed.keys()) != required_keys:
            raise ValueError(f"Unexpected keys: {set(parsed.keys())}")

        classification = parsed["classification"]
        if classification not in ALLOWED_CLASSIFICATIONS:
            raise ValueError(f"Invalid classification: {classification}")
        if not isinstance(parsed["reason"], str):
            raise ValueError("Reason must be a string.")
        if parsed["proxy_used"] is not None and not isinstance(parsed["proxy_used"], str):
            raise ValueError("proxy_used must be a string or null.")
        if classification == "answerable" and parsed["proxy_used"] is not None:
            parsed["classification"] = "partially_answerable"
            classification = parsed["classification"]

        # Derive in Python — never trust the LLM for this
        parsed["proceed_to_planning"] = classification in {"answerable", "partially_answerable"}

        print(f"[stage1] '{question[:60]}' -> {classification}")
        return parsed

    except (json.JSONDecodeError, ValueError, TypeError, KeyError) as e:
        print(f"[stage1] ERROR: {e}")
        return {
            "classification": "unanswerable",
            "reason": "Sanity check could not be completed reliably.",
            "proceed_to_planning": False,
            "proxy_used": None
        }