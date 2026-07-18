import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { parseLearningSliceArtifact, type LearningSliceArtifact } from "../../contracts/learning-slices";
import { parseVisualizationScenarioIndex, type VisualizationScenario } from "../../contracts/visualization-scenarios";
import { siteBaseUrl } from "../../data/base-url";
import { EvidenceLinks } from "../evidence/EvidenceLinks";
import { NotFoundPage } from "../navigation/NotFoundPage";
import { ScenarioLessonPanel } from "../visualization/ScenarioLessonPanel";
import { ScenarioContextPanel } from "../theater/ScenarioContextPanel";
import { LearningSliceRenderer } from "./renderer-registry";

type State =
  | { status: "loading" }
  | { status: "error"; error: Error }
  | { status: "not-found" }
  | { status: "ready"; scenario: VisualizationScenario; artifact: LearningSliceArtifact };

export function LearningSlicePage() {
  const { scenarioId = "" } = useParams();
  const [state, setState] = useState<State>({ status: "loading" });
  useEffect(() => {
    const controller = new AbortController();
    setState({ status: "loading" });
    void loadScenario(scenarioId, controller.signal).then(
      (result) => setState(result ? { status: "ready", ...result } : { status: "not-found" }),
      (caught: unknown) => {
        if (!controller.signal.aborted) setState({ status: "error", error: caught instanceof Error ? caught : new Error(String(caught)) });
      },
    );
    return () => controller.abort();
  }, [scenarioId]);
  if (state.status === "not-found") return <NotFoundPage detail={`可視化シナリオ「${scenarioId}」は登録されていません。`} />;
  if (state.status === "error") return <section className="atlas-page"><h1>可視化を読み込めません</h1><p role="alert">{state.error.message}</p></section>;
  if (state.status === "loading") return <p role="status">可視化を読み込んでいます…</p>;
  const { scenario, artifact } = state;
  const kindLabel = artifact.artifact_kind === "executable_trace"
    ? "実行Trace (Executable teaching trace)"
    : "実行結果 (Executable result)";
  return (
    <section className="atlas-page learning-slice-page">
      <header className="atlas-page-header">
        <p className="eyebrow">Learning slice · {artifact.renderer_family}</p>
        <h1>{scenario.title_ja}</h1>
        <p>{scenario.title_en}</p>
        <div className="artifact-provenance" aria-label="可視化の由来">
          <strong>{kindLabel}</strong>
          <span>描画方式 (Renderer family): {artifact.renderer_family}</span>
          <span>問題 (Problem): {scenario.problem_instance_id}</span>
        </div>
      </header>
      <ScenarioContextPanel scenario={scenario} />
      <LearningSliceRenderer
        artifact={artifact}
        initialRunRole={scenario.purpose === "failure_contrast" ? "failure_contrast" : scenario.purpose === "sensitivity" ? "comparison" : "primary"}
      />
      <ScenarioLessonPanel scenario={scenario} />
      <section className="learning-slice-links" aria-label="関連する入口">
        <h2>同じデータからたどる</h2>
        <Link to="/map">Mapで問題の構造を見る</Link>
        {scenario.runs.map((run) => <Link key={run.run_id} to={`/methods/${run.method_id}`}>{run.method_id}の手法教材を見る</Link>)}
      </section>
      <p className="atlas-note">{scenario.lesson.limitations_ja}</p>
      <EvidenceLinks sourceIds={scenario.source_ids} />
    </section>
  );
}

async function loadScenario(scenarioId: string, signal: AbortSignal) {
  const indexResponse = await fetch(`${siteBaseUrl()}data/visualization-scenarios.json`, { signal });
  if (!indexResponse.ok) throw new Error(`Visualization scenarios request failed (${indexResponse.status}).`);
  const index = parseVisualizationScenarioIndex(await indexResponse.json());
  const scenario = index.scenarios.find((candidate) => candidate.scenario_id === scenarioId);
  if (!scenario || (scenario.artifact.renderer_family !== "feasible_region" && scenario.artifact.renderer_family !== "pareto_front" && scenario.artifact.renderer_family !== "field_evolution")) return undefined;
  const payloadResponse = await fetch(`${siteBaseUrl()}data/${scenario.artifact.payload_path}`, { signal });
  if (!payloadResponse.ok) throw new Error(`Visualization payload request failed (${payloadResponse.status}).`);
  const artifact = parseLearningSliceArtifact(await payloadResponse.json());
  if (artifact.dataset_version !== index.dataset_version || artifact.renderer_family !== scenario.artifact.renderer_family) {
    throw new Error("Visualization payload identity differs from its canonical scenario.");
  }
  return { scenario, artifact };
}
