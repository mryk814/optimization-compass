#!/usr/bin/env python3
"""Read-only baseline audit. Standard library; never imports or executes repo code.

Exact string/ID matches are candidates, NOT human-approved semantic coverage.
Output must be outside the inspected repository. No network calls or git changes.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import unicodedata
from typing import Any

MAX_JSON = 50 * 1024 * 1024
MAX_DB = 256 * 1024 * 1024

def normalized(value: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFKC', value).casefold() if c.isalnum())

def read_json(path: Path) -> Any:
    if path.stat().st_size > MAX_JSON:
        raise ValueError(f'JSON exceeds {MAX_JSON} bytes: {path.name}')
    return json.loads(path.read_text(encoding='utf-8-sig'))

def file_observation(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {'observed': False, 'reason': 'file_not_found', 'bytes': None, 'sha256': None}
    return {'observed': True, 'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

def quote_identifier(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'

def database_audit(db: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if not db.is_file():
        return {'observed': False, 'reason': 'database_not_found'}, []
    if db.stat().st_size > MAX_DB:
        return {'observed': False, 'reason': 'database_size_limit'}, []
    counts: dict[str, int] = {}
    methods: list[dict[str, Any]] = []
    # mode=ro prohibits writes to the inspected SQLite file.
    con = sqlite3.connect(db.resolve().as_uri() + '?mode=ro', uri=True, timeout=5)
    con.row_factory = sqlite3.Row
    try:
        con.execute('PRAGMA query_only=ON')
        names = [r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        for name in names:
            counts[name] = int(con.execute('SELECT COUNT(*) FROM ' + quote_identifier(name)).fetchone()[0])
        if 'methods' in names:
            cols = [r[1] for r in con.execute('PRAGMA table_info("methods")')]
            safe_cols = [x for x in ('method_id', 'name_ja', 'name_en', 'method_level', 'method_type') if x in cols]
            if 'method_id' in safe_cols:
                query = 'SELECT ' + ','.join(quote_identifier(c) for c in safe_cols) + ' FROM "methods" ORDER BY "method_id"'
                methods = [dict(r) for r in con.execute(query)]
        return {'observed': True, 'table_count': len(counts), 'table_rows': counts,
                'row_count': sum(counts.values()), 'read_only': True}, methods
    finally:
        con.close()

def candidate_mapping(topics: list[dict[str, Any]], methods: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {str(m['method_id']): m for m in methods if m.get('method_id')}
    name_index: dict[str, set[str]] = {}
    for mid, method in by_id.items():
        for key in ('name_ja', 'name_en'):
            if isinstance(method.get(key), str) and normalized(method[key]):
                name_index.setdefault(normalized(method[key]), set()).add(mid)
    output=[]
    for topic in topics:
        hint=topic.get('existing_canonical_id_hint')
        matched: set[str]=set()
        basis=[]
        if hint in by_id:
            matched.add(hint); basis.append('explicit_id_hint_exists')
        names=[topic.get('title_ja',''),topic.get('title_en',''),*topic.get('aliases',[])]
        for name in names:
            if isinstance(name,str):
                hits=name_index.get(normalized(name),set())
                if hits:
                    matched.update(hits); basis.append('normalized_exact_name')
        status='auto_exact_candidate' if len(matched)==1 else 'ambiguous' if matched else 'needs_semantic_review'
        output.append({'scope_item_id':topic['topic_id'],'candidate_canonical_ids':sorted(matched),
                       'match_basis':sorted(set(basis)),'mapping_status':status,
                       'approved_coverage':False,
                       'note':'Unmatched does not prove absence; aliases, combined entries and primitives require review.'})
    return output

def audit(repo: Path, scope: Path) -> dict[str, Any]:
    repo=repo.resolve()
    if not repo.is_dir(): raise ValueError('Repository directory does not exist')
    warnings=[]
    try:
        head=subprocess.run(['git','-C',str(repo),'rev-parse','HEAD'],capture_output=True,text=True,timeout=5,check=True).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        head=None; warnings.append('git HEAD unavailable; no commit identity asserted')
    db=repo/'src/optimization_compass/resources/knowledge.sqlite'
    try:
        db_report,methods=database_audit(db)
    except (sqlite3.Error, OSError, ValueError) as exc:
        db_report={'observed':False,'error':str(exc)}; methods=[]
        warnings.append('SQLite audit incomplete')
    sitepath=repo/'site/public/data/recommendation/site-data.json'
    if not methods and sitepath.is_file():
        data=read_json(sitepath)
        raw=data.get('methods',[]) if isinstance(data,dict) else []
        methods=[m for m in raw if isinstance(m,dict) and m.get('method_id')]
        warnings.append('Method records read from exported site data, not SQLite; other DB totals may be unavailable')
    paths={}
    for rel in ['data/seeds/learning_paths.json','data/seeds/site_gallery.json',
                'data/seeds/formulation_atlas.json','src/optimization_compass/resources/explorables.json',
                'data/seeds/article_quality_ledger.json','site/public/data/manifest.json',
                'site/public/data/coverage.json']:
        path=repo/rel
        obs=file_observation(path)
        if obs['observed']:
            try:
                data=read_json(path)
                obs['root_keys']=sorted(data) if isinstance(data,dict) else None
                obs['array_lengths']={k:len(v) for k,v in data.items() if isinstance(v,list)} if isinstance(data,dict) else {}
                if rel.endswith('learning_paths.json') and isinstance(data,dict) and isinstance(data.get('paths'),list):
                    obs['authored_paths']=len(data['paths'])
                    obs['step_references']=sum(len(p.get('steps',[])) for p in data['paths'] if isinstance(p,dict))
                if rel.endswith('manifest.json') and isinstance(data,dict):
                    obs['dataset_version']=data.get('dataset_version')
            except (ValueError, OSError) as exc:
                obs['parse_error']=str(exc)
        paths[rel]=obs
    scope_data=read_json(scope)
    topics=scope_data['topics']
    mapping=candidate_mapping(topics,methods)
    counts={s:sum(m['mapping_status']==s for m in mapping) for s in ('auto_exact_candidate','ambiguous','needs_semantic_review')}
    return {'audit_contract_version':'1.0','audited_at_utc':datetime.now(timezone.utc).isoformat(),
            'repo_head':head,'scope_version':scope_data.get('scope_version'),
            'database':db_report,'files':paths,'method_records_observed':len(methods),
            'mapping_candidate_counts':counts,'mapping_candidates':mapping,
            'approved_scope_coverage':None,
            'coverage_reason':'Semantic approval and eligibility decisions have not been performed by this read-only audit.',
            'warnings':warnings,'executed_repository_code':False,'network_used':False,'modified_repository':False}

def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,required=True)
    p.add_argument('--scope',type=Path,default=Path(__file__).resolve().parents[1]/'catalog/reference_topics.json')
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    repo=args.repo.resolve(); out=args.out.resolve()
    if out.is_relative_to(repo):
        p.error('--out must be outside the inspected repository')
    try:
        result=audit(repo,args.scope)
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    except (OSError,ValueError,KeyError,json.JSONDecodeError) as exc:
        p.exit(1,f'Audit failed without repository mutation: {exc}\n')
    print(f'Read-only audit written: {out}')
    print('Matches are candidates only; approved coverage was not calculated.')
if __name__=='__main__': main()
