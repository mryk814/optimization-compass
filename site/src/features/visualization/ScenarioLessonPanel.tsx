import type { VisualizationScenario } from "../../contracts/visualization-scenarios";

interface ScenarioLessonPanelProps {
  scenario: VisualizationScenario;
  showNarration?: boolean;
}

export function ScenarioLessonPanel({ scenario, showNarration = true }: ScenarioLessonPanelProps) {
  const lesson = scenario.lesson;
  return (
    <section className="scenario-lesson-panel" aria-labelledby={`lesson-${scenario.scenario_id}`}>
      <p className="eyebrow">見るポイント (Reading cues)</p>
      <h2 id={`lesson-${scenario.scenario_id}`}>{lesson.learning_objective.ja}</h2>
      <p>{lesson.expected_phenomenon_ja}</p>
      {lesson.misconception && (
        <p className="scenario-misconception">
          <strong>解く誤解:</strong> {lesson.misconception.ja}
        </p>
      )}
      <dl className="scenario-observables">
        <div>
          <dt>主に観測する値 (Primary observables)</dt>
          <dd>{lesson.primary_observables.map((item) => item.label_ja).join(" · ")}</dd>
        </div>
        <div>
          <dt>うまくいったサイン (Success signals)</dt>
          <dd>{lesson.success_signals.map((item) => item.label_ja).join(" · ")}</dd>
        </div>
        {lesson.failure_signals.length > 0 && (
          <div>
            <dt>失敗・対比のサイン (Failure / contrast signals)</dt>
            <dd>{lesson.failure_signals.map((item) => item.label_ja).join(" · ")}</dd>
          </div>
        )}
      </dl>
      {showNarration && (
        <ol className="scenario-narration" aria-label="説明の節目">
          {lesson.narration_steps.map((step, index) => (
            <li key={step.milestone_id}>
              <small>{index + 1}</small>
              <span>{step.title_ja}</span>
            </li>
          ))}
        </ol>
      )}
      <details className="scenario-derived-text">
        <summary>静的要約・テキスト代替・キャプション</summary>
        <p><strong>要約:</strong> {scenarioStaticSummary(scenario)}</p>
        <p><strong>テキスト代替:</strong> {scenarioTextAlternative(scenario)}</p>
        <p><strong>キャプション:</strong> {scenarioDerivedMediaCaption(scenario)}</p>
      </details>
    </section>
  );
}

export function scenarioStaticSummary(scenario: VisualizationScenario): string {
  return scenario.lesson.static_summary.ja;
}

export function scenarioTextAlternative(scenario: VisualizationScenario): string {
  return scenario.lesson.text_alternative.ja;
}

export function scenarioDerivedMediaCaption(scenario: VisualizationScenario): string {
  return scenario.lesson.derived_media_caption.ja;
}
