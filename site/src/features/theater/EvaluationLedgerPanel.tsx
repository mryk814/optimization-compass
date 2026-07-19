import type { EvaluationLedger, EvaluationLedgerEntry } from "../../contracts/surrogate-uncertainty";

const statusLabels: Record<EvaluationLedgerEntry["status"], string> = {
  ok: "ok",
  failed: "failed",
  censored: "censored",
  timeout: "timeout",
};

export function EvaluationLedgerPanel({
  ledger,
  visibleCalls,
}: {
  ledger: EvaluationLedger;
  visibleCalls: number;
}) {
  const calls = ledger.calls.slice(0, visibleCalls);
  const latest = calls.at(-1);
  return (
    <section className="bo-ledger" aria-labelledby="bo-ledger-title">
      <header>
        <p className="eyebrow">評価を1 callずつ読む</p>
        <h2 id="bo-ledger-title">Simulator evaluation ledger</h2>
        <p>
          low/high fidelityのcostと、値を得られなかったcallのstatusを同じ履歴に残します。
          best-so-farは成功したhigh fidelityだけで更新します。
        </p>
      </header>
      <dl className="bo-ledger-summary">
        <div>
          <dt>累積cost</dt>
          <dd>{latest?.accumulated_cost.toFixed(0) ?? "0"} / {ledger.budget_cost.toFixed(0)}</dd>
        </div>
        <div>
          <dt>high相当budget</dt>
          <dd>{latest?.accumulated_high_fidelity_equivalent_cost.toFixed(2) ?? "0.00"} / {ledger.high_fidelity_equivalent_budget.toFixed(2)}</dd>
        </div>
        <div>
          <dt>high fidelity best-so-far</dt>
          <dd>{latest?.best_so_far?.toFixed(3) ?? "未観測"}</dd>
        </div>
      </dl>
      <div className="bo-ledger-table-wrap">
        <table aria-label="Simulator evaluation ledger">
          <caption>表示中のsimulator call {calls.length}/{ledger.calls.length}</caption>
          <thead>
            <tr>
              <th>call</th>
              <th>x</th>
              <th>fidelity</th>
              <th>cost</th>
              <th>status</th>
              <th>observed value</th>
              <th>累積cost</th>
              <th>best-so-far</th>
            </tr>
          </thead>
          <tbody>
            {calls.map((call) => (
              <tr key={call.call_id} className={`bo-ledger-status-${call.status}`}>
                <td>{call.call_id}</td>
                <td>{call.x.toFixed(2)}</td>
                <td>{call.fidelity}</td>
                <td>{call.cost.toFixed(0)}</td>
                <td>{statusLabels[call.status]}</td>
                <td>{call.observed_value?.toFixed(3) ?? "—"}</td>
                <td>{call.accumulated_cost.toFixed(0)}</td>
                <td>{call.best_so_far?.toFixed(3) ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="atlas-note">
        失敗・censored・timeoutを大きな目的値へ置換していません。この単独runはledgerの読み方を示すもので、fidelity policyの一般的順位は判定しません。
      </p>
    </section>
  );
}
