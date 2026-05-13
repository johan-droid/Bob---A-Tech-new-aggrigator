'use client';

import { useEffect, useState, useRef } from 'react';

// ─── Animated Counter ───
export function AnimatedCounter({ value, label }: { value: number; label: string }) {
  const [count, setCount] = useState(0);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const target = value;
    if (target === 0) return;

    let start = 0;
    const duration = 1200;
    const startTime = performance.now();

    function animate(now: number) {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setCount(Math.floor(eased * target));
      if (progress < 1) requestAnimationFrame(animate);
    }

    requestAnimationFrame(animate);
  }, [value]);

  return (
    <div className="stat" ref={ref}>
      <span className="stat-value">{count.toLocaleString()}</span>
      <span className="stat-label">{label}</span>
    </div>
  );
}

// ─── Live Clock ───
export function LiveClock() {
  const [time, setTime] = useState('');

  useEffect(() => {
    const update = () => {
      setTime(new Date().toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', second: '2-digit', hour12: true }));
    };
    update();
    const id = setInterval(update, 1000);
    return () => clearInterval(id);
  }, []);

  return <span className="live-clock">{time || '--:--'}</span>;
}

// ─── Source Filter Tabs ───
export function SourceFilter({ 
  sources, 
  activeSource, 
  onSelect 
}: { 
  sources: string[]; 
  activeSource: string; 
  onSelect: (s: string) => void;
}) {
  return (
    <div className="source-tabs">
      <button
        className={`source-tab ${activeSource === 'all' ? 'active' : ''}`}
        onClick={() => onSelect('all')}
      >
        All Sources
      </button>
      {sources.map(s => (
        <button
          key={s}
          className={`source-tab ${activeSource === s ? 'active' : ''}`}
          onClick={() => onSelect(s)}
        >
          {s}
        </button>
      ))}
    </div>
  );
}

// ─── Search Bar ───
export function SearchBar({ onSearch }: { onSearch: (q: string) => void }) {
  const [query, setQuery] = useState('');

  useEffect(() => {
    const timeout = setTimeout(() => onSearch(query), 200);
    return () => clearTimeout(timeout);
  }, [query, onSearch]);

  return (
    <div className="search-box">
      <svg className="search-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="11" cy="11" r="8" />
        <path d="m21 21-4.35-4.35" />
      </svg>
      <input
        type="text"
        placeholder="Search signals..."
        value={query}
        onChange={e => setQuery(e.target.value)}
        className="search-input"
      />
      {query && (
        <button className="search-clear" onClick={() => setQuery('')}>✕</button>
      )}
    </div>
  );
}

// ─── Interactive Feed (combines search + filter + cards) ───
export function InteractiveFeed({ articles }: { articles: any[] }) {
  const [search, setSearch] = useState('');
  const [activeSource, setActiveSource] = useState('all');

  // All unique sources
  const sources = [...new Set(articles.map(a => a.source_name))];

  // Filter articles
  const filtered = articles.filter(article => {
    const matchesSearch = search === '' || 
      article.headline.toLowerCase().includes(search.toLowerCase()) ||
      article.source_name.toLowerCase().includes(search.toLowerCase());
    const matchesSource = activeSource === 'all' || article.source_name === activeSource;
    return matchesSearch && matchesSource;
  });

  // Group by tag
  const sections: Record<string, any[]> = {};
  filtered.forEach(article => {
    const tag = article.tags?.[0] || '#General';
    if (!sections[tag]) sections[tag] = [];
    sections[tag].push(article);
  });

  return (
    <>
      <div className="feed-controls">
        <SearchBar onSearch={setSearch} />
        <SourceFilter sources={sources} activeSource={activeSource} onSelect={setActiveSource} />
      </div>

      {filtered.length === 0 ? (
        <div className="empty-state">
          <h3>No Matches</h3>
          <p>Try adjusting your search or filter.</p>
        </div>
      ) : (
        Object.entries(sections).map(([tag, items]) => (
          <section key={tag} className="section">
            <div className="section-header">
              <span className="section-tag">{tag}</span>
              <div className="section-line" />
              <span className="section-count">{items.length} signal{items.length !== 1 ? 's' : ''}</span>
            </div>
            <div className="card-grid">
              {items.map((article, idx) => (
                <a
                  href={`/article/${article.id}`}
                  key={article.id}
                  className="card"
                  style={{ animationDelay: `${idx * 60}ms` }}
                >
                  <span className="card-source">{article.source_name}</span>
                  <h3 className="card-title">{article.headline}</h3>
                  <div className="card-footer">
                    <span>{article.editor_name || 'Editorial'}</span>
                    <time>{new Date(article.pub_date).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })}</time>
                  </div>
                </a>
              ))}
            </div>
          </section>
        ))
      )}

      <div className="feed-status">
        Showing {filtered.length} of {articles.length} signals
        {activeSource !== 'all' && <> from <strong>{activeSource}</strong></>}
      </div>
    </>
  );
}

// ─── Scroll to Top ───
export function ScrollToTop() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const onScroll = () => setVisible(window.scrollY > 400);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  if (!visible) return null;

  return (
    <button
      className="scroll-top"
      onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
      aria-label="Scroll to top"
    >
      ↑
    </button>
  );
}
