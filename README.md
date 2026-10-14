# Catalog Chatbot

Chat interface for a fashion catalog of 8,108 dresses. Questions are turned into read-only queries against the bundled database (`fashion.db`), and the reply is written from those rows.

## What you can ask

- Find products by name, brand, or color.
- Count products by brand, color, or seller label.
- Compare MRP and selling price in INR or USD.
- Look at discounts from the calculated discount percentage.
- Compare ratings and review counts where those values exist.
- Rank products with `rank_label`, `rank_percentile`, `rank_absolute`, or the popularity score.
- Ask how much of a field is filled in.

Follow-up questions in the same chat keep the earlier filters. For example, a color filter can be followed by a price limit.

Phrases like "best selling" and "most popular" are answered with rank and popularity fields. The catalog has no units sold. "Trending" is answered from highly ranked products in this snapshot, not from change over time. "Reviews" means the review count. There is no review text.

## What the catalog does not contain

- Units sold, sales volume, or revenue.
- Current stock or availability.
- Written customer reviews.
- History beyond this one snapshot.
- Store rankings.

If a question needs one of those, the chatbot says so instead of filling in a number.

## Run

Docker Desktop and an OpenAI API key are required.

Copy `.env.example` to `.env` and replace the placeholder with your OpenAI API key:

```text
OPENAI_API_KEY=sk-your-key-here
```

Start Docker Desktop, then:

```powershell
docker compose up --build
```

Open http://localhost:8501. Stop the app with Ctrl+C.
