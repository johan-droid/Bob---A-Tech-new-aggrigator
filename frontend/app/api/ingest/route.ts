import { NextResponse } from 'next/server';
import { db } from '@/db';
import { articles } from '@/db/schema';

export async function POST(req: Request) {
  try {
    const body = await req.json();

    // Ensure it's an array of articles
    const newArticles = Array.isArray(body) ? body : [body];

    if (newArticles.length === 0) {
      return NextResponse.json({ success: true, message: 'No articles to ingest' });
    }

    // Insert articles to database
    // Ignore duplicates on ID
    for (const article of newArticles) {
      await db.insert(articles).values({
        id: article.id,
        headline: article.headline,
        summary: article.summary,
        pub_date: new Date(article.pub_date),
        editor_name: article.editor_name || 'Editorial Team',
        source_name: article.source_name,
        original_url: article.original_url,
        tags: article.tags || [],
        content: article.content || null,
      }).onConflictDoNothing();
    }

    return NextResponse.json({ success: true, ingested: newArticles.length });
  } catch (error) {
    console.error('Ingestion error:', error);
    return NextResponse.json({ success: false, error: 'Internal Server Error' }, { status: 500 });
  }
}
