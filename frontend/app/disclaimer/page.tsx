export default function DisclaimerPage() {
  return (
    <div style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }} className="glass-panel">
      <h1 style={{ fontSize: '2.5rem', fontWeight: 'bold', marginBottom: '1.5rem' }}>Legal Disclaimer</h1>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', color: 'var(--muted-foreground)' }}>
        <p>
          This website (Tech News Aggregator) operates as an automated news aggregation platform designed for informational purposes only. We exclusively crawl and index public content from open-source ecosystems, AI research, and related tech domains.
        </p>
        <p>
          <strong>Content Ownership:</strong> All rights, copyrights, and intellectual property associated with the articles and content linked on this platform belong entirely to their original publishers, authors, and editors. We do not claim any ownership over the content.
        </p>
        <p>
          <strong>No Modification:</strong> We do not modify the meaning, intent, or substance of any article. Our automated systems merely extract headlines, brief summaries, and metadata to provide an index for our users.
        </p>
        <p>
          <strong>Proper Attribution:</strong> We make every automated effort to accurately credit the original editor, author, and source publication. If an explicit author is not found, we attribute the content to the source's Editorial Team.
        </p>
        <p>
          <strong>Takedown Requests:</strong> If you are a copyright holder, publisher, or editor and wish for your content to be removed from our index, please contact us. We will promptly comply with all verified takedown requests.
        </p>
      </div>
    </div>
  );
}
