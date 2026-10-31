import { useEffect, useRef, useState } from "react";

import type { SurrogateFrame } from "../../contracts/surrogate-uncertainty";
import {
  AcquisitionStrip,
  EvaluationMarks,
  ModelCurve,
  ProposalMarker,
  RangeBand,
  stageScale,
  TerrainLine,
} from "../../visual-system";

const ACQUISITION_HEIGHT = 46;

/**
 * A recorded surrogate frame drawn with the shared Search Stage marks, so the canonical BO
 * Theater, its comparisons, and the algorithm-view Theater read the same way: teal band and
 * line for the model, teal circles for observations, orange for the next proposal and the
 * acquisition, dashed grey for the teaching objective that the optimizer never sees.
 */
export function SurrogatePlot({
  frame,
  visibleLayers,
}: {
  frame: SurrogateFrame;
  visibleLayers: ReadonlySet<string>;
}) {
  const ref = useRef<HTMLElement>(null);
  const [width, setWidth] = useState(640);
  useEffect(() => {
    const element = ref.current;
    if (!element) return undefined;
    const measure = () => { if (element.clientWidth > 0) setWidth(Math.round(element.clientWidth)); };
    measure();
    if (typeof ResizeObserver === "undefined") return undefined;
    const observer = new ResizeObserver(measure);
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  const points = frame.predictive_summary;
  const xs = points.map((point) => point.x);
  const minY = Math.min(...points.flatMap((point) => [point.lower, point.true_value]));
  const maxY = Math.max(...points.flatMap((point) => [point.upper, point.true_value]));
  const xDomain: readonly [number, number] = [Math.min(...xs), Math.max(...xs)];
  const stageHeight = Math.round(Math.min(300, Math.max(200, width * 0.42)));
  const height = stageHeight + ACQUISITION_HEIGHT + 22;
  const pad = (maxY - minY || 1) * 0.06;
  const scale = stageScale(width, stageHeight, xDomain, [minY - pad, maxY + pad], { left: 10, right: 10, top: 30, bottom: 18 });

  return (
    <figure className="bo-figure vs-surrogate-figure" ref={ref}>
      <svg
        aria-labelledby="bo-plot-title bo-plot-desc"
        className="vs-stage"
        height={height}
        role="img"
        width={width}
      >
        <title id="bo-plot-title">surrogateの平均、不確実性、観測、Expected Improvement</title>
        <desc id="bo-plot-desc">
          上段は教材用の真の目的関数を灰色の破線、surrogateの予測平均を青緑の線、不確実性を青緑の帯、観測を丸で示します。下段は獲得関数で、橙の縦線が次の候補です。
        </desc>
        {visibleLayers.has("posterior_uncertainty") && (
          <RangeBand lower={points.map((point) => point.lower)} scale={scale} upper={points.map((point) => point.upper)} xs={xs} />
        )}
        <TerrainLine scale={scale} xs={xs} ys={points.map((point) => point.true_value)} />
        {visibleLayers.has("posterior_mean") && <ModelCurve scale={scale} xs={xs} ys={points.map((point) => point.mean)} />}
        {visibleLayers.has("observations") && (
          <EvaluationMarks
            points={frame.observations.map((point, index) => ({
              key: `${point.x}:${index}`,
              x: point.x,
              y: point.observed_value,
              latest: index === frame.observations.length - 1,
            }))}
            scale={scale}
            shape="circle"
          />
        )}
        {visibleLayers.has("selected_candidate") && frame.selected_point !== null && (
          <ProposalMarker scale={scale} x={frame.selected_point} />
        )}
        {visibleLayers.has("expected_improvement") && (
          <AcquisitionStrip
            height={ACQUISITION_HEIGHT - 6}
            label="Expected Improvement"
            next={visibleLayers.has("selected_candidate") ? frame.selected_point : null}
            scale={scale}
            top={stageHeight + 14}
            values={points.map((point) => point.acquisition)}
            xs={xs}
          />
        )}
        <text className="vs-stage-label" x={10} y={18}>目的関数 / surrogate</text>
      </svg>
      <ul className="vs-legend bo-figure-legend" aria-label="記号の読み方">
        <li><span className="vs-legend-line" aria-hidden="true" />surrogate平均（不確実性の帯つき）</li>
        <li><span className="vs-legend-line is-terrain" aria-hidden="true" />真の目的関数（教材の答え合わせ用）</li>
        <li><span className="vs-legend-dot" aria-hidden="true" />観測値</li>
        <li><span className="vs-legend-line is-proposal" aria-hidden="true" />次の候補</li>
      </ul>
      <figcaption>
        surrogateの予測（青緑）と教材用の真の目的関数（灰色の破線）は別物です。optimizerは観測点以外の真の値を参照しません。
      </figcaption>
    </figure>
  );
}
