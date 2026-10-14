import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SCHEMA = """
Table: products
Description: Fashion-retail product catalog.

Identifiers:
- product_id: Product identifier; unique in the dataset.
- sku: Stock keeping unit; may repeat across records.
- _id: Source record identifier.

Product information:
- product_name: Name or title of the product.
- brand: Brand associated with the product.
- color: Original color field; may be missing.
- color_filled: Color field completed using product images.
- common_color: Standardized color category for grouping (includes 'unknown').
- product_search_text: Search-oriented text associated with the product.
- channel_id: Source channel identifier.

Prices and discounts:
- mrp_INR: Maximum retail price in Indian rupees.
- selling_price_INR: Selling price in Indian rupees.
- mrp_USD: Maximum retail price in US dollars.
- selling_price_USD: Selling price in US dollars.
- discount: Original discount value from the source.
- calculated_discount_pct: Discount calculated from MRP and selling price.
- discount_mismatch: 1 where original discount conflicts with calculated value.

Ratings and reviews:
- rating: Product rating on a 1-5 scale; missing for approximately 4,240 records.
- review_count: Number of reviews; missing for approximately 4,238 records.
- rating_count: Source rating-count field; missing for approximately 7,933 records.
- has_rating: 1 if rating is present, 0 otherwise.
- has_review_count: 1 if review_count is present, 0 otherwise.

Popularity and ranking:
- popularity: Higher value is better. Sort descending for most popular.
- niche_score: Source niche score; definition not documented.
- rank_absolute: Lower number is better. 1 is the best rank. Sort ascending for best products.
- rank_percentile: Higher value is better. About 100 is the best. Sort descending for best products.
- rank_label: Source seller classification: Best Seller, Good Seller, Average Seller, Poor Seller.

Dates:
- launch_on: Product launch date.
- last_seen_date: Date the product was last seen in the source.

Links:
- pdp_url: Product detail page URL.
- feature_image: Product image URL.

The dataset does not contain:
- Actual sales volume or revenue.
- Current inventory or stock levels.
- Written customer review text.
- Historical data beyond the available snapshot.
- Store ranking data; those columns were removed.
"""

CAPABILITIES = """
DATASET: Fashion-retail product catalog containing 8,108 records
from a single catalog snapshot.

IMPORTANT: All 8,108 products in this dataset are dresses. No category filter is needed or available.

WHAT THIS DATASET CAN ANSWER:
- Product lookup and filtering by name, brand, and color.
- Product counts by brand, color, and other available categories.
- Price comparisons using MRP and selling prices in INR and USD.
- Discount analysis using calculated_discount_pct.
- Rating-based comparisons, accounting for missing values.
- Counts of products in each rank_label category.
- Ranking analysis using rank_label, rank_percentile, rank_absolute.
- Popularity comparisons, without assuming popularity means sales.
- Missing-value analysis and data coverage questions.

WHAT THIS DATASET CANNOT DIRECTLY ANSWER:
- Actual units sold, sales volume, or sales revenue.
- Current stock or product availability.
- Customer sentiment because written review text is unavailable.
- Historical trends because only a single snapshot is available.
- Store rankings because the relevant data is unavailable.

CRITICAL REMAPS — apply these before classifying:
- "best selling" → rank by rank_label or rank_percentile. NOT sales data.
- "most popular" → rank by popularity score or review_count. NOT sales data.
- "trending" → attribute prevalence among highly ranked products. NOT time-series growth.
- "in stock" / "available" → unanswerable, inventory data does not exist.
- "reviews" → review COUNT is available; written review TEXT is not.

MISSING DATA RULES:
- Do not reject a question because some values are missing.
- Missing values reduce scope — state the scope, do not fabricate values.
- A missing rating does not mean the product is poorly rated.
"""