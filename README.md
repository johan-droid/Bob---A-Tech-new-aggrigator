# ☕ Bob — The Agentic News Portal

**Bob** is a SaaS-grade intelligence aggregator designed for high-performance signal tracking across the tech and AI ecosystem. Built with a premium "Midnight Espresso" aesthetic, it delivers rich, synthesized intelligence reports from 20+ diverse sources.

![Bob Dashboard Mockup](https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&q=80&w=2070)

## 🌟 Key Features
- **Midnight Coffee Aesthetic**: A high-fidelity dark theme featuring glassmorphism, staggered animations, and developer-centric typography.
- **20+ Intelligence Channels**: Real-time signals from GitHub (Trending, Releases, Topics), Hacker News, ArXiv, Hugging Face, TechCrunch, and more.
- **Rich Repository Intelligence**: Automated synthesis of GitHub metadata into structured momentum reports and strategic significance analysis.
- **SaaS-Grade Architecture**: Partitioned Frontend (Next.js) and Backend (Python) for independent scaling and production-ready deployments.
- **Automated Pipeline**: Integrated GitHub Actions for hourly crawling and anti-sleep pings to keep the engine running 24/7.

## 🏗️ Project Structure
```text
├── frontend/           # Next.js 16+ App, Drizzle ORM, Tailwind CSS
├── backend/            # Python 3.11 Scraper, Crawl4AI, BeautifulSoup4
└── .github/workflows/  # Unified Intelligence Pipeline (Scraper + Keep-Alive)
```

## 🚀 Quick Start

### 1. Prerequisites
- Node.js 18+
- Python 3.11+
- Neon PostgreSQL (or any Postgres instance)

### 2. Setup
```bash
# Install Frontend Dependencies
cd frontend
npm install

# Install Backend Dependencies
cd ../backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
python -m playwright install chromium
```

### 3. Local Development
Run the unified development stack from the root:
```bash
npm run dev:all
```

## 🌍 Deployment
Detailed instructions for **Vercel** and **Render** are available in [README_DEPLOY.md](./README_DEPLOY.md).

## 🛡️ License
Distributed under the MIT License. See `LICENSE` for more information.

---
*Notice: This intelligence signal is aggregated for informational and research purposes. All original trademarks and intellectual property belong to their respective owners.*
