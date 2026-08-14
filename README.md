# celld-operator.io

The static website for [celld-operator](https://github.com/ezgamehost/celld-operator) —
landing page and documentation, served at https://celld-operator.io.

No framework, no build step required to serve: every page is plain HTML with one shared
stylesheet (`assets/style.css`) and zero JavaScript dependencies. Deploy by pointing any
static host at the repository root (GitHub Pages, Cloudflare Pages, Netlify, an S3
bucket). The `CNAME` file is for GitHub Pages custom-domain setup.

## Layout

| Path | What it is |
| --- | --- |
| `index.html` | Landing page (hand-edited) |
| `docs/**/index.html` | Documentation pages — **generated**, do not edit directly |
| `build/content/*.html` | The source fragments for the docs pages |
| `build/build.py` | Assembles docs pages, `sitemap.xml`, and `404.html` from the fragments |
| `assets/style.css` | The single shared stylesheet (hand-edited) |
| `assets/og.png` | Social-preview image (rendered from an SVG; see below) |

## Editing docs

Edit the fragment in `build/content/<page>.html`, then regenerate:

```sh
python3 build/build.py
```

To add a page, add a fragment file and register it in the `PAGES` list at the top of
`build/build.py` (slug, sidebar group, nav title, `<title>`, meta description). The
sidebar, prev/next pager, breadcrumbs, JSON-LD, and sitemap update automatically.
Bump `LASTMOD` in `build.py` when publishing.

## Preview locally

```sh
python3 -m http.server 8080
# http://localhost:8080
```

## SEO checklist (already wired in)

- Unique `<title>` and meta description per page; canonical URLs (directory-style, e.g.
  `/docs/quick-start/`).
- Open Graph + Twitter cards with `assets/og.png`; JSON-LD (`SoftwareApplication` on the
  landing page, `TechArticle` + `BreadcrumbList` on docs pages).
- `sitemap.xml` + `robots.txt`; `404.html` is `noindex`.
- Light/dark theme via `prefers-color-scheme`; responsive with no horizontal overflow.

## License and trademarks

Site content is © the celld-operator authors, under the repository's Apache-2.0 license.
celld is a project of Deno Land Inc. Cloudflare, Cloudflare Workers, and Durable Objects
are trademarks of Cloudflare, Inc. This site describes compatibility and is not
affiliated with, sponsored by, or endorsed by Deno Land or Cloudflare.
