#!/usr/bin/env python3
"""Validate handoff IDs, source links, dependency DAG and optional manifest hashes.
No repository code, network, or package installation is used.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]

def walk(obj, sources, where):
    if isinstance(obj,dict):
        for k,v in obj.items():
            if k=='source_refs' and isinstance(v,list):
                for sid in v:
                    if sid not in sources: raise ValueError(f'{where}: unknown source {sid}')
            elif k=='source_ref' and isinstance(v,str) and v not in sources:
                raise ValueError(f'{where}: unknown source {v}')
            walk(v,sources,where)
    elif isinstance(obj,list):
        for v in obj: walk(v,sources,where)

def main():
    files=[p for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    parsed={p.relative_to(ROOT).as_posix():json.loads(p.read_text(encoding='utf-8')) for p in files if p.suffix=='.json'}
    rows=parsed['sources.json']['sources']; sources={r['source_id'] for r in rows}
    if len(sources)!=len(rows): raise ValueError('duplicate source IDs')
    for path,obj in parsed.items(): walk(obj,sources,path)
    specs=[('catalog/reference_topics.json','topics','topic_id'),('catalog/problem_scope.json','items','scope_item_id'),
           ('catalog/domain_bridges.json','bridges','bridge_id'),('catalog/personas.json','personas','persona_id'),
           ('catalog/experience_patterns.json','patterns','pattern_id'),('catalog/decision_rule_candidates.json','rules','candidate_rule_id')]
    counts={}
    for path,key,idkey in specs:
        rows=parsed[path][key]; ids=[r[idkey] for r in rows]
        if len(set(ids))!=len(ids): raise ValueError('Duplicate IDs in '+path)
        counts[key if key!='items' else 'problem_topics']=len(rows)
    issues=parsed['backlog/issues.json']['issues']; byid={i['issue_id']:i for i in issues}
    if len(byid)!=len(issues): raise ValueError('Duplicate issue IDs')
    visited=set(); active=set()
    def visit(i):
        if i in active: raise ValueError('Cyclic dependency '+i)
        if i in visited:return
        if i not in byid:raise ValueError('Unknown dependency '+i)
        active.add(i)
        for dep in byid[i]['dependencies']:visit(dep)
        active.remove(i); visited.add(i)
    for iid in byid:
        visit(iid)
        if not (ROOT/'backlog'/f'{iid}.md').is_file(): raise ValueError('Missing issue card '+iid)
    for p in files:
        if p.suffix=='.md':
            for dest in re.findall(r'\[[^\]]*\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
                if dest.startswith(('http:','https:','mailto:','#')): continue
                target=dest.split('#')[0].split(' "')[0]
                if target and not (p.parent/target).resolve().exists(): raise ValueError(f'Missing relative link {p}: {dest}')
    hashes=0
    manifest=parsed.get('MANIFEST.json')
    if manifest:
        for entry in manifest['files']:
            p=ROOT/entry['path']
            if not p.is_file(): raise ValueError('Manifest file missing '+entry['path'])
            if hashlib.sha256(p.read_bytes()).hexdigest()!=entry['sha256']:
                raise ValueError('Manifest mismatch '+entry['path'])
            hashes+=1
    print(json.dumps({'status':'passed','json_files':len(parsed),'sources':len(sources),**counts,
                      'issues':len(issues),'dependency_dag':'acyclic','manifest_hashes_checked':hashes,
                      'not_tested':['repository source/build/tests','browser UI','learning efficacy','all topic semantic mappings']},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
