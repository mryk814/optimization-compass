# ruff: noqa: E501
from __future__ import annotations

HTML = r"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>最適化コンパス</title>
  <style>
    :root { color-scheme: light dark; --accent:#0f766e; --soft:#dff5f1; --warn:#fff3cd; }
    * { box-sizing: border-box; }
    body { margin:0; font-family: ui-sans-serif, system-ui, sans-serif; line-height:1.55; }
    header { padding:2.2rem 1.2rem; background:linear-gradient(135deg,#083344,#0f766e); color:white; }
    header div, main { max-width:960px; margin:auto; }
    h1 { margin:0 0 .4rem; font-size:clamp(2rem,5vw,3.4rem); }
    header p { max-width:720px; margin:0; opacity:.9; }
    main { padding:1.2rem; }
    .notice { border-left:5px solid var(--accent); padding:1rem; background:var(--soft); color:#123; border-radius:.5rem; }
    .question,.result { border:1px solid #aaa6; padding:1rem; border-radius:.8rem; margin:1rem 0; }
    .question h3,.result h3 { margin-top:0; }
    label { display:block; padding:.35rem .2rem; }
    button { border:0; border-radius:.6rem; padding:.85rem 1.2rem; background:var(--accent); color:white; font-weight:700; cursor:pointer; }
    button:disabled { opacity:.5; cursor:wait; }
    .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:1rem; }
    .tag { display:inline-block; font-size:.8rem; padding:.15rem .45rem; border-radius:99px; background:#8882; margin:.1rem; }
    .warning { background:var(--warn); color:#3d3000; padding:.8rem; border-radius:.5rem; }
    details { margin:.8rem 0; }
    code { overflow-wrap:anywhere; }
    footer { text-align:center; padding:2rem; opacity:.7; }
  </style>
</head>
<body>
<header><div>
  <h1>最適化コンパス 🧭</h1>
  <p>問題の特徴を整理して、代替解法・手法・実装候補と「なぜ」を返します。万能ランキングではなく、前提確認のための診断器です。</p>
</div></header>
<main>
  <div class="notice">不明な項目は unknown 系の回答を選んでください。推測で埋めないことが、良い推薦への近道です。</div>
  <form id="form"><div id="questions">読み込み中…</div><button id="submit" type="submit">診断する</button></form>
  <section id="output"></section>
</main>
<footer><a href="/docs">OpenAPI</a> · deterministic rules + versioned SQLite</footer>
<script>
const qEl=document.querySelector('#questions'); const out=document.querySelector('#output');
const form=document.querySelector('#form'); const submit=document.querySelector('#submit');
let questions=[];
function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
async function load(){
  const r=await fetch('/v1/questions'); questions=await r.json();
  qEl.innerHTML=questions.map(q=>`<fieldset class="question"><h3>${q.sequence}. ${esc(q.question)}</h3><p>${esc(q.why_asked)}</p>${q.allowed_answers.map(a=>`<label><input type="${q.answer_type==='multi_choice'?'checkbox':'radio'}" name="${esc(q.question_id)}" value="${esc(a)}"> <code>${esc(a)}</code></label>`).join('')}</fieldset>`).join('');
}
function cards(title,items){if(!items?.length)return ''; return `<h2>${title}</h2><div class="grid">${items.map(x=>`<article class="result"><h3>${esc(x.name)}</h3><div><span class="tag">${esc(x.entity_id)}</span><span class="tag">支持規則 ${x.supporting_rule_count}</span></div><p>${esc(x.summary)}</p><ul>${x.reasons.map(r=>`<li>${esc(r)}</li>`).join('')}</ul>${x.warnings.map(w=>`<p class="warning">${esc(w)}</p>`).join('')}${x.implementations?.length?`<details><summary>代表実装</summary><ul>${x.implementations.map(i=>`<li><b>${esc(i.library_name)} ${esc(i.solver_name)}</b> — ${esc(i.language)} / ${esc(i.license)} / ${esc(i.maintenance_status)} ${i.official_docs_url?`<a href="${esc(i.official_docs_url)}" rel="noreferrer">docs</a>`:''}</li>`).join('')}</ul></details>`:''}</article>`).join('')}</div>`;}
form.addEventListener('submit',async e=>{
  e.preventDefault(); submit.disabled=true; out.innerHTML='<p>診断中…</p>';
  const fd=new FormData(form); const answers={};
  for(const q of questions){const vals=fd.getAll(q.question_id); if(vals.length)answers[q.question_id]=vals;}
  try{
    const r=await fetch('/v1/recommendations',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({answers,language:'ja'})});
    const d=await r.json(); if(!r.ok)throw new Error(JSON.stringify(d));
    out.innerHTML=`<h1>診断結果</h1>${d.warnings.map(w=>`<p class="warning">${esc(w)}</p>`).join('')}${cards('まず確認する代替解法',d.alternatives_first)}${cards('第一候補',d.first_choices)}${cards('条件付き候補',d.conditional_choices)}${cards('避ける候補',d.excluded_methods)}${cards('問題類型の候補',d.candidate_problem_archetypes)}${d.followups.length?`<h2>追加確認</h2><ul>${d.followups.map(f=>`<li>${esc(f.explanation)} <code>${esc(f.target_ids.join(';'))}</code></li>`).join('')}</ul>`:''}<details><summary>発火した規則 (${d.trace.length})</summary><pre>${esc(JSON.stringify(d.trace,null,2))}</pre></details><p>${esc(d.disclaimer)}</p>`;
    out.scrollIntoView({behavior:'smooth'});
  }catch(err){out.innerHTML=`<p class="warning">エラー: ${esc(err)}</p>`;}finally{submit.disabled=false;}
});
load().catch(e=>qEl.textContent='質問の読み込みに失敗しました: '+e);
</script>
</body></html>"""
