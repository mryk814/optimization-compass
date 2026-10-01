import { useEffect } from "react";
import { Link, useParams } from "react-router-dom";

import { stepKey, type LearningPath, type LearningPathStep } from "../../contracts/learning-paths";
import { EntityNotFoundError, NotFoundPage } from "../navigation/NotFoundPage";
import { rememberActivePath, usePathProgress } from "./path-progress";
import { usePaths } from "./use-paths";

import "./paths.css";

function ProgressMeter({ done, total }: { done: number; total: number }) {
  return (
    <div className="path-meter">
      <progress max={total} value={done}>{done} / {total}</progress>
      <span>{done} / {total} ステップ</span>
    </div>
  );
}

function nextStep(path: LearningPath, isDone: (pathId: string, key: string) => boolean): LearningPathStep {
  return path.steps.find((step) => !isDone(path.path_id, stepKey(step))) ?? path.steps[0];
}

export function PathIndexPage() {
  const { paths, error } = usePaths();
  const { doneCount, isDone } = usePathProgress();
  useEffect(() => {
    document.title = "学ぶ道筋 | Optimization Compass";
  }, []);
  return (
    <section className="atlas-page path-index">
      <header className="path-index-header">
        <p className="eyebrow">道筋</p>
        <h1>学ぶ道筋</h1>
        <p>
          一つの問いに答えると、次の問いが見えてきます。
          道筋は、定式化と手法の解説を「問い」でつないだ順路です。どこから読み始めても、進み具合はこのブラウザに残ります。
        </p>
      </header>
      {error && <p className="atlas-error" role="alert">{error.message}</p>}
      {!paths && !error && <p role="status">道筋を読み込んでいます…</p>}
      <div className="path-card-grid">
        {paths?.paths.map((path) => {
          const done = Math.min(doneCount(path.path_id), path.steps.length);
          const next = nextStep(path, isDone);
          return (
            <article className="path-card" key={path.path_id}>
              <h2><Link to={path.route}>{path.title_ja}</Link></h2>
              <p>{path.summary_ja}</p>
              <p className="path-card-audience">対象: {path.audience_ja}</p>
              <ProgressMeter done={done} total={path.steps.length} />
              <p className="path-card-next">
                <span>{done === 0 ? "最初の問い" : "次の問い"}</span>
                {next.question_ja}
              </p>
              <Link className="path-primary-action" onClick={() => rememberActivePath(path.path_id)} to={next.route}>
                {done === 0 ? "はじめる" : "続きから"} →
              </Link>
            </article>
          );
        })}
      </div>
    </section>
  );
}

export function PathPage() {
  const { pathId = "" } = useParams();
  const { paths, error } = usePaths();
  const { isDone, setDone, doneCount } = usePathProgress();
  const path = paths?.paths.find((item) => item.path_id === pathId);

  useEffect(() => {
    if (!path) return;
    document.title = `${path.title_ja} | 学ぶ道筋 | Optimization Compass`;
    rememberActivePath(path.path_id);
  }, [path]);

  if (paths && !path) return <NotFoundPage detail={new EntityNotFoundError("道筋ID", pathId).message} />;
  if (!path) {
    return (
      <section className="atlas-page path-detail">
        {error ? <p className="atlas-error" role="alert">{error.message}</p> : <p role="status">道筋を読み込んでいます…</p>}
      </section>
    );
  }
  const done = Math.min(doneCount(path.path_id), path.steps.length);
  const next = nextStep(path, isDone);
  return (
    <article className="atlas-page path-detail">
      <header className="path-hero">
        <p className="eyebrow"><Link to="/paths">学ぶ道筋</Link></p>
        <h1>{path.title_ja}</h1>
        <p>{path.summary_ja}</p>
        <dl className="path-contract">
          <div><dt>終えるとできること</dt><dd>{path.goal_ja}</dd></div>
          <div><dt>想定する読者</dt><dd>{path.audience_ja}</dd></div>
        </dl>
        <ProgressMeter done={done} total={path.steps.length} />
        <Link className="path-primary-action" to={next.route}>
          {done === 0 ? "最初の問いへ" : "次の問いへ"}: {next.title_ja} →
        </Link>
      </header>
      <ol className="path-steps">
        {path.steps.map((step) => {
          const key = stepKey(step);
          const complete = isDone(path.path_id, key);
          return (
            <li className={complete ? "path-step path-step-done" : "path-step"} key={key}>
              <span aria-hidden="true" className="path-step-number">{complete ? "✓" : step.step}</span>
              <div>
                <p className="path-step-question">{step.question_ja}</p>
                <p className="path-step-target">
                  <Link to={step.route}>{step.title_ja}</Link>
                  <span>{step.target_type === "formulation" ? "定式化" : "解説"}</span>
                  {!step.has_article && <span className="path-step-stub">標準形のみ・解説は準備中</span>}
                </p>
              </div>
              <label className="path-step-check">
                <input
                  checked={complete}
                  onChange={(event) => setDone(path.path_id, key, event.target.checked)}
                  type="checkbox"
                />
                読んだ
              </label>
            </li>
          );
        })}
      </ol>
    </article>
  );
}
