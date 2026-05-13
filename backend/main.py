"""
Bob Intelligence Crawler — SaaS-Grade Backend
═══════════════════════════════════════════════
A resilient, multi-source news intelligence pipeline with:
- Per-source error isolation (one failing source doesn't crash others)
- Structured logging with timestamps and source attribution
- Metrics collection (articles/source, errors, cycle timing)
- Graceful degradation and retry logic
- Configurable crawl intervals
"""

import os
import requests
import json
import uuid
import datetime
import sys
import io
import time
from dataclasses import dataclass, field

# Force UTF-8 encoding for stdout/stderr on Windows
if sys.platform == "win32":
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    else:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# pyrefly: ignore [missing-import]
from crawl4ai import AsyncWebCrawler
import asyncio
# pyrefly: ignore [missing-import]
from bs4 import BeautifulSoup

# ══════════════════════════════════════════
# Configuration
# ══════════════════════════════════════════
INGEST_URL = os.getenv("INGEST_URL", "http://localhost:3000/api/ingest")
CRAWL_INTERVAL = int(os.getenv("CRAWL_INTERVAL", "1800"))  # 30 minutes default
DISCLAIMER = "Notice: This intelligence signal is aggregated for informational and research purposes. All original trademarks, copyrights, and intellectual property belong to their respective owners."

# ══════════════════════════════════════════
# Structured Logging
# ══════════════════════════════════════════
def log(level: str, source: str, message: str):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    icons = {"INFO": "→", "OK": "✓", "WARN": "⚠", "ERR": "✗", "SYS": "◆"}
    icon = icons.get(level, "·")
    print(f"  {icon} [{ts}] [{source:20s}] {message}")

def log_header(text: str):
    print(f"\n{'═' * 60}")
    print(f"  {text}")
    print(f"{'═' * 60}")

def log_separator():
    print(f"  {'─' * 56}")


# ══════════════════════════════════════════
# Metrics Tracker
# ══════════════════════════════════════════
@dataclass
class CycleMetrics:
    started_at: float = field(default_factory=time.time)
    articles_by_source: dict = field(default_factory=dict)
    errors: list = field(default_factory=list)

    def record(self, source: str, count: int):
        self.articles_by_source[source] = count

    def record_error(self, source: str, error: str):
        self.errors.append(f"{source}: {error}")

    @property
    def total_articles(self):
        return sum(self.articles_by_source.values())

    @property
    def elapsed(self):
        return round(time.time() - self.started_at, 1)

    def print_report(self):
        log_separator()
        log("SYS", "METRICS", f"Cycle completed in {self.elapsed}s")
        log("SYS", "METRICS", f"Total articles: {self.total_articles}")
        for src, count in sorted(self.articles_by_source.items()):
            log("OK", "METRICS", f"  {src}: {count} articles")
        if self.errors:
            log("WARN", "METRICS", f"Errors ({len(self.errors)}):")
            for err in self.errors:
                log("ERR", "METRICS", f"  {err}")
        log_separator()


# ══════════════════════════════════════════
# Source Extractors
# ══════════════════════════════════════════

async def extract_hacker_news(crawler: AsyncWebCrawler):
    """Hacker News — Official API (no crawling needed)"""
    top_ids = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=10).json()[:25]
    
    articles = []
    for item_id in top_ids:
        item = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json", timeout=5).json()
        if not item or "title" not in item:
            continue
        
        title = item.get("title", "").lower()
        keywords = ["ai", "ml", "open source", "llm", "model", "github", "gpt", "neural", "transformer", "agent"]
        if any(kw in title for kw in keywords):
            articles.append({
                "id": f"hn_{item_id}",
                "headline": item.get("title"),
                "summary": f"Hacker News ({item.get('score', 0)} pts, {item.get('descendants', 0)} comments)",
                "pub_date": datetime.datetime.fromtimestamp(item.get("time", 0)).isoformat(),
                "editor_name": item.get("by", "HN User"),
                "source_name": "Hacker News",
                "original_url": item.get("url", f"https://news.ycombinator.com/item?id={item_id}"),
                "tags": ["#AI", "#OpenSource"] if "open source" in title else ["#AI", "#LLM"],
                "disclaimer_text": DISCLAIMER
            })
    return articles


async def _parse_github_trending(soup, source_label, extra_tags):
    """Shared parser for GitHub trending pages with rich content synthesis."""
    articles = []
    for repo in soup.select("article.Box-row")[:12]:
        h2 = repo.select_one("h2.h3 a")
        if not h2: continue
        repo_name = h2.text.strip().replace("\n", "").replace(" ", "")
        original_url = f"https://github.com{h2['href']}"
        p = repo.select_one("p.col-9")
        summary = p.text.strip() if p else "No description available."
        
        lang_span = repo.select_one("span[itemprop='programmingLanguage']")
        lang = lang_span.text.strip() if lang_span else "N/A"
        
        # Get all stats (stars, forks, etc.)
        stats_links = repo.select("a.Link--muted")
        stars = stats_links[0].text.strip() if len(stats_links) > 0 else "0"
        forks = stats_links[1].text.strip() if len(stats_links) > 1 else "0"
        stars_today = repo.select_one("span.d-inline-block.float-sm-right")
        stars_today_text = stars_today.text.strip() if stars_today else ""

        tags = ["#GitHub", "#OpenSource"] + extra_tags
        if lang != "N/A" and lang in ["Python","TypeScript","Rust","Go","C++","Julia"]:
            tags.append(f"#{lang}")
            
        # Synthesize rich content
        full_content = f"## Repository Intelligence: {repo_name}\n\n"
        full_content += f"**{repo_name}** is currently trending in the {source_label} sector. "
        full_content += f"This repository is primarily built using **{lang}** and has garnered significant momentum with **{stars} stars** and **{forks} forks**.\n\n"
        full_content += "### Core Value Proposition\n"
        full_content += f"> {summary}\n\n"
        full_content += "### Momentum Analysis\n"
        if stars_today_text:
            full_content += f"- **Current Velocity:** {stars_today_text}\n"
        full_content += f"- **Global Reach:** {stars} developers have starred this repository.\n"
        full_content += f"- **Collaborative Depth:** {forks} independent forks have been created for development and experimentation.\n\n"
        full_content += "### Strategic Significance\n"
        full_content += "The emergence of this repository suggests a high degree of interest in its specific implementation patterns. "
        full_content += "As an open-source asset, it provides critical infrastructure or tooling that addresses current challenges in the modern tech stack.\n\n"
        full_content += "---\n"
        full_content += "*This report was automatically synthesized by Bob's Intelligence Engine based on real-time repository telemetry.*"

        articles.append({
            "id": f"gh_{uuid.uuid5(uuid.NAMESPACE_URL, original_url)}",
            "headline": f"Trending on GitHub: {repo_name}",
            "summary": summary,
            "content": full_content,
            "pub_date": datetime.datetime.now().isoformat(),
            "editor_name": repo_name.split("/")[0] if "/" in repo_name else "GitHub",
            "source_name": source_label,
            "original_url": original_url,
            "tags": tags,
            "disclaimer_text": DISCLAIMER
        })
    return articles

async def extract_github_trending(crawler: AsyncWebCrawler):
    """GitHub Trending — All languages"""
    result = await crawler.arun(url="https://github.com/trending")
    return await _parse_github_trending(BeautifulSoup(result.html, "html.parser"), "GitHub Trending", [])

async def extract_github_trending_python(crawler: AsyncWebCrawler):
    """GitHub Trending — Python (AI/ML hub)"""
    result = await crawler.arun(url="https://github.com/trending/python?since=daily")
    return await _parse_github_trending(BeautifulSoup(result.html, "html.parser"), "GitHub Python", ["#Python"])

async def extract_github_topic_llm(crawler: AsyncWebCrawler):
    """GitHub Topic — LLM repos"""
    result = await crawler.arun(url="https://github.com/topics/llm?o=desc&s=updated")
    return await _parse_github_trending(BeautifulSoup(result.html, "html.parser"), "GitHub LLM", ["#LLM"])

async def extract_github_topic_agents(crawler: AsyncWebCrawler):
    """GitHub Topic — AI Agents"""
    result = await crawler.arun(url="https://github.com/topics/ai-agents?o=desc&s=updated")
    return await _parse_github_trending(BeautifulSoup(result.html, "html.parser"), "GitHub Agents", ["#Agents"])

async def extract_github_search_ai(crawler: AsyncWebCrawler):
    """GitHub Search API — Hot new AI repos with synthesized intelligence."""
    since = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
    url = f"https://api.github.com/search/repositories?q=topic:artificial-intelligence+created:>{since}&sort=stars&order=desc&per_page=10"
    resp = requests.get(url, headers={"Accept": "application/vnd.github.v3+json"}, timeout=15)
    data = resp.json()
    articles = []
    for repo in data.get("items", [])[:10]:
        repo_name = repo["full_name"]
        lang = repo.get("language", "N/A")
        stars = repo["stargazers_count"]
        description = repo.get("description", "No description available.")

        full_content = f"## Intelligence Brief: {repo_name}\n\n"
        full_content += f"**{repo_name}** is a newly discovered repository in the artificial intelligence domain, launched within the last 7 days. "
        full_content += f"It has already gained significant traction with **{stars} stars**.\n\n"
        full_content += "### Core Value Proposition\n"
        full_content += f"> {description}\n\n"
        full_content += "### Repository Telemetry\n"
        full_content += f"- **Language:** {lang}\n"
        full_content += f"- **Discovery Date:** {repo['created_at'][:10]}\n"
        full_content += f"- **Stargazers:** {stars}\n"
        full_content += f"- **License:** {repo.get('license', {}).get('name', 'N/A') if repo.get('license') else 'N/A'}\n\n"
        full_content += "### Analyst Notes\n"
        full_content += "The rapid accumulation of stars for this new repository indicates high potential for market disruption or strong developer utility. "
        full_content += f"It is categorized under **{lang}** and represents the latest wave of open-source AI innovation.\n\n"
        full_content += "---\n"
        full_content += "*This discovery report was automatically synthesized by Bob's Intelligence Engine.*"

        articles.append({
            "id": f"ghapi_{repo['id']}",
            "headline": f"New Discovery: {repo_name}",
            "summary": description,
            "content": full_content,
            "pub_date": repo.get("pushed_at", datetime.datetime.now().isoformat()),
            "editor_name": repo["owner"]["login"],
            "source_name": "GitHub New AI",
            "original_url": repo["html_url"],
            "tags": ["#GitHub", "#AI", "#NewRepo"],
            "disclaimer_text": DISCLAIMER
        })
    return articles

async def extract_github_releases(crawler: AsyncWebCrawler):
    """Track releases from major AI open-source projects with structured changelogs."""
    watchlist = [
        "langchain-ai/langchain", "huggingface/transformers", "openai/openai-python",
        "vllm-project/vllm", "ollama/ollama", "ggml-org/llama.cpp",
        "microsoft/autogen", "crewAIInc/crewAI", "run-llama/llama_index",
        "pytorch/pytorch", "google-deepmind/gemma", "meta-llama/llama",
    ]
    articles = []
    for repo_name in watchlist:
        try:
            resp = requests.get(f"https://api.github.com/repos/{repo_name}/releases/latest",
                                headers={"Accept": "application/vnd.github.v3+json"}, timeout=8)
            if resp.status_code != 200: continue
            rel = resp.json()
            pub = rel.get("published_at", datetime.datetime.now().isoformat())
            tag = rel.get("name") or rel.get("tag_name", "Latest")
            
            # Only include releases from the last 3 days
            pub_dt = datetime.datetime.fromisoformat(pub.replace("Z", "+00:00"))
            if (datetime.datetime.now(datetime.timezone.utc) - pub_dt).days > 3: continue
            
            full_content = f"## Release Intelligence: {repo_name} {tag}\n\n"
            full_content += f"A major update has been published for **{repo_name}**. This release, tagged as **{tag}**, includes significant updates to the core repository.\n\n"
            full_content += "### Changelog Highlights\n"
            full_content += f"{rel.get('body', '')[:1200]}...\n\n"
            full_content += "### Deployment Recommendation\n"
            full_content += "Review the full changelog at the original source for breaking changes before updating your production environment.\n\n"
            full_content += "---\n"
            full_content += f"*Release tracked and synthesized by Bob's Intelligence Engine on {pub[:10]}.*"

            articles.append({
                "id": f"ghrel_{repo_name.replace('/','_')}_{rel['id']}",
                "headline": f"Release Update: {repo_name} {tag}",
                "summary": f"New release {tag} for {repo_name}",
                "content": full_content,
                "pub_date": pub,
                "editor_name": rel.get("author", {}).get("login", repo_name.split("/")[0]),
                "source_name": "GitHub Releases",
                "original_url": rel["html_url"],
                "tags": ["#GitHub", "#Release", "#OpenSource"],
                "disclaimer_text": DISCLAIMER
            })
        except Exception:
            continue
    return articles



async def extract_huggingface_papers(crawler: AsyncWebCrawler):
    """Hugging Face Daily Papers"""
    result = await crawler.arun(url="https://huggingface.co/papers")
    soup = BeautifulSoup(result.html, "html.parser")
    
    articles = []
    for paper in soup.select("article")[:8]:
        a_tag = paper.select_one("h3 a")
        if not a_tag:
            continue
        
        headline = a_tag.text.strip()
        original_url = f"https://huggingface.co{a_tag['href']}"
        p = paper.select_one("p")
        summary = p.text.strip() if p else headline
        
        articles.append({
            "id": f"hf_{uuid.uuid5(uuid.NAMESPACE_URL, original_url)}",
            "headline": headline,
            "summary": summary[:300],
            "pub_date": datetime.datetime.now().isoformat(),
            "editor_name": "Hugging Face",
            "source_name": "HF Daily Papers",
            "original_url": original_url,
            "tags": ["#AI", "#Research"],
            "disclaimer_text": DISCLAIMER
        })
    return articles


async def extract_techcrunch(crawler: AsyncWebCrawler):
    """TechCrunch AI Section"""
    result = await crawler.arun(url="https://techcrunch.com/category/artificial-intelligence/")
    soup = BeautifulSoup(result.html, "html.parser")
    
    articles = []
    for post in soup.select("div.wp-block-post")[:6]:
        a_tag = post.select_one("h2 a")
        if not a_tag:
            continue
        
        headline = a_tag.text.strip()
        original_url = a_tag['href']
        excerpt = post.select_one("div.wp-block-post-excerpt")
        summary = excerpt.text.strip() if excerpt else headline
        
        articles.append({
            "id": f"tc_{uuid.uuid5(uuid.NAMESPACE_URL, original_url)}",
            "headline": headline,
            "summary": summary[:300],
            "content": result.markdown_v2.raw_markdown if result.markdown_v2 else summary,
            "pub_date": datetime.datetime.now().isoformat(),
            "editor_name": "TechCrunch",
            "source_name": "TechCrunch AI",
            "original_url": original_url,
            "tags": ["#AI", "#Industry"],
            "disclaimer_text": DISCLAIMER
        })
    return articles


async def extract_arxiv_ai(crawler: AsyncWebCrawler):
    """ArXiv cs.AI Recent Papers"""
    result = await crawler.arun(url="https://arxiv.org/list/cs.AI/recent")
    soup = BeautifulSoup(result.html, "html.parser")
    
    articles = []
    dt_tags = soup.select("dt")[:8]
    dd_tags = soup.select("dd")[:8]
    
    for dt, dd in zip(dt_tags, dd_tags):
        a_tag = dt.select_one("a[title='Abstract']")
        if not a_tag:
            continue
        
        id_text = a_tag.text.strip().replace("arXiv:", "")
        original_url = f"https://arxiv.org/abs/{id_text}"
        title_tag = dd.select_one("div.list-title")
        headline = title_tag.text.replace("Title:", "").strip() if title_tag else "New Paper"
        summary_tag = dd.select_one("p.mathjax")
        summary = summary_tag.text.strip()[:300] if summary_tag else headline
        
        articles.append({
            "id": f"arxiv_{id_text}",
            "headline": headline,
            "summary": summary,
            "content": f"**Abstract:** {summary}\n\nFull paper: {original_url}",
            "pub_date": datetime.datetime.now().isoformat(),
            "editor_name": "ArXiv",
            "source_name": "ArXiv Research",
            "original_url": original_url,
            "tags": ["#AI", "#Research"],
            "disclaimer_text": DISCLAIMER
        })
    return articles


async def extract_verge_ai(crawler: AsyncWebCrawler):
    """The Verge — AI Coverage"""
    result = await crawler.arun(url="https://www.theverge.com/ai-artificial-intelligence")
    soup = BeautifulSoup(result.html, "html.parser")
    
    articles = []
    for a_tag in soup.select("h2 a[href*='/202']")[:6]:
        headline = a_tag.text.strip()
        href = a_tag['href']
        original_url = f"https://www.theverge.com{href}" if href.startswith('/') else href
        
        articles.append({
            "id": f"verge_{uuid.uuid5(uuid.NAMESPACE_URL, original_url)}",
            "headline": headline,
            "summary": f"The Verge AI coverage: {headline}",
            "content": result.markdown_v2.raw_markdown if result.markdown_v2 else "",
            "pub_date": datetime.datetime.now().isoformat(),
            "editor_name": "The Verge",
            "source_name": "The Verge",
            "original_url": original_url,
            "tags": ["#AI", "#TechNews"],
            "disclaimer_text": DISCLAIMER
        })
    return articles


async def extract_reddit_ml(crawler: AsyncWebCrawler):
    """Reddit r/MachineLearning — Daily Top"""
    result = await crawler.arun(url="https://old.reddit.com/r/MachineLearning/top/?t=day")
    soup = BeautifulSoup(result.html, "html.parser")
    
    articles = []
    for entry in soup.select("div.thing")[:10]:
        title_a = entry.select_one("a.title")
        if not title_a:
            continue
        
        headline = title_a.text.strip()
        original_url = title_a['href']
        if original_url.startswith('/r/'):
            original_url = f"https://reddit.com{original_url}"
            
        articles.append({
            "id": f"reddit_{uuid.uuid5(uuid.NAMESPACE_URL, original_url)}",
            "headline": headline,
            "summary": f"Top r/MachineLearning discussion",
            "pub_date": datetime.datetime.now().isoformat(),
            "editor_name": "Reddit Community",
            "source_name": "r/MachineLearning",
            "original_url": original_url,
            "tags": ["#AI", "#Community"],
            "disclaimer_text": DISCLAIMER
        })
    return articles


async def extract_aws_ml(crawler: AsyncWebCrawler):
    """AWS Machine Learning Blog"""
    result = await crawler.arun(url="https://aws.amazon.com/blogs/machine-learning/")
    soup = BeautifulSoup(result.html, "html.parser")
    
    articles = []
    for post in soup.select("article")[:5]:
        h2 = post.select_one("h2.blog-post-title a")
        if not h2:
            continue
        
        headline = h2.text.strip()
        original_url = h2['href']
        
        articles.append({
            "id": f"aws_{uuid.uuid5(uuid.NAMESPACE_URL, original_url)}",
            "headline": headline,
            "summary": f"AWS ML engineering insights",
            "content": result.markdown_v2.raw_markdown if result.markdown_v2 else "",
            "pub_date": datetime.datetime.now().isoformat(),
            "editor_name": "AWS",
            "source_name": "AWS ML Blog",
            "original_url": original_url,
            "tags": ["#AI", "#Cloud"],
            "disclaimer_text": DISCLAIMER
        })
    return articles


async def extract_mit_tech_review(crawler: AsyncWebCrawler):
    """MIT Technology Review — AI section"""
    result = await crawler.arun(url="https://www.technologyreview.com/topic/artificial-intelligence/")
    soup = BeautifulSoup(result.html, "html.parser")

    articles = []
    for a_tag in soup.select("a.teaserItem__title--32O7a, h3 a[href*='/202']")[:6]:
        headline = a_tag.text.strip()
        if not headline:
            continue
        href = a_tag.get('href', '')
        original_url = href if href.startswith('http') else f"https://www.technologyreview.com{href}"

        articles.append({
            "id": f"mit_{uuid.uuid5(uuid.NAMESPACE_URL, original_url)}",
            "headline": headline,
            "summary": f"MIT Technology Review: {headline}",
            "content": result.markdown_v2.raw_markdown if result.markdown_v2 else "",
            "pub_date": datetime.datetime.now().isoformat(),
            "editor_name": "MIT Tech Review",
            "source_name": "MIT Tech Review",
            "original_url": original_url,
            "tags": ["#AI", "#Research"],
            "disclaimer_text": DISCLAIMER
        })
    return articles


async def extract_ars_technica(crawler: AsyncWebCrawler):
    """Ars Technica — AI section"""
    result = await crawler.arun(url="https://arstechnica.com/ai/")
    soup = BeautifulSoup(result.html, "html.parser")

    articles = []
    for a_tag in soup.select("h2 a[href*='/202']")[:6]:
        headline = a_tag.text.strip()
        if not headline:
            continue
        original_url = a_tag['href']
        if not original_url.startswith('http'):
            original_url = f"https://arstechnica.com{original_url}"

        articles.append({
            "id": f"ars_{uuid.uuid5(uuid.NAMESPACE_URL, original_url)}",
            "headline": headline,
            "summary": f"Ars Technica AI: {headline}",
            "content": result.markdown_v2.raw_markdown if result.markdown_v2 else "",
            "pub_date": datetime.datetime.now().isoformat(),
            "editor_name": "Ars Technica",
            "source_name": "Ars Technica",
            "original_url": original_url,
            "tags": ["#AI", "#TechNews"],
            "disclaimer_text": DISCLAIMER
        })
    return articles


async def extract_google_ai_blog(crawler: AsyncWebCrawler):
    """Google AI Blog"""
    result = await crawler.arun(url="https://blog.google/technology/ai/")
    soup = BeautifulSoup(result.html, "html.parser")

    articles = []
    for card in soup.select("a[href*='/technology/ai/']")[:6]:
        h3 = card.select_one("h3, h2")
        if not h3:
            continue
        headline = h3.text.strip()
        href = card.get('href', '')
        original_url = href if href.startswith('http') else f"https://blog.google{href}"

        articles.append({
            "id": f"gai_{uuid.uuid5(uuid.NAMESPACE_URL, original_url)}",
            "headline": headline,
            "summary": f"Google AI: {headline}",
            "content": result.markdown_v2.raw_markdown if result.markdown_v2 else "",
            "pub_date": datetime.datetime.now().isoformat(),
            "editor_name": "Google AI",
            "source_name": "Google AI Blog",
            "original_url": original_url,
            "tags": ["#AI", "#Industry"],
            "disclaimer_text": DISCLAIMER
        })
    return articles


async def extract_openai_blog(crawler: AsyncWebCrawler):
    """OpenAI Blog"""
    result = await crawler.arun(url="https://openai.com/blog")
    soup = BeautifulSoup(result.html, "html.parser")

    articles = []
    for a_tag in soup.select("a[href*='/index/']")[:6]:
        headline_el = a_tag.select_one("h3, h2, span")
        if not headline_el:
            continue
        headline = headline_el.text.strip()
        if not headline or len(headline) < 10:
            continue
        href = a_tag.get('href', '')
        original_url = href if href.startswith('http') else f"https://openai.com{href}"

        articles.append({
            "id": f"oai_{uuid.uuid5(uuid.NAMESPACE_URL, original_url)}",
            "headline": headline,
            "summary": f"OpenAI: {headline}",
            "content": result.markdown_v2.raw_markdown if result.markdown_v2 else "",
            "pub_date": datetime.datetime.now().isoformat(),
            "editor_name": "OpenAI",
            "source_name": "OpenAI Blog",
            "original_url": original_url,
            "tags": ["#AI", "#Industry"],
            "disclaimer_text": DISCLAIMER
        })
    return articles


async def extract_wired_ai(crawler: AsyncWebCrawler):
    """Wired — AI section"""
    result = await crawler.arun(url="https://www.wired.com/tag/artificial-intelligence/")
    soup = BeautifulSoup(result.html, "html.parser")

    articles = []
    for a_tag in soup.select("a[href*='/story/']")[:6]:
        headline_el = a_tag.select_one("h2, h3")
        if not headline_el:
            continue
        headline = headline_el.text.strip()
        href = a_tag.get('href', '')
        original_url = href if href.startswith('http') else f"https://www.wired.com{href}"

        articles.append({
            "id": f"wrd_{uuid.uuid5(uuid.NAMESPACE_URL, original_url)}",
            "headline": headline,
            "summary": f"Wired: {headline}",
            "content": result.markdown_v2.raw_markdown if result.markdown_v2 else "",
            "pub_date": datetime.datetime.now().isoformat(),
            "editor_name": "Wired",
            "source_name": "Wired",
            "original_url": original_url,
            "tags": ["#AI", "#TechNews"],
            "disclaimer_text": DISCLAIMER
        })
    return articles


async def extract_lobsters(crawler: AsyncWebCrawler):
    """Lobsters — Tech community"""
    result = await crawler.arun(url="https://lobste.rs/")
    soup = BeautifulSoup(result.html, "html.parser")

    articles = []
    for story in soup.select("div.story")[:12]:
        a_tag = story.select_one("a.u-url")
        if not a_tag:
            continue
        headline = a_tag.text.strip()
        original_url = a_tag['href']
        if original_url.startswith('/'):
            original_url = f"https://lobste.rs{original_url}"

        tag_els = story.select("a.tag")
        tags = [f"#{t.text.strip()}" for t in tag_els[:2]] if tag_els else ["#Tech"]

        articles.append({
            "id": f"lob_{uuid.uuid5(uuid.NAMESPACE_URL, original_url)}",
            "headline": headline,
            "summary": f"Lobsters discussion: {headline}",
            "pub_date": datetime.datetime.now().isoformat(),
            "editor_name": "Lobsters",
            "source_name": "Lobsters",
            "original_url": original_url,
            "tags": tags,
            "disclaimer_text": DISCLAIMER
        })
    return articles


async def extract_producthunt(crawler: AsyncWebCrawler):
    """Product Hunt — Top tech products"""
    result = await crawler.arun(url="https://www.producthunt.com/")
    soup = BeautifulSoup(result.html, "html.parser")

    articles = []
    for item in soup.select("a[href*='/posts/']")[:8]:
        headline_el = item.select_one("h3, strong")
        if not headline_el:
            continue
        headline = headline_el.text.strip()
        if not headline or len(headline) < 5:
            continue
        href = item.get('href', '')
        original_url = href if href.startswith('http') else f"https://www.producthunt.com{href}"

        articles.append({
            "id": f"ph_{uuid.uuid5(uuid.NAMESPACE_URL, original_url)}",
            "headline": headline,
            "summary": f"Product Hunt: {headline}",
            "pub_date": datetime.datetime.now().isoformat(),
            "editor_name": "Product Hunt",
            "source_name": "Product Hunt",
            "original_url": original_url,
            "tags": ["#Product", "#Startup"],
            "disclaimer_text": DISCLAIMER
        })
    return articles


# ══════════════════════════════════════════
# Source Registry
# ══════════════════════════════════════════
SOURCE_REGISTRY = [
    # Core Intelligence
    ("Hacker News",      extract_hacker_news),
    ("HF Daily Papers",  extract_huggingface_papers),
    ("ArXiv Research",   extract_arxiv_ai),
    # GitHub Ecosystem
    ("GitHub Trending",  extract_github_trending),
    ("GitHub Python",    extract_github_trending_python),
    ("GitHub LLM",       extract_github_topic_llm),
    ("GitHub Agents",    extract_github_topic_agents),
    ("GitHub New AI",    extract_github_search_ai),
    ("GitHub Releases",  extract_github_releases),
    # Industry
    ("TechCrunch AI",    extract_techcrunch),
    ("The Verge",        extract_verge_ai),
    ("Ars Technica",     extract_ars_technica),
    ("Wired",            extract_wired_ai),
    ("MIT Tech Review",  extract_mit_tech_review),
    # Labs
    ("Google AI Blog",   extract_google_ai_blog),
    ("OpenAI Blog",      extract_openai_blog),
    ("AWS ML Blog",      extract_aws_ml),
    # Community
    ("r/MachineLearning",extract_reddit_ml),
    ("Lobsters",         extract_lobsters),
    ("Product Hunt",     extract_producthunt),
]


# ══════════════════════════════════════════
# Orchestrator
# ══════════════════════════════════════════

async def run_extraction(crawler: AsyncWebCrawler, metrics: CycleMetrics):
    """Run all extractors with per-source error isolation."""
    all_articles = []

    for source_name, extractor in SOURCE_REGISTRY:
        try:
            log("INFO", source_name, "Extracting...")
            result = await asyncio.wait_for(extractor(crawler), timeout=60)
            count = len(result)
            all_articles.extend(result)
            metrics.record(source_name, count)
            log("OK", source_name, f"Extracted {count} articles")
        except asyncio.TimeoutError:
            metrics.record_error(source_name, "Timeout (60s)")
            log("ERR", source_name, "Timed out after 60s — skipping")
        except Exception as e:
            error_msg = str(e)[:80]
            metrics.record_error(source_name, error_msg)
            log("ERR", source_name, f"Failed: {error_msg}")

    return all_articles


async def ingest_articles(articles: list):
    """Push articles to the Next.js ingestion API."""
    if not articles:
        log("WARN", "INGEST", "No articles to send")
        return

    try:
        response = requests.post(
            INGEST_URL,
            json=articles,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            log("OK", "INGEST", f"Pushed {data.get('ingested', len(articles))} articles → API")
        else:
            log("ERR", "INGEST", f"API returned {response.status_code}: {response.text[:100]}")
    except Exception as e:
        log("ERR", "INGEST", f"Connection failed: {str(e)[:80]}")


async def main():
    """Single crawl cycle."""
    metrics = CycleMetrics()
    log_header(f"CRAWL CYCLE — {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    async with AsyncWebCrawler() as crawler:
        articles = await run_extraction(crawler, metrics)
        await ingest_articles(articles)

    metrics.print_report()


async def run_daemon():
    """Continuous daemon loop with configurable interval."""
    log_header("BOB INTELLIGENCE CRAWLER — DAEMON MODE")
    log("SYS", "DAEMON", f"Ingestion endpoint: {INGEST_URL}")
    log("SYS", "DAEMON", f"Crawl interval: {CRAWL_INTERVAL}s ({CRAWL_INTERVAL // 60}m)")
    log("SYS", "DAEMON", f"Registered sources: {len(SOURCE_REGISTRY)}")

    cycle = 0
    while True:
        cycle += 1
        try:
            log("SYS", "DAEMON", f"Starting cycle #{cycle}")
            await main()
            log("SYS", "DAEMON", f"Sleeping {CRAWL_INTERVAL // 60}m until next cycle...")
            await asyncio.sleep(CRAWL_INTERVAL)
        except asyncio.CancelledError:
            log("SYS", "DAEMON", "Shutdown signal received")
            break
        except Exception as e:
            log("ERR", "DAEMON", f"Unhandled error: {e}")
            log("SYS", "DAEMON", "Retrying in 60s...")
            await asyncio.sleep(60)

    log_header("CRAWLER STOPPED")


# SaaS API Layer
import threading
from flask import Flask, jsonify
import time

# --- SaaS API Configuration ---
app = Flask(__name__)
crawl_lock = threading.Lock()
engine_status = {
    "last_run": None,
    "is_running": False,
    "total_articles_synced": 0,
    "last_error": None
}

@app.route("/")
def home():
    return jsonify({
        "service": "Bob Intelligence Engine",
        "status": "online",
        "endpoints": {
            "GET /": "Service info",
            "GET /status": "Current engine metrics",
            "POST /crawl": "Trigger manual intelligence synthesis"
        }
    })

@app.route("/status")
def status():
    return jsonify({
        "engine": "Bob Intelligence",
        "state": engine_status,
        "config": {
            "interval_seconds": CRAWL_INTERVAL,
            "ingest_target": INGEST_URL
        }
    })

@app.route("/crawl", methods=["POST"])
def trigger_crawl():
    if crawl_lock.locked():
        return jsonify({"error": "Crawler is already in progress"}), 429
    
    # Run in background thread to avoid timeout
    threading.Thread(target=manual_crawl_task).start()
    return jsonify({"message": "Intelligence synthesis started in background"}), 202

def manual_crawl_task():
    with crawl_lock:
        global engine_status
        engine_status["is_running"] = True
        try:
            log_header("REMOTE TRIGGER RECEIVED — STARTING SYNTHESIS")
            # Run the async main loop in the thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            stats = loop.run_until_complete(main())
            loop.close()
            
            engine_status["last_run"] = datetime.datetime.now().isoformat()
            engine_status["total_articles_synced"] += stats if stats else 0
            engine_status["last_error"] = None
        except Exception as e:
            log("ERROR", "API", f"Crawl failed: {e}")
            engine_status["last_error"] = str(e)
        finally:
            engine_status["is_running"] = False

def run_periodic_daemon():
    """Maintain the background loop for autonomous updates."""
    log("SYS", "DAEMON", f"Autonomous mode active. Interval: {CRAWL_INTERVAL}s")
    while True:
        if not crawl_lock.locked():
            manual_crawl_task()
        time.sleep(CRAWL_INTERVAL)

if __name__ == "__main__":
    # Environment Check
    single_pass = os.getenv("SINGLE_PASS", "false").lower() == "true"
    
    # Pre-crawl Health Check for Ingestion Target
    if INGEST_URL.startswith("http"):
        root_url = "/".join(INGEST_URL.split("/")[:3])
        try:
            requests.get(root_url, timeout=10)
            log("OK", "SYS", "Ingestion target verified")
        except:
            log("WARN", "SYS", "Ingestion target unreachable")

    if single_pass:
        log_header("BOB INTELLIGENCE — CI/CD SINGLE PASS")
        asyncio.run(main())
    else:
        # Start the autonomous daemon in a background thread
        threading.Thread(target=run_periodic_daemon, daemon=True).start()
        
        # Start the Web API
        port = int(os.getenv("PORT", "8080"))
        log_header(f"BOB INTELLIGENCE API ACTIVE ON PORT {port}")
        app.run(host="0.0.0.0", port=port)
