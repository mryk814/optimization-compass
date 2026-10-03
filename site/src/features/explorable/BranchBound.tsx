import { useLayoutEffect, useRef, useState } from "react";
import { ExplorableFrame } from "./ExplorableFrame";
import { act, INTRO, SCENARIOS, certificate, nodeId, relaxation, startSearch, totals, type Choice, type SearchState, type Scenario } from "./math/branchBound";
import "./branch-bound.css";

// Round displayed upper bounds outwards, so the label never understates the bound.
const upperText = (n: number) => (Math.ceil(n * 100 - 1e-10) / 100).toLocaleString("ja-JP", { maximumFractionDigits: 2 });
const selectedNames = (choice: Choice, scenario: Scenario) => scenario.items.filter((_, i) => choice[i]).map((item) => item.name).join("・") || "なし";
const candidateTitle = (choice: Choice, scenario: Scenario) => choice.length
  ? choice.map((take, i) => `${scenario.items[i].name}${take ? "あり" : "なし"}`).join("・") : "すべて未決定";
// All objects use the same icon box. Weight is represented only by numbers and the meter.
function ItemIcon({ name }: { name: string }) {
  const shapes: Record<string, React.ReactNode> = {
    A: <><rect x="6" y="12" width="28" height="20" rx="3"/><path d="M10 12l3-5h9l3 5"/><circle cx="21" cy="22" r="7"/></>,
    D: <><path d="M15 5h10v6l4 5v19H11V16l4-5z"/><path d="M15 11h10M11 23h18"/></>,
    B: <><path d="M7 8h12l3 3 3-3h8v25H22l-3-2H7zM22 11v22"/><path d="M11 14h6M11 19h6M26 15h4"/></>,
    C: <><rect x="9" y="8" width="23" height="26" rx="5"/><path d="M15 8V5h11v3M9 18h23M19 18v8h4v-8"/></>,
    E: <><path d="M10 15h20v18H10zM10 15L7 9h26l-3 6M17 15v18M24 15v18"/></>,
    F: <><rect x="7" y="13" width="26" height="20" rx="3"/><path d="M14 13V7h12v6M7 20h26M17 20v5h6v-5"/></>,
    G: <><path d="M9 16h20v15H9zM29 18h3a5 5 0 010 10h-3M13 6v6M20 5v7M26 6v6"/></>,
    H: <><path d="M10 29l16-16 6 6-16 16zM24 15l-5-8 8-3 7 9-4 4"/><path d="M12 28l5 5"/></>,
  };
  return <svg className="bnb-object" width="40" height="40" viewBox="0 0 40 40" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2" strokeLinejoin="round">{shapes[name]}</svg>;
}
function ConditionChips({ choice, scenario }: { choice: Choice; scenario: Scenario }) {
  return <span className="bnb-condition-chips">{choice.length ? choice.map((take, i) => <span key={i}>{scenario.items[i].name}{take ? "✓" : "×"}</span>) : <span>条件なし</span>}</span>;
}
function Packing({ choice, scenario }: { choice: Choice; scenario: Scenario }) {
  const score = totals(choice, scenario);
  const packed = scenario.items.filter((_, i) => choice[i] === 1);
  return <div className={`bnb-packing${score.weight > scenario.capacity ? " bnb-infeasible" : ""}`} role="group" aria-label={`${candidateTitle(choice, scenario)}の袋`}>
    <div className={`bnb-bag${score.weight > scenario.capacity ? " bnb-overweight" : ""}`}>
      <span className="bnb-bag-label">袋の中</span>
      <div className="bnb-packed">{packed.length ? packed.map((item) => <span key={item.name}><ItemIcon name={item.name}/><strong>{item.name}</strong></span>) : <span className="bnb-empty">空</span>}</div>
    </div>
    <div className="bnb-packing-metrics">
      <div className="bnb-capacity"><span>容量使用 <strong>{score.weight} / {scenario.capacity}</strong></span><progress max={scenario.capacity} value={Math.min(score.weight, scenario.capacity)} aria-label="袋の重量" /><span>{score.weight > scenario.capacity ? `⚠ 容量超過 ${score.weight - scenario.capacity}` : `残り ${scenario.capacity - score.weight}`}</span></div>
      <div className="bnb-bag-value"><span>{choice.length < scenario.items.length ? "固定品の得点" : "袋の得点"}</span><strong>{score.value}<span>点</span></strong></div>
    </div>
  </div>;
}
const preferred = (frontier: Choice[], scenario: Scenario) => [...frontier].sort((a, b) => relaxation(b, scenario).bound - relaxation(a, scenario).bound)[0];

const closedText = { split: "分けた", bound: "終了：記録以下", infeasible: "終了：容量超過", leaf: "終了：記録更新" } as const;
function BranchFocus({ state, onSelect }: { state: SearchState; onSelect: (id: string) => void }) {
  const last = state.closed.at(-1)!;
  const focus = last.choice;
  const parent = focus.slice(0, -1);
  const isRoot = !focus.length;
  const pair: Choice[] = isRoot ? [] : [[...parent, 1], [...parent, 0]];
  const children: Choice[] = last.reason === "split" ? [[...focus, 1], [...focus, 0]] : [];
  const node = (choice: Choice, inherited = false) => {
    const id = nodeId(choice);
    const closed = state.closed.find((entry) => nodeId(entry.choice) === id);
    const available = state.frontier.some((entry) => nodeId(entry) === id);
    const status = available ? `未決定 ${state.scenario.items.length - choice.length}品` : closed ? closedText[closed.reason] : "引き継ぐ条件";
    const kind = available ? "pending" : closed?.reason === "split" ? "split" : "closed";
    const contents = <><span className="bnb-condition-chips">{inherited
      ? choice.length ? choice.map((take, i) => <span key={i}>{state.scenario.items[i].name}{take ? "✓" : "×"}</span>) : <span>条件なし</span>
      : <span>{state.scenario.items[choice.length - 1].name}{choice.at(-1) ? "✓ 入れる" : "× 入れない"}</span>}</span><span className="bnb-node-state">{status}{id === nodeId(focus) && "・直近"}</span></>;
    const label = `${candidateTitle(choice, state.scenario)}：${status}`;
    return available
      ? <button type="button" className={`bnb-branch-node ${kind}`} data-branch-id={id} data-branch-state={kind} aria-label={`${label}の候補へ`} aria-controls="bnb-selected-candidate" onClick={() => onSelect(id)}>{contents}</button>
      : <div className={`bnb-branch-node ${kind}${id === nodeId(focus) ? " current" : ""}`} data-branch-id={id} data-branch-state={kind} role="group" aria-label={label}>{contents}</div>;
  };
  const fork = <svg className="bnb-branch-lines" width="100%" height="18" viewBox="0 0 100 18" preserveAspectRatio="none" aria-hidden="true"><path d="M50 0V8H25V18M50 8H75V18" /></svg>;
  const row = (choices: Choice[], itemIndex: number) => <div className="bnb-branch-row">{choices.map((choice) => <div key={nodeId(choice)} className="bnb-branch-arm"><span className="bnb-edge-label">{state.scenario.items[itemIndex].name}{choice.at(-1) ? "入れる" : "入れない"}</span>{node(choice)}</div>)}</div>;
  return <div className="bnb-branch-focus" role="group" aria-label="直近の枝のつながり">
    <p className="bnb-branch-heading">{parent.length ? "親から引き継ぐ条件" : "ここから条件を決める"}</p>
    <div className="bnb-branch-parent">{node(isRoot ? focus : parent, true)}</div>
    {!isRoot && <>{fork}{row(pair, focus.length - 1)}</>}
    {children.length > 0 && <>{!isRoot && <svg className="bnb-branch-lines" width="100%" height="18" viewBox="0 0 100 18" preserveAspectRatio="none" aria-hidden="true"><path d={`M${focus.at(-1) ? 25 : 75} 0V8H50V18`} /></svg>}{fork}{row(children, focus.length)}</>}
    <p className="bnb-branch-hint">未決定の枠から袋を確認できます。</p>
  </div>;
}

export default function BranchBound() {
  const [scenario, setScenario] = useState<Scenario>(INTRO);
  const ITEMS = scenario.items;
  const CAPACITY = scenario.capacity;
  const emptyChoice = () => ITEMS.map(() => 0 as const);
  const [choice, setChoice] = useState<Choice>(INTRO.items.map(() => 0));
  const [history, setHistory] = useState<SearchState[]>([]);
  const [feedback, setFeedback] = useState<{ id: string; text: string }>();
  const changeRef = useRef<HTMLDivElement>(null);
  const cardRef = useRef<HTMLElement>(null);
  const requestedFocus = useRef(false);
  const [selectedId, setSelectedId] = useState<string>();
  const state = history.at(-1);
  const savedScroll = useRef<{ x: number; y: number } | null>(null);
  const preserveScroll = () => { savedScroll.current = { x: window.scrollX, y: window.scrollY }; };
  useLayoutEffect(() => {
    if (requestedFocus.current) {
      cardRef.current?.focus({ preventScroll: true });
      requestedFocus.current = false;
    } else if (state && document.activeElement === document.body) {
      // A completed search removes its last action; keep focus inside the result.
      (cardRef.current ?? changeRef.current)?.focus({ preventScroll: true });
    }
    if (savedScroll.current) {
      const { x, y } = savedScroll.current;
      if (window.scrollX !== x || window.scrollY !== y) window.scrollTo({ left: x, top: y, behavior: "instant" });
      savedScroll.current = null;
    }
  }, [selectedId, state]);
  const selectCandidate = (id: string) => {
    preserveScroll();
    if (selectedId === id) { cardRef.current?.focus({ preventScroll: true }); savedScroll.current = null; }
    else { requestedFocus.current = true; setSelectedId(id); }
    setFeedback(undefined);
  };
  const score = totals(choice, scenario);
  const bounds = state ? certificate(state) : undefined;
  const last = state?.closed.at(-1);
  const previous = history.length > 1 ? certificate(history[history.length - 2]) : undefined;
  const selected = state?.frontier.find((node) => nodeId(node) === selectedId) ?? (state ? preferred(state.frontier, scenario) : undefined);
  const begin = () => {
    preserveScroll();
    // The first action already compares A-in with A-out, rather than an abstract root.
    const next = act(startSearch(choice, scenario), "root", "open");
    setHistory([next]); setSelectedId(next.frontier.length ? nodeId(preferred(next.frontier, scenario)) : undefined); setFeedback(undefined);
  };
  const step = (node: Choice, action: "open" | "prune") => {
    if (!state || !bounds) return;
    const next = act(state, nodeId(node), action);
    if (next.frontier === state.frontier) {
      setFeedback({ id: nodeId(node), text: `最高で ${upperText(relaxation(node, scenario).bound)} 点まであり得ます。記録 ${bounds.lower} 点を超えるので、まだ調べ終えられません。` });
      return;
    }
    preserveScroll();
    setHistory([...history, next]); setSelectedId(next.frontier.length ? nodeId(preferred(next.frontier, scenario)) : undefined); setFeedback(undefined);
  };
  const summary = bounds
    ? `得点の記録 ${bounds.lower}、残る得点の上限 ${upperText(bounds.upper)}。${bounds.proven ? "最適性を証明できました。" : "もっと高い得点がないか、まだ確認が必要です。"}`
    : `重さ ${score.weight} / ${CAPACITY}、得点 ${score.value}。`;
  const renderCandidate = (node: Choice) => {
    const r = relaxation(node, scenario);
    const title = candidateTitle(node, scenario);
    const removable = !r.feasible || r.bound <= bounds!.lower;
    const integral = r.feasible && r.fill.every((part) => part === 0 || part === 1);
    return <article className={`bnb-candidate${!r.feasible ? " bnb-infeasible" : ""}`} aria-label={`${title}の候補`} data-candidate-id={nodeId(node)} id="bnb-selected-candidate" tabIndex={-1} ref={cardRef}>
      <div className="bnb-candidate-heading"><span>選択中の候補</span><ConditionChips choice={node} scenario={scenario}/></div>
      <div className="bnb-ceiling"><span>この枝の上限</span><strong>{r.feasible ? `${upperText(r.bound)}点` : "⚠ 容量超過"}</strong><span>{r.feasible ? `${r.bound <= bounds!.lower ? "≤" : ">"} 全体最高記録 ${bounds!.lower}点` : "この条件では袋に入りません"}</span></div>
      <Packing choice={node} scenario={scenario} />
      <div className="bnb-actions">
        {removable ? <button className="ex-action" type="button" onClick={() => step(node, "prune")}>この枝を終える</button>
          : <button className="ex-action" type="button" onClick={() => step(node, "open")}>{integral ? `${selectedNames(r.fill as Choice, scenario)}を記録（${r.bound}点）` : `${ITEMS[node.length].name} 入れる／入れない`}</button>}
      </div>
      <div className="bnb-detail-drawers">
      {node.length < ITEMS.length && <details className="bnb-undecided"><summary aria-label={`未決定 ${ITEMS.length - node.length}品を見る`}>未決定 {ITEMS.length - node.length}品</summary><div className="bnb-icon-row">{ITEMS.slice(node.length).map((item) => <span key={item.name}><ItemIcon name={item.name}/>{item.name}</span>)}</div></details>}
      {r.feasible && <details className="bnb-bound-details"><summary aria-label={`なぜ最高でも${upperText(r.bound)}点？ 詰め方を見る`}>上限の根拠</summary>
        <p>未決定の品は分割してよいことにし、重さあたりの得点が高い順に詰めます。</p>
        <div className="bnb-fill" aria-label={`${title}の分割してよい詰め方`}>{ITEMS.map((item, i) => <div key={item.name}><span>{item.name}{i < node.length ? "（決定済）" : ""}</span><progress max={1} value={r.fill[i]} aria-label={`${item.name}の詰めた割合`} /><span>{Math.round(r.fill[i] * 100)}%</span></div>)}</div>
        <p className="bnb-equation">{r.fill.map((part, i) => `${ITEMS[i].value}×${Number(part.toFixed(3))}`).join(" + ")} ≈ {upperText(r.bound)} 点</p>
        <p>分割を許して得た最高点なので、丸ごと選ぶ得点はこれを超えません。表示は丸めています。</p>
        {!removable && <button className="bnb-question" type="button" onClick={() => step(node, "prune")}>この枝は終了できる？</button>}
        {feedback?.id === nodeId(node) && <p className="bnb-feedback" role="status">{feedback.text}</p>}
      </details>}
      </div>
    </article>;
  };
  return <ExplorableFrame id="branch-bound-proof" summary={summary}
    controls={<div className="bnb-controls">
      <fieldset className="bnb-mode"><legend>品数を選ぶ</legend>{SCENARIOS.map((mode) => <label key={mode.id}><input type="radio" name="bnb-mode" checked={scenario.id === mode.id} onChange={() => { setScenario(mode); setChoice(mode.items.map(() => 0)); setHistory([]); setSelectedId(undefined); setFeedback(undefined); }}/>{mode.title}</label>)}</fieldset>
      <p className="bnb-mode-note">切り替えると、品選びと調査記録をやり直します。絵の大きさは重さを表しません。</p>
      {!state ? <>
        <p>重さ{CAPACITY}以内で、高い得点の組合せを作ってみましょう。各品は一つまでです。</p>
        <div className={`bnb-items${ITEMS.length === 8 ? " bnb-items-eight" : ""}`}>{ITEMS.map((item, i) => <label key={item.name}>
          <input type="checkbox" aria-label={`${item.name} 重さ${item.weight} 得点${item.value}`} checked={Boolean(choice[i])} onChange={() => setChoice(choice.map((take, j) => i === j ? (take ? 0 : 1) : take))} />
          <ItemIcon name={item.name}/><span className="bnb-choice-metrics"><strong>{item.name}</strong><span>重さ{item.weight}</span><span className="bnb-catalog-value">得点{item.value}</span></span>
        </label>)}</div>
        <Packing choice={choice} scenario={scenario} />
        <p>{summary} {score.weight > CAPACITY ? "容量超過です。品を外してみましょう。" : "この組合せなら袋に入ります。"}</p>
        <button className="ex-action" disabled={score.weight > CAPACITY} onClick={begin} type="button">Aを入れる／入れないで比べる</button>
      </> : <>
        <p>袋に入る最高記録：{selectedNames(state.best, scenario)}で{bounds!.lower}点。</p>
        <details className="bnb-catalog"><summary>品の重さと得点（{ITEMS.length}品）</summary><div className="bnb-catalog-items">{ITEMS.map((item) => <div key={item.name}><ItemIcon name={item.name}/><strong>{item.name}</strong><span>重さ{item.weight}</span><span className="bnb-catalog-value">得点{item.value}</span></div>)}</div></details>
        <div className="bnb-actions">
          <button className="ex-action" type="button" disabled={history.length <= 1} onClick={() => { setHistory(history.slice(0, -1)); setSelectedId(last ? nodeId(last.choice) : undefined); setFeedback(undefined); }}>一手戻す</button>
          <button className="ex-action" type="button" onClick={begin}>同じ組合せで再実行</button>
          <button className="ex-action" type="button" onClick={() => { setHistory([]); setChoice(emptyChoice()); setSelectedId(undefined); setFeedback(undefined); }}>品選びからやり直す</button>
        </div>
      </>}
    </div>}
    stage={state && bounds ? <div className="bnb-workspace">
      <p className="bnb-count">全{2 ** ITEMS.length}通りに対し、今調べる候補は{state.frontier.length}枠です。各枠は未決定の品の組合せをまとめています。</p>
      <div className="bnb-proof" aria-label="最適性の証明の進み具合">
        <div className="bnb-meter"><span>全体最高記録 <strong>{bounds.lower}</strong></span><span>残る得点の上限 <strong>{upperText(bounds.upper)}</strong></span></div>
        <div className="bnb-range" aria-hidden="true"><span style={{ width: `${bounds.lower / relaxation([], scenario).bound * 100}%` }} /><span style={{ width: `${(bounds.upper - bounds.lower) / relaxation([], scenario).bound * 100}%` }} /></div>
        <p className="bnb-equation">{bounds.lower} ≤ 最適値 ≤ {upperText(bounds.upper)}</p>
        <p>{history.length === 1 && !bounds.proven ? `選んだ袋の${bounds.lower}点は記録です。もっと高い得点がないことは、枝の上限を調べて確かめます。` : bounds.proven ? `${bounds.lower === score.value ? "最初に選んだ袋が最適でした。" : ""}記録と上限が一致しました。これより高い得点はありません。最適性を証明できました。` : `まだ最大 ${upperText(bounds.gap)} 点よくなる可能性を否定できていません。`}</p>
      </div>
      <div className="bnb-overview">
      <div className={`bnb-change${last && last.reason !== "split" ? " bnb-finished" : ""}`} tabIndex={-1} ref={changeRef}>
        <p role="status">{last?.reason === "split" ? `${ITEMS[last.choice.length].name}で二つに分けました。` : last ? `${candidateTitle(last.choice, scenario)}：${closedText[last.reason]}。` : ""}
          {last?.reason === "bound" && <span> 上限 {upperText(relaxation(last.choice, scenario).bound)} ≤ 記録 {bounds.lower}。</span>}
          {last?.reason === "infeasible" && <span> 重量 {totals(last.choice, scenario).weight} &gt; 容量 {CAPACITY}。</span>}
          {previous && (previous.lower !== bounds.lower || previous.upper !== bounds.upper) && <span> 記録 {previous.lower} → {bounds.lower}、上限 {upperText(previous.upper)} → {upperText(bounds.upper)}。</span>}</p>
        <BranchFocus state={state} onSelect={selectCandidate} />
        {last?.reason === "leaf" && <div className="bnb-recorded"><p>記録した完成形：{selectedNames(state.best, scenario)}、{bounds.lower}点</p><Packing choice={state.best} scenario={scenario} /></div>}
      </div>
      {state.frontier.length > 0 && <div className="bnb-comparison-list" role="group" aria-label="残る候補の比較">{state.frontier.map((node) => {
        const id = nodeId(node); const r = relaxation(node, scenario); const weight = totals(node, scenario).weight;
        return <button className={`bnb-candidate-summary${!r.feasible ? " bnb-infeasible" : ""}`} type="button" key={id} data-summary-id={id} aria-pressed={nodeId(selected!) === id} aria-controls="bnb-selected-candidate" aria-label={`${candidateTitle(node, scenario)}、この枝の上限${r.feasible ? `${upperText(r.bound)}点` : "容量超過"}を選ぶ`} onClick={() => selectCandidate(id)}>
          <ConditionChips choice={node} scenario={scenario}/><span className="bnb-summary-bound">この枝の上限 <strong>{r.feasible ? `${upperText(r.bound)}点` : "⚠ 容量超過"}</strong></span><span className="bnb-summary-capacity"><span>容量 {weight}/{CAPACITY}</span><span>未決定{ITEMS.length - node.length}品</span></span>
        </button>;
      })}</div>}
      </div>
      {selected && renderCandidate(selected)}
      {!state.frontier.length && <p>残っていた候補をすべて調べ終えました。</p>}
      <details className="bnb-log"><summary>操作記録を見る（{state.closed.length} 手）</summary><ol>{state.closed.map((node) => <li key={nodeId(node.choice)}>{candidateTitle(node.choice, scenario)}：{({ split: "次の品の有無で二つに分けた", leaf: "袋に入る組合せを記録した", bound: "最高点が記録以下なので調べ終えた", infeasible: "容量超過なので調べ終えた" })[node.reason]}</li>)}</ol></details>
    </div> : <p>たとえばAとDなら12点です。もっと高くできそうなら、品を入れ替えてみてください。</p>}
    readout={<p>分割してよい詰め方から計算した最高点の上限を「上界」、袋に入る最高記録を「暫定値」と呼びます。橙の幅は、まだ否定できていない改善の余地です。</p>}
  />;
}
