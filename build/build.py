#!/usr/bin/env python3
"""Assemble the static docs pages for celld-operator.io from content fragments."""
import html
import json
import pathlib
import re

SRC = pathlib.Path(__file__).parent / "content"
OUT = pathlib.Path(__file__).parent.parent
BASE = "https://celld-operator.io"
LASTMOD = "2026-10-18"
REPO = "https://github.com/ezgamehost/celld-operator.io"

# slug ("" = /docs/), group, nav title, <title> (without site suffix), meta description
PAGES = [
    ("", "Getting started", "Introduction",
     "Introduction to celld-operator",
     "What celld-operator is: a Kubernetes operator that turns celld into a self-hosted Cloudflare Workers and Durable Objects platform. Concepts, scope, and project status."),
    ("install", "Getting started", "Installation",
     "Install celld-operator on Kubernetes",
     "Install the celld-operator with Helm or kustomize: prerequisites, trust allowlists, optional integrations (Gateway API, Istio, KEDA), and verification."),
    ("quick-start", "Getting started", "Quick start",
     "Quick start: your first WorkerApp",
     "Deploy a Wrangler project to your bucket with celld deploy, allowlist its endpoint and identity, create a WorkerApp, and watch the operator converge a celld fleet."),
    ("architecture", "Concepts", "Architecture",
     "celld-operator architecture",
     "How celld-operator works: fleet-per-app tenancy, the resources reconciled per WorkerApp, the celld behaviors the design depends on, and the trust boundaries."),
    ("object-stores", "Concepts", "Object stores",
     "Object store requirements",
     "celld requires atomically enforced conditional writes, exact ranged reads, and read-after-write consistency. Qualified stores, S3/GCS/Azure dialects, and how to qualify your own."),
    ("compatibility", "Concepts", "Cloudflare compatibility",
     "Cloudflare Workers compatibility matrix",
     "Which Cloudflare Workers platform services and runtime APIs run on celld v0.6.2, the documented differences, and the Wrangler configuration celld deploy accepts."),
    ("deploying", "Guides", "Deploying updates",
     "Deploying updates and rollouts",
     "How deploys work on celld-operator: in-place adoption, appVersion tracking, deployment policies, the gated rollout controller, and celld version upgrades."),
    ("autoscaling", "Guides", "Autoscaling",
     "Autoscaling celld fleets with KEDA",
     "Scale celld fleets on resident-cell utilization, not CPU: the operator's /state-derived Prometheus metrics, KEDA ScaledObjects, freshness gates, and celld-aware policy."),
    ("networking", "Guides", "Networking &amp; ingress",
     "Networking, ingress, and WebSockets",
     "Route WorkerApp hostnames via Gateway API, Istio, or Ingress; keep the internal listener private; retries, readiness, forwarded headers, and WebSockets."),
    ("security", "Guides", "Security",
     "Security model and tenancy",
     "celld-operator's isolation story: fleet-per-app blast radius, operator allowlists, prefix-scoped bucket credentials, pod hardening, and the internal listener."),
    ("observability", "Guides", "Observability",
     "Observability: telemetry and metrics",
     "Per-tenant traces and logs as Parquet in your own bucket or OTLP to a collector, plus the operator's Prometheus metrics for fleet capacity, freshness, and self-fencing."),
    ("workerapp", "Reference", "WorkerApp reference",
     "WorkerApp API reference (v1alpha1)",
     "Complete reference for the WorkerApp custom resource: every spec field with defaults and validation, status phases, observed deployments, rollout state, and conditions."),
    ("operator-configuration", "Reference", "Operator configuration",
     "Operator configuration reference",
     "Every celld-operator flag and Helm value: trust allowlists, namespace scoping, ingress modes, gateway wiring, poll intervals, metrics TLS, and graceful degradation."),
]


LOGO = '<svg width="24" height="24" viewBox="0 0 32 32" aria-hidden="true"><rect width="32" height="32" rx="8" fill="#07090e"/><polygon points="16 4.5 25.5 10 25.5 21 16 26.5 6.5 21 6.5 10" fill="none" stroke="#22d3ee" stroke-width="2.4" stroke-linejoin="round"/><circle cx="16" cy="15.5" r="3.4" fill="#22d3ee"/></svg>'
GH_ICON = '<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27s1.36.09 2 .27c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8z"/></svg>'
EDIT_ICON = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4z"/></svg>'

# Shared <head> lines for every page (index.html carries a copy of these).
HEAD_COMMON = '''<meta name="theme-color" content="#07090e">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&amp;family=Geist+Mono:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="/assets/style.css">'''


def header(section: str = "") -> str:
    def nav(href: str, label: str, key: str) -> str:
        current = ' aria-current="page"' if key == section else ""
        return f'<a href="{href}"{current}>{label}</a>'
    return f'''<header class="site-head">
  <div class="container">
    <a class="brand" href="/">
      {LOGO}
      celld-operator
    </a>
    <nav class="site-nav" aria-label="Main">
      {nav("/docs/", "Docs", "docs")}
      {nav("/docs/workerapp/", "Reference", "reference")}
      {nav("/docs/compatibility/", "Compatibility", "compatibility")}
      <a href="https://celld.dev" rel="external">celld</a>
    </nav>
    <div class="head-actions">
      <a class="gh" href="https://github.com/ezgamehost/celld-operator" rel="external">{GH_ICON}<span>GitHub</span></a>
      <a class="btn btn-primary btn-sm" href="/docs/quick-start/">Get started</a>
    </div>
  </div>
</header>'''


FOOTER = '''<footer class="site-foot">
  <div class="container">
    <div class="cols">
      <div>
        <a class="brand" href="/">''' + LOGO + '''
          celld-operator
        </a>
        <p class="blurb">
          A Kubernetes control plane for celld: self-hosted Cloudflare Workers and
          Durable Objects on infrastructure you own.
        </p>
      </div>
      <div>
        <h4>Documentation</h4>
        <ul>
          <li><a href="/docs/">Introduction</a></li>
          <li><a href="/docs/quick-start/">Quick start</a></li>
          <li><a href="/docs/workerapp/">WorkerApp reference</a></li>
          <li><a href="/docs/compatibility/">Cloudflare compatibility</a></li>
        </ul>
      </div>
      <div>
        <h4>Project</h4>
        <ul>
          <li><a href="https://github.com/ezgamehost/celld-operator" rel="external">GitHub</a></li>
          <li><a href="https://github.com/ezgamehost/celld-operator/blob/main/docs/production.md" rel="external">Production guide</a></li>
          <li><a href="https://github.com/ezgamehost/celld-operator/blob/main/docs/celld-behaviors.md" rel="external">celld behaviors index</a></li>
          <li><a href="https://github.com/ezgamehost/celld-operator/blob/main/SECURITY.md" rel="external">Security policy</a></li>
        </ul>
      </div>
      <div>
        <h4>Upstream</h4>
        <ul>
          <li><a href="https://celld.dev" rel="external">celld.dev</a></li>
          <li><a href="https://github.com/denoland/celld" rel="external">denoland/celld</a></li>
          <li><a href="https://github.com/denoland/celld/blob/v0.6.2/docs/README.md" rel="external">celld v0.6.2 docs</a></li>
        </ul>
      </div>
    </div>
    <p class="legal">
      celld-operator is an independent open-source project released under the
      Apache License 2.0. celld is a project of Deno Land Inc. Cloudflare, Cloudflare
      Workers, and Durable Objects are trademarks of Cloudflare, Inc. This project is
      not affiliated with, sponsored by, or endorsed by Deno Land or Cloudflare.
    </p>
  </div>
</footer>'''


def url_for(slug: str) -> str:
    return f"{BASE}/docs/" if slug == "" else f"{BASE}/docs/{slug}/"


def href_for(slug: str) -> str:
    return "/docs/" if slug == "" else f"/docs/{slug}/"


def sidebar(active_slug: str) -> str:
    groups: dict[str, list] = {}
    for slug, group, nav_title, *_ in PAGES:
        groups.setdefault(group, []).append((slug, nav_title))
    parts = ['<nav class="docs-nav" aria-label="Documentation">',
             '<details open>', '<summary>Documentation menu</summary>',
             '<div class="docs-nav-inner">']
    for group, items in groups.items():
        parts.append(f"<h4>{group}</h4>")
        parts.append("<ul>")
        for slug, nav_title in items:
            current = ' aria-current="page"' if slug == active_slug else ""
            parts.append(f'<li><a href="{href_for(slug)}"{current}>{nav_title}</a></li>')
        parts.append("</ul>")
    parts += ["</div>", "</details>",
              '<script>if(matchMedia("(max-width: 56rem)").matches)'
              'document.currentScript.parentElement.querySelector("details").removeAttribute("open")</script>',
              "</nav>"]
    return "\n".join(parts)


H2 = re.compile(r'<h2 id="([^"]+)"><a class="anchor" href="#\1">(.*?)</a></h2>')


def toc(body: str, edit_url: str) -> str:
    """'On this page' rail, built from the fragment's <h2> anchors."""
    items = "\n".join(f'<li><a href="#{anchor}">{title}</a></li>' for anchor, title in H2.findall(body))
    return f'''<aside class="toc" aria-label="On this page">
<div class="toc-inner">
<h4>On this page</h4>
<ul>
{items}
</ul>
<div class="toc-meta"><a href="{edit_url}" rel="external">{EDIT_ICON}Edit this page</a></div>
</div>
</aside>'''


def pager(idx: int) -> str:
    prev_html = next_html = ""
    if idx > 0:
        slug, _, nav_title, *_ = PAGES[idx - 1]
        prev_html = (f'<a class="prev" href="{href_for(slug)}" rel="prev">'
                     f'<span class="dir">&larr; Previous</span>{nav_title}</a>')
    if idx < len(PAGES) - 1:
        slug, _, nav_title, *_ = PAGES[idx + 1]
        next_html = (f'<a class="next" href="{href_for(slug)}" rel="next">'
                     f'<span class="dir">Next &rarr;</span>{nav_title}</a>')
    if not prev_html and not next_html:
        return ""
    return f'<nav class="pager" aria-label="Docs pages">{prev_html}{next_html}</nav>'


def jsonld(title: str, desc: str, url: str, nav_title: str) -> str:
    data = [
        {
            "@context": "https://schema.org",
            "@type": "TechArticle",
            "headline": title,
            "description": desc,
            "url": url,
            "dateModified": LASTMOD,
            "isPartOf": {"@type": "WebSite", "name": "celld-operator", "url": BASE + "/"},
            "about": {"@type": "SoftwareApplication", "name": "celld-operator",
                      "operatingSystem": "Kubernetes 1.30+",
                      "applicationCategory": "DeveloperApplication"},
        },
        {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Docs", "item": BASE + "/docs/"},
                {"@type": "ListItem", "position": 3, "name": html.unescape(nav_title), "item": url},
            ],
        },
    ]
    return "\n".join(
        '<script type="application/ld+json">\n' + json.dumps(d, indent=1) + "\n</script>"
        for d in data
    )


def page_html(idx: int, body: str) -> str:
    slug, group, nav_title, title, desc = PAGES[idx]
    url = url_for(slug)
    sep = '<span class="sep">/</span>'
    crumbs = f'<a href="/docs/">Docs</a>{sep}<span>{group}</span>'
    if slug:
        crumbs += f'{sep}<span>{nav_title}</span>'
    edit_url = f"{REPO}/blob/main/build/content/{slug or 'index'}.html"
    section = {"workerapp": "reference", "operator-configuration": "reference",
               "compatibility": "compatibility"}.get(slug, "docs")
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · celld-operator</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
{HEAD_COMMON}
<meta property="og:type" content="article">
<meta property="og:site_name" content="celld-operator">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{BASE}/assets/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{BASE}/assets/og.png">
{jsonld(title, desc, url, nav_title)}
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>

{header(section)}

<div class="container docs-wrap">
{sidebar(slug)}
<main class="docs-main" id="main">
<nav class="breadcrumbs" aria-label="Breadcrumb">{crumbs}</nav>
{body}
<div class="page-foot"><a href="{edit_url}" rel="external">{EDIT_ICON}Edit this page on GitHub</a><span>Updated {LASTMOD}</span></div>
{pager(idx)}
</main>
{toc(body, edit_url)}
</div>

{FOOTER}

</body>
</html>
'''


def build() -> None:
    written = []
    for idx, (slug, *_rest) in enumerate(PAGES):
        frag = SRC / (f"{slug or 'index'}.html")
        body = frag.read_text()
        out = OUT / "docs" / (slug if slug else "") / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page_html(idx, body))
        written.append(str(out.relative_to(OUT)))

    # sitemap
    urls = [(BASE + "/", "1.0")] + [(url_for(slug), "0.8" if slug in ("", "quick-start", "workerapp", "compatibility") else "0.7")
                                     for slug, *_ in PAGES]
    entries = "\n".join(
        f"  <url>\n    <loc>{loc}</loc>\n    <lastmod>{LASTMOD}</lastmod>\n    <priority>{prio}</priority>\n  </url>"
        for loc, prio in urls
    )
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + entries + "\n</urlset>\n"
    )
    written.append("sitemap.xml")

    # 404
    body_404 = '''<div class="notfound">
<div class="code404">404 · not found</div>
<h1>This cell is inactive.</h1>
<p>The page you asked for does not exist. Unlike a Durable Object, it will not activate on request.</p>
<div class="cta-row"><a class="btn btn-primary" href="/">Back to the homepage</a><a class="btn btn-secondary" href="/docs/">Browse the docs</a></div>
</div>'''
    (OUT / "404.html").write_text(f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Page not found · celld-operator</title>
<meta name="robots" content="noindex">
{HEAD_COMMON}
</head>
<body>
{header()}
<main id="main">
{body_404}
</main>
{FOOTER}
</body>
</html>
''')
    written.append("404.html")
    print("wrote:\n  " + "\n  ".join(written))


if __name__ == "__main__":
    build()
