import { pgTable, text, timestamp, varchar, index, customType } from 'drizzle-orm/pg-core';
import { sql } from 'drizzle-orm';

// Custom type for tsvector search
const tsvector = customType<{ data: string }>({
  dataType() {
    return 'tsvector';
  },
});

export const articles = pgTable('articles', {
  id: varchar('id', { length: 255 }).primaryKey(),
  headline: text('headline').notNull(),
  summary: text('summary').notNull(),
  pub_date: timestamp('pub_date').notNull(),
  editor_name: varchar('editor_name', { length: 255 }).notNull(),
  source_name: varchar('source_name', { length: 255 }).notNull(),
  original_url: text('original_url').notNull(),
  tags: text('tags').array().notNull(),
  content: text('content'),
  search_vector: tsvector('search_vector'),
  created_at: timestamp('created_at').defaultNow().notNull(),
}, (table) => {
  return {
    searchIdx: index('search_idx').on(table.search_vector),
    dateIdx: index('date_idx').on(table.pub_date),
  };
});


