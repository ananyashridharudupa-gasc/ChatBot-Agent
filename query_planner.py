import json
from config import client, SCHEMA, CAPABILITIES

ALLOWED_COLUMNS = {
    "_id", "channel_id", "sku", "color", "color_filled",
    "common_color", "product_id", "brand", "product_name",
    "product_search_text", "rank_absolute", "rank_percentile",
    "rank_label", "niche_score", "popularity", "discount",
    "calculated_discount_pct", "discount_mismatch", "rating",
    "has_rating", "rating_count", "review_count",
    "has_review_count", "launch_on", "last_seen_date",
    "pdp_url", "feature_image", "mrp_USD", "mrp_INR",
    "selling_price_USD", "selling_price_INR"
}

NUMERIC_COLUMNS = {
    "rank_absolute", "rank_percentile", "niche_score", "popularity",
    "discount", "calculated_discount_pct", "discount_mismatch",
    "rating", "rating_count", "review_count", "mrp_USD", "mrp_INR",
    "selling_price_USD", "selling_price_INR"
}

ALLOWED_OPERATORS = {"=", "!=", ">", ">=", "<", "<=", "contains", "in"}


def plan_queries(question: str, sanity_result: dict, context: str = "") -> dict:
    conversation_block = (
        f"\nCONVERSATION HISTORY (use this to resolve follow-up questions):\n{context}\n"
        if context else ""
    )

    prompt = f"""
Create a structured query plan for this fashion-retail question.
{conversation_block}
QUESTION:
{question}

STAGE 1 RESULT:
{json.dumps(sanity_result, indent=2)}

SCHEMA:
{SCHEMA}

CAPABILITIES:
{CAPABILITIES}

Return JSON with exactly these keys:
- operation: select, count, group_count, avg, min, or max
- select_columns: list of column names
- filters: list of objects with column, operator, value
- group_by: list of column names
- order_by: object with column and direction
- limit: integer from 1 to 100 for select, or 1 to 500 otherwise
- explanation: brief explanation

Rules:
- Use only columns listed in the schema.
- Allowed filter operators: =, !=, >, >=, <, <=, contains, in.
- Use select to retrieve records.
- Use count to count matching records.
- Use group_count to count records per group.
- For group_count, group_by must contain at least one column.
- For count, select_columns and group_by must be empty.
- For select, select_columns must contain at least one column.
- Use an empty filters list when there are no filters.
- Use order_by column=null and direction=asc if no sorting is needed.
- direction must be asc or desc.
- For group_count, order_by column may be a grouping column or count.
- Use the proxy identified by Stage 1 when applicable.
- Never equate product counts or seller labels with actual sales.
- Do not write SQL.
- For keyword or name-based searches, use the 'contains' operator on product_search_text.
- For comparison questions involving two specific products, use the 'in' operator on product_name with both product titles as the value list.
- Always include product_name, brand, selling_price_INR, rating, rank_label, common_color in select_columns for product retrieval questions so Stage 3 has enough data to compare.
- Use avg, min, or max for an average, minimum, or maximum. select_columns must contain exactly one numeric column. group_by may list columns, or be empty.
- For avg, min, or max, order_by column may be value or a grouping column.
- For a full group_count or grouped aggregate, set limit to 500. Use a small limit only for a top-N question.
- Best rank: order rank_absolute ascending, or rank_percentile descending. Higher popularity is better, so order it descending.
- For a standard color (beige, black, blue, brown, green, grey, multicolor, orange, pink, purple, red, white, yellow), filter common_color with =.
- For a shade such as navy, maroon, blush, or sand, filter color_filled with contains. Do not use the color column.
- To count products by color, group by common_color.

Return valid JSON only.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Generate structured query plans. Return JSON only."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0
    )

    plan = json.loads(response.choices[0].message.content)
    validate_plan(plan)
    print(f"[stage2] operation={plan['operation']} filters={len(plan['filters'])}")
    return plan


def validate_plan(plan: dict) -> None:
    required_keys = {
        "operation", "select_columns", "filters",
        "group_by", "order_by", "limit", "explanation"
    }

    if not isinstance(plan, dict) or set(plan) != required_keys:
        raise ValueError("Invalid query-plan structure.")
    if plan["operation"] not in {"select", "count", "group_count", "avg", "min", "max"}:
        raise ValueError("Unsupported operation.")
    if not isinstance(plan["select_columns"], list):
        raise ValueError("select_columns must be a list.")
    if not isinstance(plan["filters"], list):
        raise ValueError("filters must be a list.")
    if not isinstance(plan["group_by"], list):
        raise ValueError("group_by must be a list.")
    if not isinstance(plan["limit"], int) or isinstance(plan["limit"], bool):
        raise ValueError("limit must be an integer.")
    max_limit = 100 if plan["operation"] == "select" else 500
    if not 1 <= plan["limit"] <= max_limit:
        raise ValueError(f"limit must be between 1 and {max_limit}.")
    if not isinstance(plan["explanation"], str):
        raise ValueError("explanation must be a string.")

    for column in plan["select_columns"] + plan["group_by"]:
        if not isinstance(column, str) or column not in ALLOWED_COLUMNS:
            raise ValueError(f"Unsupported column: {column}")

    if len(set(plan["select_columns"])) != len(plan["select_columns"]):
        raise ValueError("Duplicate selected columns.")
    if len(set(plan["group_by"])) != len(plan["group_by"]):
        raise ValueError("Duplicate grouping columns.")

    if plan["operation"] == "select":
        if not plan["select_columns"]:
            raise ValueError("Select requires at least one column.")
        if plan["group_by"]:
            raise ValueError("Select does not support grouping.")
    elif plan["operation"] == "count":
        if plan["select_columns"] or plan["group_by"]:
            raise ValueError("Count requires empty select_columns and group_by.")
    elif plan["operation"] == "group_count":
        if not plan["group_by"]:
            raise ValueError("group_count requires group_by.")
        if plan["select_columns"]:
            raise ValueError("group_count requires empty select_columns.")
    elif plan["operation"] in {"avg", "min", "max"}:
        if len(plan["select_columns"]) != 1:
            raise ValueError("Aggregate requires exactly one column.")
        if plan["select_columns"][0] not in NUMERIC_COLUMNS:
            raise ValueError("Aggregate column must be numeric.")

    for item in plan["filters"]:
        if not isinstance(item, dict):
            raise ValueError("Each filter must be an object.")
        if set(item) != {"column", "operator", "value"}:
            raise ValueError("Invalid filter structure.")

        column = item["column"]
        operator = item["operator"]
        value = item["value"]

        if not isinstance(column, str) or column not in ALLOWED_COLUMNS:
            raise ValueError(f"Unsupported filter column: {column}")
        if operator not in ALLOWED_OPERATORS:
            raise ValueError(f"Unsupported operator: {operator}")
        if operator == "in":
            if not isinstance(value, list) or not value:
                raise ValueError("'in' requires a non-empty list.")
            if not all(v is None or type(v) in (str, int, float) for v in value):
                raise ValueError("Unsupported value in 'in' filter.")
        elif value is not None and type(value) not in (str, int, float):
            raise ValueError("Unsupported filter value.")
        if operator == "contains" and not isinstance(value, str):
            raise ValueError("'contains' requires a string.")

    order = plan["order_by"]
    if not isinstance(order, dict) or set(order) != {"column", "direction"}:
        raise ValueError("Invalid order_by structure.")

    order_column = order["column"]
    direction = order["direction"]

    if direction not in {"asc", "desc"}:
        raise ValueError("Sort direction must be asc or desc.")

    if order_column is not None:
        if order_column == "count":
            if plan["operation"] != "group_count":
                raise ValueError("'count' sorting requires group_count.")
        elif order_column == "value":
            if plan["operation"] not in {"avg", "min", "max"}:
                raise ValueError("'value' sorting requires an aggregate.")
        elif order_column not in ALLOWED_COLUMNS:
            raise ValueError(f"Unsupported sort column: {order_column}")
        if (
            plan["operation"] == "group_count"
            and order_column != "count"
            and order_column not in plan["group_by"]
        ):
            raise ValueError("group_count can sort only by a grouping column or count.")
        if (
            plan["operation"] in {"avg", "min", "max"}
            and plan["group_by"]
            and order_column != "value"
            and order_column not in plan["group_by"]
        ):
            raise ValueError("Grouped aggregate can sort only by a grouping column or value.")


def build_sql(plan: dict) -> tuple:
    validate_plan(plan)

    if plan["operation"] == "select":
        columns = ", ".join(f'"{c}"' for c in plan["select_columns"])
        sql = f"SELECT {columns} FROM products"
    elif plan["operation"] == "count":
        sql = "SELECT COUNT(*) AS count FROM products"
    elif plan["operation"] == "group_count":
        groups = ", ".join(f'"{c}"' for c in plan["group_by"])
        sql = f"SELECT {groups}, COUNT(*) AS count FROM products"
    else:
        func = plan["operation"].upper()
        column = f'"{plan["select_columns"][0]}"'
        if plan["group_by"]:
            groups = ", ".join(f'"{c}"' for c in plan["group_by"])
            sql = f"SELECT {groups}, {func}({column}) AS value FROM products"
        else:
            sql = f"SELECT {func}({column}) AS value FROM products"

    params = []
    conditions = []

    for item in plan["filters"]:
        column = f'"{item["column"]}"'
        operator = item["operator"]
        value = item["value"]

        if value is None and operator in {"=", "!="}:
            null_op = "IS NULL" if operator == "=" else "IS NOT NULL"
            conditions.append(f"{column} {null_op}")
        elif operator == "contains":
            conditions.append(f"LOWER({column}) LIKE LOWER(?)")
            params.append(f"%{value}%")
        elif operator == "in" and item["column"] in {"product_name", "product_search_text"}:
            if any(v is None for v in value):
                raise ValueError("Null values in 'in' filters must be handled separately.")
            likes = " OR ".join(f"LOWER({column}) LIKE LOWER(?)" for _ in value)
            conditions.append(f"({likes})")
            params.extend(f"%{v}%" for v in value)
        elif operator == "in":
            if any(v is None for v in value):
                raise ValueError("Null values in 'in' filters must be handled separately.")
            if all(isinstance(v, str) for v in value):
                placeholders = ", ".join("LOWER(?)" for _ in value)
                conditions.append(f"LOWER({column}) IN ({placeholders})")
            else:
                placeholders = ", ".join("?" for _ in value)
                conditions.append(f"{column} IN ({placeholders})")
            params.extend(value)
        elif operator in {"=", "!="} and isinstance(value, str):
            conditions.append(f"LOWER({column}) {operator} LOWER(?)")
            params.append(value)
        else:
            conditions.append(f"{column} {operator} ?")
            params.append(value)

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    if plan["group_by"] and plan["operation"] in {"group_count", "avg", "min", "max"}:
        groups = ", ".join(f'"{c}"' for c in plan["group_by"])
        sql += f" GROUP BY {groups}"

    order = plan["order_by"]
    if order["column"] is not None:
        if order["column"] in {"count", "value"}:
            order_column = order["column"]
        else:
            order_column = f'"{order["column"]}"'
        sql += f" ORDER BY {order_column} {order['direction'].upper()}"

    sql += " LIMIT ?"
    params.append(plan["limit"])

    return sql, params