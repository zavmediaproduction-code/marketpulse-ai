# MarketPulse AI — PH + US starter app

This is a runnable early-warning market research dashboard. It includes:
- Economic / market indicator cards
- Recent public-news headlines via the GDELT DOC API
- Philippine and US watchlists
- A transparent alert score based on recent price movement and historical volatility

## Important limitations
- This is **not** a predictive AI model and does not calculate the probability a stock will rise or fall.
- Yahoo Finance data through `yfinance` may be delayed, incomplete, or unavailable for some Philippine tickers.
- GDELT headlines are broad news discovery, not verified financial analysis.
- The alert score is a screening aid, not a buy/sell recommendation.
- No automated push notifications, user accounts, cloud hosting, or brokerage integration are included.

## Run locally

1. Install Python 3.10 or newer.
2. Unzip this folder.
3. Open a terminal in the folder and run:

   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate

   pip install -r requirements.txt
   streamlit run app.py
   ```

4. Streamlit will open the dashboard in your browser.

## Next production steps
1. Choose licensed/reliable data providers for PSE and US prices, fundamentals, corporate actions and news.
2. Add a backend database and scheduled ingestion jobs.
3. Build event-to-company exposure mapping with source citations and confidence levels.
4. Backtest alert rules and publish precision/false-positive statistics.
5. Add user accounts, watchlists and email/push alerts.
6. Deploy to a secured cloud host.

Never put paid-provider API keys in frontend code. Store them as server-side environment secrets.
