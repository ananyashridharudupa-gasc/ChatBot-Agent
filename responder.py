import json
from config import client


def generate_response(question: str, sanity_result: dict, plan: dict, results: list, context: str = "") -> str:
    conversation_block = (
        f"\nCONVERSATION HISTORY:\n{context}\n"
        if context else ""
    )

    prompt = f"""
You are a helpful fashion retail assistant.
Answer the user's question using only the supplied database results.
{conversation_block}

Rules:
- Do not invent products, prices, brands, or statistics.
- If results are empty, clearly say no matching products were found.
- Format prices in Indian rupees (rupees) rounded to 2 decimal places.
- Keep the answer concise and easy to read.
- Include product name, brand, and price when available in results.
- Include product URLs only when present in results.
- If a proxy metric was used, explain it clearly.
- Do not claim popularity or labels prove actual sales.
- Mention only relevant data limitations.
- Rows that share product_name are one product shown in more than one color.
- A result column named value is the real aggregate for the whole match, not a sample.
- If a grouped result has as many rows as the query limit, say the list is capped.
- Preserve the order of results exactly as returned.

Original question: {question}
Sanity check: {json.dumps(sanity_result, default=str)}
Query plan: {json.dumps(plan, default=str)}
Database results: {json.dumps(results, default=str)}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "Generate accurate, concise answers grounded strictly in database results."
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    return response.choices[0].message.content.strip()