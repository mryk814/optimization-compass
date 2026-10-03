import { useEffect, useMemo, useRef, useState } from "react";
import { PlayerBar, Slider } from "../explorable/controls";
import { useTimeline } from "../explorable/useTimeline";
import type { PhysicalSceneId } from "./catalog";
import { armDrawing, droneDrawing, topologyDrawing } from "./drawings";
import { Projection } from "./Projection";
import { SceneViewport } from "./SceneViewport";
import type { ArmData, DroneData, Metrics, TopologyData } from "./types";
import "../explorable/explorable.css";
import "./physical-scenes.css";

type Loaded = { id: "topology"; data: TopologyData } | { id: "arm"; data: ArmData } | { id: "drone"; data: DroneData };
async function loadScene(id: PhysicalSceneId): Promise<Loaded> {
  if (id === "topology") return { id, data: (await import("./data/topology.json")).default as unknown as TopologyData };
  if (id === "arm") return { id, data: (await import("./data/arm.json")).default as unknown as ArmData };
  return { id, data: (await import("./data/drone.json")).default as unknown as DroneData };
}

export function useLoadedScene(id?: PhysicalSceneId) {
  const [loaded, setLoaded] = useState<Loaded>();
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    setError("");
    if (id) void loadScene(id).then(result => { if (active) setLoaded(result); }, () => {
      if (active) setError("計算結果を読み込めませんでした。ページを再読み込みしてください。");
    });
    return () => { active = false; };
  }, [id]);
  return { loaded, error };
}

export function ScenePlayer({ scene, embedded = false }: { scene: Loaded; embedded?: boolean }) {
  const [variant, setVariant] = useState(scene.id === "topology" ? 1 : 0);
  const [threshold, setThreshold] = useState(0.2);
  const [deformation, setDeformation] = useState(false);
  const [compare, setCompare] = useState(false);
  const variants = scene.data.variants;
  const run = variants[variant];
  const firstFrame = run.frames[0]; const lastFrame = run.frames[run.frames.length - 1];
  const duration = "time" in firstFrame && "time" in lastFrame ? lastFrame.time - firstFrame.time : 0;
  const timeline = useTimeline(run.frames.length - 1, duration > 0 ? (run.frames.length - 1) / duration : 2);
  const previousVariant = useRef<number | undefined>(undefined);
  useEffect(() => {
    if (previousVariant.current === variant) return;
    const first = previousVariant.current === undefined;
    previousVariant.current = variant;
    if (timeline.reducedMotion || scene.id === "topology" && first) timeline.finish();
    else if (first) timeline.seek(Math.floor(timeline.length * 0.4));
    else timeline.restart();
  }, [variant, scene.id, timeline]);
  const step = Math.min(timeline.step, run.frames.length - 1);
  const drawing = useMemo(() => scene.id === "topology"
    ? topologyDrawing(scene.data, variant, step, threshold, deformation)
    : scene.id === "arm" ? armDrawing(scene.data, variant, step, compare)
      : droneDrawing(scene.data, variant, step, compare), [scene, variant, step, threshold, deformation, compare]);
  const position = scene.id === "topology" ? `反復 ${scene.data.variants[variant].frames[step].iteration}`
    : `${scene.data.variants[variant].frames[step].time.toFixed(2)} 秒`;
  const summary = `${run.label}。${scene.id === "topology" ? "材料配置" : "軌道"}の計算済み結果を再生します。`;
  return <>
    <div className="physical-controls">
      <label>計算した条件<select aria-label="計算した条件" value={variant}
        onChange={event => { setVariant(Number(event.target.value)); setDeformation(false); }}>
        {variants.map((item, i) => <option value={i} key={item.id}>{item.label}</option>)}
      </select></label>
      {scene.id === "topology" ? <>
        <Slider label="表示する密度の下限" value={threshold} min={0.05} max={0.8} step={0.05}
          display={threshold.toFixed(2)} onChange={setThreshold} hint="表示だけを切り替えます。体積と目的値は元の密度場で計算しています。" />
        <label className="physical-check"><input type="checkbox" checked={deformation}
          disabled={!scene.data.variants[variant].frames[step].nodeDisplacements}
          onChange={event => setDeformation(event.target.checked)} />最終形の変形を重ねる</label>
      </> : <label className="physical-check"><input type="checkbox" checked={compare}
        onChange={event => setCompare(event.target.checked)} />もう一方の条件の軌道を重ねる</label>}
    </div>
    <div className="physical-stage-heading"><strong>{run.label}</strong><output aria-label="現在の時刻または反復">{position}</output></div>
    <div className="physical-stage">
      <SceneViewport drawing={drawing} label={`${scene.id === "topology" ? "材料配置" : "軌道"}の3D図`} />
      <div className="physical-side">
        <Projection drawing={drawing} />
        <CurrentReadout scene={scene} variant={variant} step={step} deformation={deformation} />
      </div>
    </div>
    <ul className="physical-legend" aria-label="図の凡例">
      <li><i className="physical-swatch accepted" />{scene.id === "topology" ? "3Dは密度の等値面／2Dは密度" : "実行した状態"}</li>
      <li><i className="physical-swatch update" />{scene.id === "topology" ? "荷重" : scene.id === "arm" ? "到達点／比較軌道" : "未来の予測"}</li>
      <li><i className="physical-swatch ghost" />{scene.id === "topology" ? "元の設計領域" : "参照／軌道の全体"}</li>
      {scene.id !== "topology" && <li><i className="physical-swatch obstacle" />障害物</li>}
    </ul>
    {scene.id === "topology" && <p className="physical-model-note">左面を固定し、右下端に荷重をかけています。変形表示は最大変位を高さの12%に揃えます。</p>}
    <p className="physical-sr-only" aria-live="polite">{summary}</p>
    <PlayerBar timeline={timeline} stepLabel={scene.id === "topology" ? "記録した反復" : "時刻"}
      positionText={`${position} ／ ${run.frames.length} コマ`} />
    {!embedded && <Reading scene={scene} variant={variant} step={step} />}
    {!embedded && <ResultComparison scene={scene} />}
    <details className="physical-details">
      <summary>計算の前提、検証結果、出典</summary>
      <p>{scene.data.model}</p>
      <ul>{scene.data.limitations.map(limit => <li key={limit}>{limit}</li>)}</ul>
      <p>条件を選ぶと、その条件で実際に計算した記録に切り替わります。選択肢の間の未計算の結果は補間しません。</p>
      <dl className="physical-diagnostics">{Object.entries(run.metrics).map(([key, value]) => <div key={key}><dt>{key}</dt><dd>{typeof value === "number" ? value.toPrecision(5) : String(value)}</dd></div>)}</dl>
      <ul>{scene.data.sources.map(source => <li key={source.url}><a href={source.url} target="_blank" rel="noreferrer">{source.title}</a></li>)}</ul>
    </details>
  </>;
}

function CurrentReadout({ scene, variant, step, deformation }: { scene: Loaded; variant: number; step: number; deformation: boolean }) {
  if (scene.id === "topology") {
    const frame = scene.data.variants[variant].frames[step];
    const initial = scene.data.variants[variant].frames[0].compliance;
    const factor = scene.data.grid[1] * scene.data.spacing[1] * 0.12 / Math.max(frame.maxDisplacement, 1e-12);
    return <dl className="physical-readout">
      <div><dt>材料の体積率</dt><dd>{(frame.volume * 100).toFixed(1)}%</dd></div>
      <div><dt>変形しやすさ（初期比）</dt><dd>{(frame.compliance / initial * 100).toFixed(1)}%</dd></div>
      <div><dt>平衡方程式の残差</dt><dd>{frame.residual.toExponential(1)}</dd></div>
      {deformation && frame.nodeDisplacements && <div><dt>表示用の変位倍率</dt><dd>{factor.toPrecision(3)}倍</dd></div>}
    </dl>;
  }
  if (scene.id === "arm") {
    const frame = scene.data.variants[variant].frames[step];
    return <dl className="physical-readout">
      <div><dt>腕と障害物の最小離隔</dt><dd>{(frame.clearance * 1000).toFixed(1)} mm</dd></div>
      <div><dt>旋回／肩／肘の角度</dt><dd>{frame.joints.map(value => (value * 180 / Math.PI).toFixed(0)).join(" / ")}°</dd></div>
    </dl>;
  }
  const frame = scene.data.variants[variant].frames[step];
  return <dl className="physical-readout">
    <div><dt>参照位置からのずれ</dt><dd>{frame.trackingError.toFixed(3)} m</dd></div>
    <div><dt>加速度の大きさ</dt><dd>{Math.hypot(...frame.acceleration).toFixed(2)} m/s²</dd></div>
    <div><dt>次に予測した点</dt><dd>{Math.max(0, frame.prediction.length - 1)}点</dd></div>
  </dl>;
}

function Reading({ scene, variant, step }: { scene: Loaded; variant: number; step: number }) {
  let values: number[]; let label: string; let text: string;
  if (scene.id === "topology") {
    const frames = scene.data.variants[variant].frames;
    values = frames.map(frame => frame.compliance / frames[0].compliance * 100);
    label = "変形しやすさ（初期を100%）";
    text = "同じ量の材料を置き直すことで、荷重に対する変形を小さくします。形を見るときは、固定面と荷重の間に残る材料を追ってください。格子は16×8×6要素です。";
  } else if (scene.id === "arm") {
    values = scene.data.variants[variant].frames.map(frame => frame.clearance * 1000);
    label = "腕全体と障害物の最小離隔（mm）";
    text = "到達点は同じでも、関節の動きを滑らかにする重みで通り道が変わります。再生を止めて、手先だけでなく肘とリンクも障害物を避けているかを見てください。";
  } else {
    values = scene.data.variants[variant].frames.map(frame => frame.trackingError);
    label = "参照軌道からのずれ（m）";
    text = "橙の線は、この時刻に最適化した未来です。その先頭の入力だけを実行し、次の時刻で解き直します。再生を最初に戻すと、青緑の実行軌道が橙の予測の先へ伸びる様子を追えます。";
  }
  const max = Math.max(...values) * 1.1 || 1;
  const x = (i: number) => 45 + i / Math.max(1, values.length - 1) * 630;
  const y = (value: number) => 115 - value / max * 88;
  return <section className="physical-reading" aria-label="計算結果の読み方">
    <p>{text}</p>
    <figure><figcaption>{label}</figcaption><svg viewBox="0 0 700 145" role="img" aria-label={label}>
      <line x1="45" y1="115" x2="675" y2="115" stroke="#c5d4d8" />
      <polyline points={values.map((value, i) => `${x(i)},${y(value)}`).join(" ")} stroke="#177e82" strokeWidth="2" fill="none" />
      <line x1={x(step)} x2={x(step)} y1="22" y2="115" stroke="#cc7728" strokeDasharray="4 4" />
      <circle cx={x(step)} cy={y(values[step])} r="4" fill="#cc7728" />
    </svg><div className="physical-chart-labels"><span>開始</span><span>縦軸 0〜{max.toFixed(1)}</span><span>終了</span></div></figure>
  </section>;
}

function numeric(metrics: Metrics, key: string) { return Number(metrics[key]); }
function ResultComparison({ scene }: { scene: Loaded }) {
  const columns = scene.id === "topology"
    ? [{ key: "finalCompliance", label: "変形しやすさ", digits: 2, unit: "" }, { key: "complianceReduction", label: "初期からの低減", digits: 1, unit: "%", multiplier: 100 }]
    : scene.id === "arm" ? [{ key: "tipTravel", label: "手先の距離（節点近似）", digits: 2, unit: "m" }, { key: "maxVelocity", label: "最大関節速度", digits: 2, unit: "rad/s" }]
      : [{ key: "rmsTrackingError", label: "追従誤差 RMS", digits: 3, unit: "m" }, { key: "maxAcceleration", label: "最大加速度", digits: 2, unit: "m/s²" }];
  return <section className="physical-comparison" aria-label="条件ごとの計算結果">
    <h2>条件ごとの結果</h2>
    <div className="physical-table-wrap"><table><thead><tr><th scope="col">計算した条件</th>{columns.map(column => <th key={column.key} scope="col">{column.label}</th>)}</tr></thead>
      <tbody>{scene.data.variants.map(run => <tr key={run.id}><th scope="row">{run.label}</th>{columns.map(column => <td key={column.key}>{(numeric(run.metrics, column.key) * ("multiplier" in column ? column.multiplier ?? 1 : 1)).toFixed(column.digits)} {column.unit}</td>)}</tr>)}</tbody>
    </table></div>
    <p>{scene.id === "topology" ? "同じ領域と荷重で、使用できる材料量を変えています。各条件を100反復で止めた結果です。" : "同じ問題の費用の重みを変えた結果です。目的関数が異なるため、値による手法の順位付けはしません。"}</p>
  </section>;
}
