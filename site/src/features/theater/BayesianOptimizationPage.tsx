import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";

import { findEntity } from "../../contracts/entity-links";
import { parseSiteManifest } from "../../contracts/manifest";
import {
  parseSurrogateUncertaintyPayload,
  type SurrogateUncertaintyPayload,
} from "../../contracts/surrogate-uncertainty";
import {
  parseVisualizationScenarioIndex,
  type GuidedPlaybackSpeed,
  type GuidedStoryStep,
  type VisualizationScenario,
} from "../../contracts/visualization-scenarios";
import { siteBaseUrl } from "../../data/base-url";
import { buildAtlasNavigation } from "../../state/atlas-navigation";
import { useEntityLinks } from "../../state/entity-links";
import { atlasStateFromSearch, patchJourneyState } from "../../state/journey-navigation";
import { EvidenceLinks } from "../evidence/EvidenceLinks";
import { EntityNotFoundError, NotFoundPage } from "../navigation/NotFoundPage";
import { ScenarioLessonPanel } from "../visualization/ScenarioLessonPanel";
import { GuidedStoryPanel, type GuidedPlaybackController } from "../visualization/GuidedStoryPanel";
import { SurrogatePlot } from "../visualization/SurrogatePlot";
import { ScenarioContextPanel } from "./ScenarioContextPanel";

type Strategy = "exploit" | "explore";
type NoisePreset = "noiseless" | "small_noise";
const DEFAULT_SCENARIO_ID = "SCENARIO_BO_1D_EXPLORE_NOISELESS";

async function json(url: string): Promise<unknown> {
  const response = await fetch(url);
  if (!response.ok)
    throw new Error(`${url} の読み込みに失敗しました (${response.status})。`);
  return response.json();
}

export function BayesianOptimizationPage() {
  const { scenarioId = "" } = useParams();
  const requestedScenarioId = scenarioId || DEFAULT_SCENARIO_ID;
  const location = useLocation();
  const navigate = useNavigate();
  const [loaded, setLoaded] = useState<{
    scenario: VisualizationScenario;
    payload: SurrogateUncertaintyPayload;
  }>();
  const [error, setError] = useState<Error>();
  useEffect(() => {
    const controller = new AbortController();
    setLoaded(undefined);
    setError(undefined);
    void (async () => {
      const base = `${siteBaseUrl()}data/`;
      const manifest = parseSiteManifest(await json(`${base}manifest.json`));
      const index = parseVisualizationScenarioIndex(
        await json(`${base}${manifest.visualization_scenarios.path}`),
      );
      if (index.dataset_version !== manifest.dataset_version)
        throw new Error(
          "VisualizationScenario indexのdataset versionが一致しません。",
        );
      const scenario = index.scenarios.find(
        (item) => item.scenario_id === requestedScenarioId,
      );
      if (!scenario)
        throw new EntityNotFoundError("Bayesian Optimization scenario ID", requestedScenarioId);
      if (
        scenario.artifact.renderer_family !== "surrogate_uncertainty" ||
        scenario.artifact.artifact_contract !== "SurrogateUncertainty"
      )
        throw new Error("BO scenarioのrenderer契約が一致しません。");
      const payload = parseSurrogateUncertaintyPayload(
        await json(`${base}${scenario.artifact.payload_path}`),
      );
      const payloadPresetId = `BO_${payload.strategy.toUpperCase()}_${payload.noise_preset.toUpperCase()}`;
      if (scenario.experiment.parameter_preset_id !== payloadPresetId)
        throw new Error("renderer payloadのpresetがscenarioと一致しません。");
      if (
        payload.frames.at(-1)?.oracle_evaluations !==
        scenario.experiment.budget.value
      )
        throw new Error("renderer payloadの評価予算がscenarioと一致しません。");
      if (!controller.signal.aborted) setLoaded({ scenario, payload });
    })().catch((caught: unknown) => {
      if (!controller.signal.aborted)
        setError(caught instanceof Error ? caught : new Error(String(caught)));
    });
    return () => controller.abort();
  }, [requestedScenarioId]);
  if (error instanceof EntityNotFoundError) return <NotFoundPage detail={error.message} />;
  const strategy: Strategy = loaded?.payload.strategy ?? "explore";
  const noise: NoisePreset = loaded?.payload.noise_preset ?? "noiseless";
  const selectScenario = (nextStrategy: Strategy, nextNoise: NoisePreset) => {
    const nextId = `SCENARIO_BO_1D_${nextStrategy.toUpperCase()}_${nextNoise.toUpperCase()}`;
    const pathname = `/theater/bayesian-optimization/${nextId}`;
    const state = atlasStateFromSearch(location.search);
    const nextState = state ? patchJourneyState(state, { scenarioId: nextId }) : undefined;
    const destination = nextState
      ? buildAtlasNavigation(pathname, location.search, nextState)
      : undefined;
    navigate(destination?.ok ? destination.to : pathname);
  };
  return (
    <section className="atlas-page bo-theater">
      <header className="atlas-page-header">
        <p className="eyebrow">Method Theater · Executable Trace</p>
        <h1>Bayesian Optimization Theater</h1>
        <p>
          高価なblack-boxを、観測 → surrogate更新 → Expected
          Improvementで次点選択、の順に再生します。
        </p>
      </header>
      <div className="bo-presets" aria-label="実験preset">
        <label>
          探索方針
          <select
            aria-label="探索方針"
            value={strategy}
            onChange={(event) => selectScenario(event.target.value as Strategy, noise)}
          >
            <option value="exploit">活用寄り (exploit)</option>
            <option value="explore">探索寄り (explore)</option>
          </select>
        </label>
        <label>
          観測noise
          <select
            aria-label="観測noise"
            value={noise}
            onChange={(event) => selectScenario(strategy, event.target.value as NoisePreset)}
          >
            <option value="noiseless">noiseなし</option>
            <option value="small_noise">小さいnoise</option>
          </select>
        </label>
      </div>
      {error && (
        <p role="alert" className="atlas-error">
          {error.message}
        </p>
      )}
      {!loaded && !error && (
        <p role="status">生成済みscenarioを検証しています…</p>
      )}
      {loaded && (
        <Theater
          key={loaded.scenario.scenario_id}
          scenario={loaded.scenario}
          payload={loaded.payload}
        />
      )}
    </section>
  );
}

function Theater({
  scenario,
  payload,
}: {
  scenario: VisualizationScenario;
  payload: SurrogateUncertaintyPayload;
}) {
  const links = useEntityLinks();
  const [frameIndex, setFrameIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState<GuidedPlaybackSpeed>(1);
  const [guidedStep, setGuidedStep] = useState<GuidedStoryStep | null>(null);
  const root = useRef<HTMLDivElement>(null);
  const frame = payload.frames[frameIndex];
  useEffect(() => {
    if (!playing) return;
    const timer = window.setInterval(
      () =>
        setFrameIndex((current) => {
          if (current >= payload.frames.length - 1) {
            setPlaying(false);
            return current;
          }
          return current + 1;
        }),
      850 / speed,
    );
    return () => window.clearInterval(timer);
  }, [playing, payload.frames.length, speed]);
  const move = (delta: number) => {
    setPlaying(false);
    setFrameIndex((current) =>
      Math.max(0, Math.min(payload.frames.length - 1, current + delta)),
    );
  };
  const onKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === "ArrowLeft") {
      event.preventDefault();
      move(-1);
    }
    if (event.key === "ArrowRight") {
      event.preventDefault();
      move(1);
    }
    if (event.key === " ") {
      event.preventDefault();
      setPlaying((value) => !value);
    }
  };
  const boHistory = payload.frames.map((item) => item.incumbent_value);
  const randomHistory = payload.random_history.map((_, index) =>
    Math.min(
      ...payload.random_history
        .slice(0, index + 1)
        .map((item) => item.observed_value),
    ),
  );
  const method =
    links.status === "ready"
      ? findEntity(links.index, "method", "M_BAYESIAN_OPT_GP")
      : undefined;
  const baseline =
    links.status === "ready"
      ? findEntity(links.index, "method", "M_RANDOM_SEARCH")
      : undefined;
  const budget = scenario.experiment.budget.value;
  const guidedPlayback: GuidedPlaybackController = {
    currentFrameIndex: frameIndex,
    isPlaying: playing,
    pause: () => setPlaying(false),
    seekToFrameAtSpeed: (nextFrameIndex, nextSpeed) => {
      setPlaying(false);
      setSpeed(nextSpeed);
      setFrameIndex(Math.max(0, Math.min(payload.frames.length - 1, nextFrameIndex)));
    },
  };
  const visibleLayers = new Set(guidedStep?.visible_layers ?? scenario.artifact.observable_ids);
  return (
    <div
      ref={root}
      tabIndex={0}
      onKeyDown={onKeyDown}
      className="bo-player"
      aria-label="Bayesian optimization再生領域。左右矢印で移動、Spaceで再生"
    >
      <section className="bo-contract">
        <strong>
          {scenario.artifact.artifact_kind} ·{" "}
          {scenario.artifact.renderer_family}{" "}
          {scenario.artifact.renderer_contract_version}
        </strong>
        <span>方向 / Direction: minimize（best valueが小さいほど良い）</span>
        <span>
          seed {scenario.experiment.seed.value} · 初期点{" "}
          {scenario.experiment.initial_condition.point.join(", ")} · noise σ=
          {payload.noise_std}
        </span>
        <span>
          評価 {frame.oracle_evaluations}/{budget} · ξ={payload.exploration_xi}
        </span>
      </section>
      <ScenarioContextPanel scenario={scenario} />
      <ScenarioLessonPanel scenario={scenario} />
      <GuidedStoryPanel
        activeStep={guidedStep}
        onStepChange={setGuidedStep}
        playback={guidedPlayback}
        scenario={scenario}
      />
      <section className="bo-goal-cues" aria-label="BOの目標と現在値">
        <dl>
          <div>
            <dt>Initial design</dt>
            <dd>[{scenario.experiment.initial_condition.point.join(", ")}]</dd>
          </div>
          <div>
            <dt>Current incumbent</dt>
            <dd>
              x={frame.incumbent_x.toFixed(3)} · y=
              {frame.incumbent_value.toFixed(3)}
            </dd>
          </div>
          <div>
            <dt>Known optimum</dt>
            <dd>{scenario.lesson.known_reference_display.note_ja}</dd>
          </div>
          <div>
            <dt>Terminal</dt>
            <dd>
              {frame.oracle_evaluations >= budget
                ? "evaluation budget reached"
                : "ongoing"}
            </dd>
          </div>
        </dl>
      </section>
      <div className="bo-playback" role="group" aria-label="再生コントロール">
        <button
          type="button"
          aria-label="1フレーム戻る"
          disabled={frameIndex === 0}
          onClick={() => move(-1)}
        >
          ←
        </button>
        <button type="button" onClick={() => setPlaying((value) => !value)}>
          {playing ? "一時停止" : "再生"}
        </button>
        <button
          type="button"
          aria-label="1フレーム進む"
          disabled={frameIndex === payload.frames.length - 1}
          onClick={() => move(1)}
        >
          →
        </button>
        <label>
          評価位置{" "}
          <input
            aria-label="評価位置"
            type="range"
            min={0}
            max={payload.frames.length - 1}
            value={frameIndex}
            onChange={(event) => {
              setPlaying(false);
              setFrameIndex(Number(event.target.value));
            }}
          />
        </label>
        <span aria-live="polite">
          Frame {frameIndex + 1}/{payload.frames.length} · {speed}×
        </span>
      </div>
      <div
        className="bo-layout"
        data-guided-focus={guidedStep?.focus_target}
        data-viewport-preset={guidedStep?.viewport_preset}
      >
        <SurrogatePlot frame={frame} visibleLayers={visibleLayers} />
        <aside className="bo-explanation">
          <h2>なぜこの点？</h2>
          <p aria-live="polite">{frame.explanation_ja}</p>
          {frame.selected_point !== null && (
            <dl>
              <div>
                <dt>next x</dt>
                <dd>{frame.selected_point.toFixed(3)}</dd>
              </div>
              <div>
                <dt>Expected Improvement</dt>
                <dd>{frame.selected_acquisition?.toFixed(4)}</dd>
              </div>
              <div>
                <dt>予測不確実性 (1.96σ)</dt>
                <dd>{frame.selected_uncertainty?.toFixed(3)}</dd>
              </div>
              <div>
                <dt>incumbent</dt>
                <dd>
                  x={frame.incumbent_x.toFixed(2)}, y=
                  {frame.incumbent_value.toFixed(3)}
                </dd>
              </div>
            </dl>
          )}
          <p className="atlas-note">{payload.truth_disclosure_ja}</p>
        </aside>
      </div>
      {visibleLayers.has("incumbent_history") && <Comparison
        boHistory={boHistory}
        randomHistory={randomHistory}
        count={frame.oracle_evaluations}
        budget={budget}
      />}
      <details className="bo-text-alternative">
        <summary>図のテキスト代替</summary>
        <p>
          観測点は
          {frame.observations
            .map(
              (item) =>
                `x=${item.x.toFixed(2)}でy=${item.observed_value.toFixed(3)}`,
            )
            .join("、")}
          です。
        </p>
        <p>{frame.explanation_ja}</p>
        <p>
          同じ評価回数で、BOの最良値は{frame.incumbent_value.toFixed(3)}、random
          searchは{frame.random_incumbent_value.toFixed(3)}です。
        </p>
      </details>
      <section className="bo-limitations">
        <h2>この可視化の限界</h2>
        <p>{scenario.lesson.limitations_ja}</p>
        <p>
          Fairness: 同じ目的関数・domain・seed・評価予算 {budget}
          。比較線は優越性の証明ではなく、この固定runの履歴です。
        </p>
        <p>
          {method?.canonical_url ? (
            <Link className="text-link" to={method.canonical_url}>
              {method.label}
            </Link>
          ) : (
            "M_BAYESIAN_OPT_GP"
          )}{" "}
          <span aria-hidden="true">·</span>{" "}
          {baseline?.canonical_url ? (
            <Link className="text-link" to={baseline.canonical_url}>
              {baseline.label}
            </Link>
          ) : (
            "M_RANDOM_SEARCH"
          )}
        </p>
        <EvidenceLinks sourceIds={scenario.source_ids} />
      </section>
    </div>
  );
}

function Comparison({
  boHistory,
  randomHistory,
  count,
  budget,
}: {
  boHistory: number[];
  randomHistory: number[];
  count: number;
  budget: number;
}) {
  const rows = Array.from({ length: Math.max(0, count - 2) }, (_, index) => {
    const evaluation = index + 3;
    return {
      evaluation,
      bo: boHistory[index],
      random: randomHistory[evaluation - 1],
    };
  });
  return (
    <section className="bo-comparison">
      <h2>Equal-budget comparison</h2>
      <p>
        共通の初期設計3点から、評価回数を同じ {budget} 回に固定したrandom search
        baseline。
      </p>
      <div className="bo-score">
        <strong>BO {rows.at(-1)?.bo.toFixed(3)}</strong>
        <span>vs</span>
        <strong>Random {rows.at(-1)?.random.toFixed(3)}</strong>
      </div>
      <table>
        <caption>評価ごとのbest-so-far（小さいほど良い）</caption>
        <thead>
          <tr>
            <th>評価</th>
            <th>BO</th>
            <th>Random</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.evaluation}>
              <td>{row.evaluation}</td>
              <td>{row.bo.toFixed(3)}</td>
              <td>{row.random.toFixed(3)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
