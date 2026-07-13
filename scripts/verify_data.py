from __future__ import annotations

import json

from optimization_compass.db import KnowledgeRepository

result = KnowledgeRepository().verify()
print(json.dumps(result, ensure_ascii=False, indent=2))
raise SystemExit(0 if result["ok"] else 1)
