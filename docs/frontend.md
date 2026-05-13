# Frontend Technical Documentation

## Overview
The frontend is a modern, high-performance web application built with **Next.js 14** using the **App Router**. It serves as a news portal for AI and Open Source enthusiasts.

## Tech Stack
- **Framework**: Next.js 14 (React 18)
- **Styling**: Vanilla CSS with CSS Modules and CSS Variables for theming.
- **Icons**: Lucide React
- **Theming**: Dark/Light mode support via `prefers-color-scheme` and CSS variables in `globals.css`.

## Directory Structure
- `app/`: Contains the application routes and layouts.
  - `layout.tsx`: The root layout defining the global structure (header, footer, fonts).
  - `page.tsx`: The main landing page with the masonry news grid.
  - `article/[id]/`: Dynamic route for individual article pages.
  - `disclaimer/`: Static page for full legal terms.
  - `globals.css`: Global styles, CSS variables, and utility classes.
- `components/`: (To be added as the project scales) Reusable UI components.

## Key Features
### Masonry Grid
The homepage uses a responsive CSS grid layout that adjusts columns based on screen size (`repeat(auto-fill, minmax(300px, 1fr))`).

### Glassmorphism UI
A custom `.glass-panel` utility class provides a modern, semi-transparent look with backdrop filtering, enhancing the "premium" feel.

### SEO & Performance
- Uses Next.js Metadata API for page-specific titles and descriptions.
- Server-side rendering (SSR) for fast initial page loads and better search engine indexing.

## Customization
To change the theme colors, modify the variables in `app/globals.css`:
```css
:root {
  --background: #ffffff;
  --foreground: #09090b;
  /* ... other variables */
}
```
