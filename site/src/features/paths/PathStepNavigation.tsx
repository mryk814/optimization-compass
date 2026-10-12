import { Link, useLocation } from "react-router-dom";

import { stepKey, stepsAtRoute } from "../../contracts/learning-paths";
import { readActivePath, rememberActivePath, usePathProgress } from "./path-progress";
import { usePaths } from "./use-paths";

import "./paths.css";

/** Carried in router state when a reader follows a "つまずいたら" link, so the page they land on
 * can offer the way back to the step even if that page is not part of the path. */
interface StumbleReturn {
  pathTitle: string;
  stepNumber: number;
  stepTitle: string;
  route: string;
}

function readStumbleReturn(state: unknown): StumbleReturn | undefined {
  if (typeof state !== "object" || state === null || !("stumbleReturn" in state)) return undefined;
  const value = (state as { stumbleReturn: unknown }).stumbleReturn;
  if (typeof value !== "object" || value === null) return undefined;
  const item = value as Record<string, unknown>;
  if (
    typeof item.pathTitle !== "string" || typeof item.stepNumber !== "number"
    || typeof item.stepTitle !== "string" || typeof item.route !== "string"
    || !item.route.startsWith("/") || item.route.startsWith("//")
  ) return undefined;
  return item as unknown as StumbleReturn;
}

function ReturnToStep({ target }: { target: StumbleReturn }) {
  return (
    <Link className="path-return-link" to={target.route}>
      ← 道筋「{target.pathTitle}」の {target.stepNumber} 番目「{target.stepTitle}」へ帰る
    </Link>
  );
}

/**
 * Shown on any page that is a step of a path: a compact position bar above the page and a
 * "next question" card below it. Pages do not need to know that paths exist.
 */
export function PathStepNavigation({ placement }: { placement: "top" | "bottom" }) {
  const { pathname, state } = useLocation();
  const { paths } = usePaths();
  const { isDone, setDone } = usePathProgress();
  const stumbleReturn = readStumbleReturn(state);
  const returnHere = stumbleReturn && stumbleReturn.route !== pathname ? stumbleReturn : undefined;
  if (!paths) return null;
  const matches = stepsAtRoute(paths, pathname);
  if (matches.length === 0) {
    return placement === "top" && returnHere ? (
      <nav aria-label="学ぶ道筋へ帰る" className="path-position">
        <ReturnToStep target={returnHere} />
      </nav>
    ) : null;
  }
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
        {returnHere && <ReturnToStep target={returnHere} />}
        <Link to={path.route}>道筋「{path.title_ja}」</Link>
        <span>{step.step} / {path.steps.length}</span>
        <p>この項の問い: {step.question_ja}</p>
      </nav>
    );
  }
  const backHere: StumbleReturn = {
    pathTitle: path.title_ja,
    stepNumber: step.step,
    stepTitle: step.title_ja,
    route: step.route,
  };
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
      {step.stumbles.length > 0 && (
        <section aria-labelledby="path-stumbles-title" className="path-stumbles">
          <h2 id="path-stumbles-title">つまずいたら戻る</h2>
          <ul>
            {step.stumbles.map((stumble) => (
              <li key={`${stumble.target_type}:${stumble.target_id}`}>
                <Link
                  onClick={() => rememberActivePath(path.path_id)}
                  state={{ stumbleReturn: backHere }}
                  to={stumble.route}
                >
                  <span>{stumble.trouble_ja}</span>
                  <small>{stumble.title_ja} へ →</small>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}
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
