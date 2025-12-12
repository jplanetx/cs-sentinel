# 🛡️ CS Sentinel: Autonomous Churn Prevention Agent

**A specialized AI agent that monitors customer health, detects "ghosting" signals, and drafts hyper-personalized retention emails.**

## 💼 The Business Problem
SaaS companies lose revenue when they miss the subtle signs of churn. Manual monitoring is too slow, and generic automation feels like spam.
* **The Gap:** High-touch CSMs can't watch every account every day.
* **The Solution:** An always-on agent that audits usage patterns 24/7.

## 🤖 How It Works (The Logic)
The Sentinel uses a State Machine architecture to ensure safety and accuracy:

1.  **Monitor:** Connects to live customer data (Google Sheets/CRM).
2.  **Analyze:** Applies a 2-stage risk detection algorithm:
    * *New Accounts:* Flags "Failure to Launch" (No login > 21 days).
    * *Veterans:* Flags "Ghosting" (Usage drop > 50% AND 2+ ignored emails).
3.  **Draft:** Uses OpenAI (GPT-4o) to write a context-aware draft (e.g., "Helpful Nudge" vs. "Strategic Audit").
4.  **Wait:** Pauses for Human Approval (Human-in-the-Loop).
5.  **Execute:** Logs the sent email and updates the database.

## 🛠️ Tech Stack
* **Core:** Python 3.11
* **Brain:** OpenAI GPT-4o (API)
* **Memory:** Google Sheets API (gspread)
* **Security:** Dotenv (.env) for key management

## 🚀 Deployment
1.  Clone the repo.
2.  Install dependencies: `pip install -r requirements.txt`
3.  Add secrets to `.env`.
4.  Run `python sentinel_brain.py`.

---
*Built by [JPXL Labs](https://jpxllabs.com) - Automating the Future of Work.*