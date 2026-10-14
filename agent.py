from database import execute_readonly_query
from sanity_check import sanity_check
from query_planner import plan_queries, build_sql
from responder import generate_response


def build_context(history: list) -> str:
    """
    Build a plain text summary of the last 6 messages (3 exchanges).
    Passed to Stage 2 and Stage 3 so they understand follow-up questions.
    """
    if not history:
        return ""
    recent = history[-6:]
    return "\n".join(
        f"{m['role'].upper()}: {m['content']}"
        for m in recent
    )


def run(question: str, history: list = None) -> dict:
    """
    Orchestrates the three-stage pipeline.
    Returns all stage outputs so the UI can display them.

    Stage 1 — sanity_check:  is this question answerable?
    Stage 2 — plan_queries:  what query plan answers it?
              build_sql:     turn the plan into parameterized SQL
    Stage 3 — generate_response: turn results into a natural language answer

    history: list of {"role": "user"/"assistant", "content": "..."} dicts
             from the Streamlit session. Used to resolve follow-up questions
             like "now show me below 2000" after "show me red dresses".
    """
    if history is None:
        history = []

    context = build_context(history)

    # Stage 1
    sanity_result = sanity_check(question, context)

    if not sanity_result["proceed_to_planning"]:
        return {
            "sanity": sanity_result,
            "plan": None,
            "sql": None,
            "results": [],
            "answer": sanity_result["reason"]
        }

    try:
        # Stage 2 — pass context so follow-up filters resolve correctly
        plan = plan_queries(question, sanity_result, context)
        sql, params = build_sql(plan)

        print(f"[sql] {sql}")
        print(f"[params] {params}")

        # Execute — read-only, parameterized, validated
        results = execute_readonly_query(sql, params)
        print(f"[results] {len(results)} rows returned")

        # Stage 3 — pass context so answer references prior conversation
        answer = generate_response(question, sanity_result, plan, results, context)
    except Exception as e:
        print(f"[run] ERROR: {e}")
        return {
            "sanity": sanity_result,
            "plan": None,
            "sql": None,
            "results": [],
            "answer": "I could not complete that query."
        }

    return {
        "sanity": sanity_result,
        "plan": plan,
        "sql": sql,
        "results": results,
        "answer": answer
    }