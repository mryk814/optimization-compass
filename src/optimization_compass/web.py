# ruff: noqa: E501
from __future__ import annotations

CANONICAL_ATLAS_URL = "https://mryk814.github.io/optimization-compass/"
LEGACY_BROWSER_UI_LAST_VERSION = "0.1.x"
CANONICAL_BROWSER_UI_FIRST_VERSION = "0.2.0"

SERVICE_LANDING_HTML = f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <link rel="icon" href="data:," />
  <link rel="canonical" href="{CANONICAL_ATLAS_URL}" />
  <title>Optimization Compass API</title>
  <style>
    :root {{ color-scheme: light; color:#17211b; background:#f4f3ed; font-family:Inter,"Noto Sans JP","Yu Gothic UI",system-ui,sans-serif; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; min-height:100vh; display:grid; place-items:center; padding:1rem; }}
    main {{ width:min(42rem,100%); border:1px solid #d4d6cf; border-radius:.75rem; background:#faf9f4; padding:clamp(1.2rem,4vw,2.4rem); box-shadow:0 1rem 3rem #263c3014; }}
    .eyebrow {{ margin:0 0 .35rem; color:#56615a; font-size:.78rem; font-weight:700; letter-spacing:.09em; text-transform:uppercase; }}
    h1 {{ margin:0; font-size:clamp(1.8rem,7vw,3rem); letter-spacing:-.04em; }}
    p {{ line-height:1.65; }}
    .notice {{ margin:1.25rem 0; border-left:4px solid #315bda; background:#eef3ff; padding:.75rem 1rem; }}
    .actions {{ display:flex; flex-wrap:wrap; gap:.55rem; margin:1.25rem 0; }}
    a {{ color:#163486; text-underline-offset:.2em; }}
    .primary {{ border-radius:999px; background:#315bda; color:#fff; padding:.6rem .9rem; font-weight:700; text-decoration:none; }}
    code {{ overflow-wrap:anywhere; }}
    footer {{ margin-top:1.4rem; padding-top:1rem; border-top:1px solid #d4d6cf; color:#56615a; font-size:.82rem; }}
  </style>
</head>
<body>
  <main data-browser-role="service-landing">
    <p class="eyebrow">Local API service</p>
    <h1>Optimization Compass</h1>
    <p>ブラウザで探索・診断するcanonical experienceは <strong>Optimization Atlas</strong> です。このFastAPI serviceはREST API、OpenAPI、health checkを提供します。</p>
    <aside class="notice" aria-label="旧ブラウザ診断画面の移行案内">
      旧FastAPI診断画面のsupportは{LEGACY_BROWSER_UI_LAST_VERSION}で終了しました。{CANONICAL_BROWSER_UI_FIRST_VERSION}以降は同じ診断をAtlasで利用してください。REST APIとCLIは継続します。
    </aside>
    <nav class="actions" aria-label="利用可能な入口">
      <a class="primary" href="{CANONICAL_ATLAS_URL}">Optimization Atlasを開く</a>
      <a href="/docs">OpenAPI docs</a>
      <a href="/openapi.json">OpenAPI JSON</a>
      <a href="/healthz">Health check</a>
    </nav>
    <p>offline/localでAtlasを使う場合は <code>cd site &amp;&amp; npm ci &amp;&amp; npm run dev</code> を実行してください。</p>
    <footer>Deterministic REST API · versioned SQLite knowledge base</footer>
  </main>
</body>
</html>"""
