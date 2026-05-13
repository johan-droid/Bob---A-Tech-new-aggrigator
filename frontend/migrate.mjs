import { neon } from '@neondatabase/serverless';
import dotenv from 'dotenv';
dotenv.config({ path: '.env.local' });

async function migrate() {
  const sql = neon(process.env.DATABASE_URL);
  
  console.log("Checking for 'content' column in 'articles' table...");
  try {
    await sql`ALTER TABLE articles ADD COLUMN IF NOT EXISTS content TEXT;`;
    await sql`ALTER TABLE articles ADD COLUMN IF NOT EXISTS disclaimer_text TEXT;`;
    console.log("Migration successful: 'content' and 'disclaimer_text' columns ensured.");
  } catch (error) {
    console.error("Migration failed:", error);
    process.exit(1);
  }
}

migrate();
