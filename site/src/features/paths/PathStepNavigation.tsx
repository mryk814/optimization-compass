import { Link, useLocation } from "react-router-dom";

import { stepKey, stepsAtRoute } from "../../contracts/learning-paths";
import { readActivePath, rememberActivePath, usePathProgress } from "./path-progress";
import { usePaths } from "./use-paths";

import "./paths.css";

/**
 * Shown on any page that is a step of a path: a compact position bar above the page and a
 * "next question" card below it. Pages do not need to know that paths exist.
 */
export function PathStepNavigation({ placement }: { placement: "top" | "bottom" }) {
  const { pathname } = useLocation();
  const { paths } = usePaths();
  const { isDone, setDone } = usePathProgress();
  if (!paths) return null;
  const matches = stepsAtRoute(paths, pathname);
  if (matches.length === 0) return null;
  const active = readActivePath();
  const { path, step } = matches.find((item) => item.path.path_id === active) ?? matches[0];
  const index = step.step - 1;
  const previous = path.steps[index - 1];
  const following = path.steps[index + 1];
  const key = stepKey(step);
  const complete = isDone(path.path_id, key);

  if (placement === "top") {
    return (
      <nav aria-label="学ぶ道筋での位置" className="path-position">
        <Link to={path.route}>道筋「{path.title_ja}」</Link>
        <span>{step.step} / {path.steps.length}</span>
        <p>この項の問い: {step.question_ja}</p>
      </nav>
    );
  }
  return (
    <aside aria-label="道筋の次の一歩" className="path-next-card">
      <label className="path-step-check">
        <input
          checked={complete}
          onChange={(event) => setDone(path.path_id, key, event.target.checked)}
          type="checkbox"
        />
        この問いに答えられるようになった
      </label>
      {following ? (
        <Link
          className="path-next-link"
          onClick={() => { setDone(path.path_id, key, true); rememberActivePath(path.path_id); }}
          to={following.route}
        >
          <span>次の問い（{following.step} / {path.steps.length}）</span>
          <strong>{following.question_ja}</strong>
          <small>{following.title_ja} →</small>
        </Link>
      ) : (
        <Link className="path-next-link" onClick={() => setDone(path.path_id, key, true)} to={path.route}>
          <span>道筋の最後の問いです</span>
          <strong>「{path.title_ja}」を振り返る</strong>
          <small>進み具合を見る →</small>
        </Link>
      )}
      {previous && <Link className="path-previous-link" to={previous.route}>← 前の問い: {previous.title_ja}</Link>}
    </aside>
  );
}
