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
const ANSWER_LABELS_JA = Object.freeze({
  continuous: '連続値（continuous）', integer: '整数値（integer）',
  binary: '0/1の二値（binary）', categorical: 'カテゴリ値（categorical）',
  mixed: '混合型（mixed）', structured_or_unknown: '構造化・複雑な型（structured or unknown）',
  explicit_algebraic: '数式で表せる（explicit algebraic）',
  residual_vector: '残差ベクトルで表せる（residual vector）',
  automatic_differentiation_graph: '自動微分グラフで表せる（automatic differentiation graph）',
  simulation_only: 'シミュレーションのみ（simulation only）',
  experiment_only: '実験で評価する（experiment only）', unknown: 'わからない（unknown）',
  linear: '線形（linear）', quadratic: '二次（quadratic）',
  sum_of_squares: '二乗和（sum of squares）', general_nonlinear: '一般の非線形（general nonlinear）',
  multiobjective: '多目的（multiobjective）',
  equation_or_feasibility: '方程式・実行可能性問題（equation or feasibility）',
  none: '制約なし（none）', bounds: '上下限制約（bounds）', nonlinear: '非線形制約（nonlinear）',
  logical_or_combinatorial: '論理・組合せ制約（logical or combinatorial）',
  conic_or_psd: '錐・半正定値制約（conic or PSD）',
  dynamics_or_manifold: '力学系・多様体制約（dynamics or manifold）',
  implicit_or_failure: '暗黙的・失敗する可能性あり（implicit or failure）',
  analytic_gradient: '解析的な勾配（analytic gradient）', autodiff: '自動微分（autodiff）',
  jacobian_or_hvp: 'Jacobian・HVP（Jacobian or HVP）',
  numerical_difference_only: '数値差分のみ（numerical difference only）',
  stochastic_gradient: '確率的勾配（stochastic gradient）',
  unreliable_or_none: '信頼できない・利用不可（unreliable or none）',
  not_differentiable: '微分できない（not differentiable）',
  milliseconds_or_less: 'ミリ秒以下（milliseconds or less）', seconds: '秒（seconds）',
  minutes: '分（minutes）', hours_or_more: '時間以上（hours or more）',
  deterministic_reliable: '決定的で信頼できる（deterministic reliable）',
  small_noise: '小さなノイズ（small noise）', large_noise: '大きなノイズ（large noise）',
  random_seeded: '乱数によるがseed固定可能（random seeded）',
  occasional_failure: 'ときどき失敗する（occasional failure）',
  frequent_failure: '頻繁に失敗する（frequent failure）',
  timeout_possible: 'タイムアウトの可能性あり（timeout possible）',
  under_10: '10未満（under 10）', 10_to_100: '10〜100', 100_to_10000: '100〜10,000',
  over_10000: '10,000超（over 10,000）',
  huge_sparse_or_distributed: '巨大・疎・分散型（huge sparse or distributed）',
  local_is_fine: '局所解で十分（local is fine）',
  global_candidate_desired: '大域解の候補がほしい（global candidate desired）',
  multiple_distinct_solutions: '異なる解を複数探したい（multiple distinct solutions）',
  no_certificate_needed: '証明は不要（no certificate needed）',
  gap_desired: '最適性gapがほしい（gap desired）',
  global_proof_required: '大域最適性の証明が必要（global proof required）',
  feasible_solution_first: 'まず実行可能解がほしい（feasible solution first）',
  approximation_guarantee: '近似保証がほしい（approximation guarantee）',
  none_known: '特になし（none known）', least_squares: '最小二乗（least squares）',
  lp_qp_conic: 'LP・QP・錐最適化（LP/QP/conic）',
  graph_flow_path_matching: 'グラフ・フロー・経路・マッチング（graph/flow/path/matching）',
  scheduling_routing: 'スケジューリング・経路計画（scheduling/routing）',
  prox_separable: '近接可能・分離可能（prox/separable）',
  optimal_control: '最適制御（optimal control）', manifold: '多様体（manifold）',
  stochastic_or_robust: '確率的・ロバスト（stochastic or robust）', other: 'その他（other）',
  one_off: '一度だけ（one-off）', repeated_similar: '似た問題を繰り返す（repeated similar）',
  online_or_realtime: 'オンライン・リアルタイム（online or realtime）',
  parallel_evaluations: '評価を並列化できる（parallel evaluations）',
  distributed: '分散実行できる（distributed）', gpu_available: 'GPUを使える（GPU available）',
  warm_start_available: 'warm startを使える（warm start available）'
});
function renderQuestion(q) {
  const questionText = q.beginner_wording || q.question;
  return `<fieldset class="question"><h3>${q.sequence}. ${esc(questionText)}</h3><p><b>この質問で確認すること：</b> ${esc(q.why_asked)}</p>${q.allowed_answers.map(a => `<label><input type="${q.answer_type==='multi_choice'?'checkbox':'radio'}" name="${esc(q.question_id)}" value="${esc(a)}"> ${esc(ANSWER_LABELS_JA[a] ?? a)}</label>`).join('')}</fieldset>`;
}
async function load(){
  const r=await fetch('/v1/questions'); questions=await r.json();
  qEl.innerHTML = questions.map(renderQuestion).join('');
}
function cards(title,items){if(!items?.length)return ''; return `<h2>${title}</h2><div class="grid">${items.map(x=>`<article class="result"><h3>${esc(x.name)}</h3><div><span class="tag">${esc(x.entity_id)}</span><span class="tag">一致した判断ルール ${x.supporting_rule_count}</span></div><p>${esc(x.summary)}</p><ul>${x.reasons.map(r=>`<li>${esc(r)}</li>`).join('')}</ul>${x.warnings.map(w=>`<p class="warning">${esc(w)}</p>`).join('')}${x.implementations?.length?`<details><summary>主な実装例</summary><ul>${x.implementations.map(i=>`<li><b>${esc(i.library_name)} ${esc(i.solver_name)}</b> — ${esc(i.language)} / ${esc(i.license)} / ${esc(i.maintenance_status)} ${i.official_docs_url?`<a href="${esc(i.official_docs_url)}" rel="noreferrer">公式docs</a>`:''}</li>`).join('')}</ul></details>`:''}</article>`).join('')}</div>`;}
form.addEventListener('submit',async e=>{
  e.preventDefault(); submit.disabled=true; out.innerHTML='<p>診断中…</p>';
  const fd=new FormData(form); const answers={};
  for(const q of questions){const vals=fd.getAll(q.question_id); if(vals.length)answers[q.question_id]=vals;}
  try{
    const r=await fetch('/v1/recommendations',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({answers,language:'ja'})});
    const d=await r.json(); if(!r.ok)throw new Error(JSON.stringify(d));
    out.innerHTML=`<h1>診断結果</h1>${d.warnings.map(w=>`<p class="warning">${esc(w)}</p>`).join('')}${cards('まず確認する代替解法',d.alternatives_first)}${cards('第一候補',d.first_choices)}${cards('条件付き候補',d.conditional_choices)}${cards('避ける候補',d.excluded_methods)}${cards('問題類型の候補',d.candidate_problem_archetypes)}${d.followups.length?`<h2>追加で確認したいこと</h2><ul>${d.followups.map(f=>`<li>${esc(f.explanation)} <code>${esc(f.target_ids.join(';'))}</code></li>`).join('')}</ul>`:''}<details><summary>適用された判断ルール (${d.trace.length})</summary><pre>${esc(JSON.stringify(d.trace,null,2))}</pre></details><p>${esc(d.disclaimer)}</p>`;
    out.scrollIntoView({behavior:'smooth'});
  }catch(err){out.innerHTML=`<p class="warning">エラー: ${esc(err)}</p>`;}finally{submit.disabled=false;}
});
load().catch(e=>qEl.textContent='質問の読み込みに失敗しました: '+e);
</script>
</body></html>"""
