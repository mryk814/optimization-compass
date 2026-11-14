import {
  memo, useCallback, useEffect, useId, useMemo, useRef, useState, type PointerEvent as ReactPointerEvent,
} from "react";

import { Choice, PlayerBar, Slider } from "../../controls";
import { ExplorableFrame } from "../../ExplorableFrame";
import { EXPLORABLE_META } from "../../figureMeta";
import { fmt } from "../../format";
import { numberSetting, stringSetting, type BeatSettings, type ResolvedSettings } from "../../scene";
import { clamp, useStageViewport } from "../../svg";
import { useSceneTour } from "../../useSceneTour";
import { useTimeline } from "../../useTimeline";
import {
  BUDGET, DATA_X, DATA_Y, DEGREES, LOG_LAMS, RANDOM_BESTS, SEEDS, SPLITS,
  bestIndex, bestSoFar, curveValue, distinctLambdas, fitCoefficients, gridRun, lamIndexOf, mapScore,
  randomRun, shadeLevel, truth,
  type Placement, type RacePoint, type Score,
} from "./math";
import "./style.css";

const ID = "hpo-budget-race";
type Mode = "probe" | "race";
const MODES: readonly Mode[] = ["probe", "race"];
const PLACEMENTS: readonly Placement[] = ["edge", "center"];
const SCORES: readonly Score[] = ["cv", "fresh"];

interface Settings {
  mode: Mode;
  d: number;
  loglam: number;
  grid: Placement;
  split: number;
  score: Score;
  seed: number;
  /** Show where the best of 200 other random runs landed. */
  spread: boolean;
}

const INITIAL: Settings = {
  mode: "race", d: 3, loglam: -3.5, grid: "edge", split: 0, score: "cv", seed: 0, spread: false,
};

function fromValues(values: BeatSettings | ResolvedSettings, base: Settings): Settings {
  return {
    mode: stringSetting(values, "mode", MODES, base.mode),
    d: clamp(Math.round(numberSetting(values, "d", base.d)), DEGREES[0], DEGREES[DEGREES.length - 1]),
    loglam: LOG_LAMS[lamIndexOf(numberSetting(values, "loglam", base.loglam))],
    grid: stringSetting(values, "grid", PLACEMENTS, base.grid),
    split: clamp(Math.round(numberSetting(values, "split", base.split)), 0, SPLITS - 1),
    score: stringSetting(values, "score", SCORES, base.score),
    seed: clamp(Math.round(numberSetting(values, "seed", base.seed)), 0, SEEDS - 1),
    spread: stringSetting(values, "spread", ["off", "on"] as const, base.spread ? "on" : "off") === "on",
  };
}

/** Seconds the bars take to move from the score when chosen to the score on fresh points. */
const REVEAL_S = 1.6;
const GAP = 8;
const WIDE = 480;
const CURVE_Y: readonly [number, number] = [-2.5, 2.5];
const CURVE_SAMPLES = Array.from({ length: 81 }, (_, i) => -1 + i / 40);
const BEST_Y: readonly [number, number] = [Math.log10(0.12), Math.log10(0.9)];
const BAR_MAX = 0.22;

interface Rect { x: number; y: number; w: number; h: number }
interface MapBox extends Rect { left: number; cell: number; cellW: number; ticks: boolean }

const mapHeight = (cell: number) => 22 + DEGREES.length * cell + 12 + 18;

function mapBox(x: number, y: number, w: number, cell: number, ticks: boolean): MapBox {
  const left = ticks ? 26 : 6;
  return { x, y, w, h: mapHeight(cell), left, cell, cellW: (w - left - 4) / LOG_LAMS.length, ticks };
}

/** Pixel position of a setting on a map. log10 λ is continuous; the cells are centred on the lattice. */
function mapPoint(box: MapBox, d: number, logLam: number): [number, number] {
  return [
    box.x + box.left + ((logLam - LOG_LAMS[0]) / 0.5 + 0.5) * box.cellW,
    box.y + 22 + (DEGREES[DEGREES.length - 1] - d + 0.5) * box.cell,
  ];
}

const LOW = [0xee, 0xf0, 0xea];
const HIGH = [0x7c, 0x86, 0x7e];
function shade(value: number): string {
  const t = shadeLevel(value);
  return `rgb(${LOW.map((low, i) => Math.round(low + (HIGH[i] - low) * t)).join(" ")})`;
}

const settingText = (point: RacePoint) => `次数${point.d}、log₁₀λ ${fmt(point.log_lam, 2)}`;

export default function HpoBudgetRace() {
  const [chosen, setChosen] = useState<Settings>(INITIAL);
  const [showTruth, setShowTruth] = useState(false);
  const patch = (part: Partial<Settings>) => setChosen((value) => ({ ...value, ...part }));
  const tour = useSceneTour(
    ID,
    EXPLORABLE_META[ID].beats,
    useCallback((settings: BeatSettings) => setChosen((value) => fromValues(settings, value)), []),
  );
  const guided = tour.active;
  const { mode, d, loglam, grid, split, score, seed, spread } = guided ? fromValues(tour.values, chosen) : chosen;
  const svgRef = useRef<SVGSVGElement>(null);
  const clipId = useId();
  // Only the measured width is used; the panels are laid out below, one SVG unit per CSS pixel.
  const { ref: stageRef, viewport } = useStageViewport(STAGE_BOUNDS, 1);
  const width = viewport.width;
  const wide = width >= WIDE;

  // The reader's own race replays when they change what is raced; taking over from the lesson,
  // or going back to it, keeps the finished state that was on screen.
  const timeline = useTimeline(BUDGET, 2);
  const replayKey = guided ? "guided" : [mode, grid, seed].join("|");
  const lastKey = useRef<string | undefined>(undefined);
  useEffect(() => {
    if (lastKey.current === replayKey) return;
    const quiet = lastKey.current === undefined || lastKey.current === "guided" || replayKey === "guided"
      || timeline.reducedMotion || mode === "probe";
    lastKey.current = replayKey;
    if (quiet) timeline.finish();
    else timeline.restart();
  }, [replayKey]);

  const evals = guided ? numberSetting(tour.values, "evals", BUDGET) : timeline.position;
  const count = Math.min(BUDGET, Math.floor(evals + 1e-9));
  // The lesson step that re-places the grid sweeps `slide` from 0 to 1, so the grid is seen moving
  // there; the scores change when it arrives. Everywhere else the grid is simply where it is.
  const slide = guided && grid === "center" ? clamp(numberSetting(tour.values, "slide", 1), 0, 1) : 1;
  const reveal = score === "fresh" ? (guided ? clamp(tour.local / REVEAL_S, 0, 1) : 1) : 0;

  const gridPoints = gridRun(slide < 1 ? "edge" : grid);
  const randomPoints = randomRun(seed);
  const gridBest = bestIndex(gridPoints, count, split);
  const randomBest = bestIndex(randomPoints, count, split);
  const gridPlaces = useMemo(() => {
    if (slide >= 1) return gridPoints.map((point) => [point.d, point.log_lam] as const);
    const to = gridRun("center");
    return gridPoints.map((point, index) => [
      point.d + (to[index].d - point.d) * slide,
      point.log_lam + (to[index].log_lam - point.log_lam) * slide,
    ] as const);
  }, [gridPoints, slide]);
  const randomPlaces = useMemo(() => randomPoints.map((point) => [point.d, point.log_lam] as const), [randomPoints]);

  // Layout: probe = the map and the curve; race = two maps, their key, the curves, the best so far.
  const cell = mode === "probe" ? (wide ? 10 : 8) : (wide ? 9 : 8);
  const keyWidth = mode === "probe" && wide ? (width - GAP) / 2 : width;
  const keyRows = keyWidth >= 420 ? 1 : 2;
  const keyH = keyRows * 17 + 2;
  let maps: MapBox[];
  let curveBox: Rect;
  let bestBox: Rect | undefined;
  if (mode === "probe") {
    const half = (width - GAP) / 2;
    maps = [mapBox(0, 0, wide ? half : width, cell, true)];
    curveBox = wide
      ? { x: half + GAP, y: 0, w: half, h: maps[0].h + GAP + keyH }
      : { x: 0, y: maps[0].h + GAP + keyH + GAP, w: width, h: 150 };
  } else {
    // The right-hand map has no degree labels, so it is narrower by their width and the cells match.
    const leftW = (width - GAP + 20) / 2;
    maps = [mapBox(0, 0, leftW, cell, true), mapBox(leftW + GAP, 0, width - GAP - leftW, cell, false)];
    const top = maps[0].h + GAP + keyH + GAP;
    const half = (width - GAP) / 2;
    curveBox = wide ? { x: 0, y: top, w: half, h: 158 } : { x: 0, y: top, w: width, h: 128 };
    bestBox = wide ? { x: half + GAP, y: top, w: half, h: 158 } : { x: 0, y: top + 128 + GAP, w: width, h: 122 };
  }
  const keyY = maps[0].h + GAP;
  const height = Math.max(curveBox.y + curveBox.h, bestBox ? bestBox.y + bestBox.h : 0, keyY + keyH);

  const probeScore = mapScore(DEGREES.indexOf(d), lamIndexOf(loglam), score, split);
  const pickCell = (event: ReactPointerEvent<SVGRectElement>) => {
    const svg = svgRef.current;
    if (!svg) return;
    const box = svg.getBoundingClientRect();
    if (box.width === 0) return;
    const px = ((event.clientX - box.left) / box.width) * width;
    const py = ((event.clientY - box.top) / box.height) * height;
    const column = clamp(Math.floor((px - maps[0].x - maps[0].left) / maps[0].cellW), 0, LOG_LAMS.length - 1);
    const row = clamp(Math.floor((py - maps[0].y - 22) / maps[0].cell), 0, DEGREES.length - 1);
    patch({ d: DEGREES[DEGREES.length - 1] - row, loglam: LOG_LAMS[column] });
  };

  // Words for the result of the current settings (the finished race), not of each frame.
  const finalGrid = gridRun(grid);
  const finalGridBest = finalGrid[bestIndex(finalGrid, BUDGET, split)];
  const finalRandomBest = randomPoints[bestIndex(randomPoints, BUDGET, split)];
  const scoreName = score === "cv" ? "交差検証の点数" : "新しい5000点での点数";
  const summary = mode === "probe"
    ? `次数${d}、log10 λ が${fmt(loglam, 1)}の設定を1つ評価します。${scoreName}は${fmt(probeScore, 3)}です。`
    : [
        `評価16回を、格子（${grid === "edge" ? "両端を含む" : "各区間の中心"}）とランダム（乱数の種${seed}）で使います。`,
        `30点の分け方は${SPLITS}通りのうち${split + 1}番目です。`,
        `交差検証で選んだ最良は、格子が${fmt(finalGridBest.cv[split], 3)}（${settingText(finalGridBest)}）、`,
        `ランダムが${fmt(finalRandomBest.cv[split], 3)}（${settingText(finalRandomBest)}）です。`,
        `この2つの設定を新しい5000点で測ると、${fmt(finalGridBest.fresh, 3)}と${fmt(finalRandomBest.fresh, 3)}です。`,
      ].join("");

  const g = gridBest === -1 ? undefined : gridPoints[gridBest];
  const r = randomBest === -1 ? undefined : randomPoints[randomBest];

  return (
    <ExplorableFrame
      controls={
        <>
          <Choice<Mode>
            legend="見るもの"
            onChange={(value) => patch({ mode: value })}
            options={[{ value: "race", label: "16回の探索を2つ" }, { value: "probe", label: "設定を1つ" }]}
            value={mode}
          />
          {mode === "probe" ? (
            <>
              <Slider
                display={String(d)} label="次数" max={15} min={2} onChange={(value) => patch({ d: value })}
                step={1} value={d}
              />
              <Slider
                display={fmt(loglam, 1)}
                hint="地図のマスを押しても選べます。"
                label={<>罰則の強さ log₁₀ λ</>}
                max={1} min={-6} onChange={(value) => patch({ loglam: value })} step={0.5} value={loglam}
              />
            </>
          ) : (
            <>
              <Choice<Placement>
                legend="格子の置き方"
                onChange={(value) => patch({ grid: value })}
                options={[{ value: "edge", label: "両端を含む" }, { value: "center", label: "各区間の中心" }]}
                value={grid}
              />
              <Slider
                display={String(seed)} label="ランダムの乱数の種" max={SEEDS - 1} min={0}
                onChange={(value) => patch({ seed: value })} step={1} value={seed}
              />
            </>
          )}
          <Slider
            display={`${split + 1} / ${SPLITS}`}
            hint="交差検証で、30点を5組に分ける分け方です。"
            label="30点の分け方" max={SPLITS - 1} min={0}
            onChange={(value) => patch({ split: value })} step={1} value={split}
            valueText={`${SPLITS}通りのうち${split + 1}番目`}
          />
          <Choice<Score>
            legend="点数を測るデータ"
            onChange={(value) => patch({ score: value })}
            options={[{ value: "cv", label: "交差検証" }, { value: "fresh", label: "新しい5000点" }]}
            value={score}
          />
          <div className="hbr-checks">
            <label className="hbr-check">
              <input checked={showTruth} onChange={(event) => setShowTruth(event.target.checked)} type="checkbox" />
              真の曲線を重ねる
            </label>
            {mode === "race" && (
              <label className="hbr-check">
                <input checked={spread} onChange={(event) => patch({ spread: event.target.checked })} type="checkbox" />
                乱数を変えた200回の最良を重ねる
              </label>
            )}
          </div>
        </>
      }
      id={ID}
      player={mode === "race" ? (
        <PlayerBar positionText={`${count} / ${BUDGET} 回`} stepLabel="評価の回数" timeline={timeline} />
      ) : undefined}
      readout={
        <p className="hbr-readout">
          {mode === "probe" ? (
            <>次数 <strong>{d}</strong>、log₁₀λ <strong>{fmt(loglam, 1)}</strong> → 点数 <strong>{fmt(probeScore, 3)}</strong></>
          ) : !g || !r ? (
            <>まだ評価していません。</>
          ) : score === "fresh" ? (
            <>
              最良どうしの点数の差：選んだとき <strong>{fmt(Math.abs(g.cv[split] - r.cv[split]), 3)}</strong>
              {" "}→ 新しい5000点 <strong>{fmt(Math.abs(g.fresh - r.fresh), 3)}</strong>
            </>
          ) : (
            <>
              <span>格子の最良 <strong>{fmt(g.cv[split], 3)}</strong>（{settingText(g)}）</span>
              <span>ランダムの最良 <strong>{fmt(r.cv[split], 3)}</strong>（{settingText(r)}）</span>
            </>
          )}
        </p>
      }
      stage={
        <div className="ex-canvas" ref={stageRef}>
          <svg className="ex-svg hbr-svg" ref={svgRef} viewBox={`0 0 ${width} ${height}`}>
            <rect className="ex-ground" height={height} width={width} />
            {maps.map((box, index) => (
              <MapCells box={box} key={index} score={score} split={split} />
            ))}
            {mode === "probe" ? (
              <>
                <text className="hbr-title" x={maps[0].x + 2} y={maps[0].y + 15}>設定の地図</text>
                <ProbeMark box={maps[0]} d={d} logLam={loglam} />
                {!guided && (
                  <rect
                    aria-hidden="true" className="hbr-hit" height={DEGREES.length * maps[0].cell}
                    onPointerDown={pickCell} width={LOG_LAMS.length * maps[0].cellW}
                    x={maps[0].x + maps[0].left} y={maps[0].y + 22}
                  />
                )}
              </>
            ) : (
              <>
                <RunMarks
                  best={slide < 1 ? -1 : gridBest} box={maps[0]} count={count} kinds={distinctLambdas(gridPoints, count)}
                  name="格子" places={gridPlaces} shape="square" sliding={slide < 1}
                />
                <RunMarks
                  best={randomBest} box={maps[1]} count={count} kinds={distinctLambdas(randomPoints, count)}
                  name="ランダム" places={randomPlaces} shape="circle" sliding={false}
                />
              </>
            )}
            <MapKey rows={keyRows} score={score} width={keyWidth} y={keyY} />
            <CurvePanel
              box={curveBox}
              clipId={clipId}
              curves={mode === "probe"
                ? [{ d, logLam: loglam, tone: "update" as const }]
                : [
                    ...(g ? [{ d: g.d, logLam: g.log_lam, tone: gridBest === count - 1 && count < BUDGET ? "update" as const : "grid" as const }] : []),
                    ...(r ? [{ d: r.d, logLam: r.log_lam, tone: randomBest === count - 1 && count < BUDGET ? "update" as const : "random" as const }] : []),
                  ]}
              legend={mode === "probe"
                ? [{ tone: "update", text: `次数${d} の曲線` }]
                : [
                    { tone: "grid", text: g ? `格子の最良（次数${g.d}）` : "格子の最良" },
                    { tone: "random", text: r ? `ランダムの最良（次数${r.d}）` : "ランダムの最良" },
                  ]}
              note={mode === "probe" ? `点数 ${fmt(probeScore, 3)}` : undefined}
              showTruth={showTruth && !guided}
            />
            {bestBox && (score === "fresh" ? (
              <ScoreBars box={bestBox} grid={g} random={r} reveal={reveal} split={split} />
            ) : (
              <BestSoFar
                box={bestBox} count={count} grid={bestSoFar(gridPoints, split)}
                random={bestSoFar(randomPoints, split)} split={split} spread={spread}
              />
            ))}
          </svg>
        </div>
      }
      summary={summary}
      tour={tour}
    />
  );
}

/** `useStageViewport` wants bounds; this figure only uses the width it measures. */
const STAGE_BOUNDS = { xMin: 0, xMax: 1, yMin: 0, yMax: 1 };

/** The grey cells of one map and its axes. Redrawn only when the scores or the geometry change. */
const MapCells = memo(function MapCells({ box, score, split }: { box: MapBox; score: Score; split: number }) {
  const top = box.y + 22;
  const bottom = top + DEGREES.length * box.cell;
  const left = box.x + box.left;
  return (
    <g>
      {DEGREES.map((degree, row) => LOG_LAMS.map((_, column) => (
        <rect
          fill={shade(mapScore(row, column, score, split))}
          height={box.cell + 0.4}
          key={`${degree}-${column}`}
          width={box.cellW + 0.4}
          x={left + column * box.cellW}
          y={top + (DEGREES.length - 1 - row) * box.cell}
        />
      )))}
      <path className="hbr-frame" d={`M${left} ${top}V${bottom}H${left + LOG_LAMS.length * box.cellW}`} />
      {box.ticks && [2, 8, 15].map((degree) => (
        <text className="ex-axes-text" key={degree} textAnchor="end" x={left - 5} y={mapPoint(box, degree, 0)[1] + 4.5}>
          {degree}
        </text>
      ))}
      {[-6, -4, -2, 0].map((exponent) => (
        <text
          className="ex-axes-text" key={exponent} textAnchor="middle"
          x={mapPoint(box, 2, exponent)[0]} y={bottom + 26}
        >
          {fmt(exponent, 0)}
        </text>
      ))}
    </g>
  );
});

function ProbeMark({ box, d, logLam }: { box: MapBox; d: number; logLam: number }) {
  const [x, y] = mapPoint(box, d, logLam);
  return (
    <g>
      <path className="hbr-lam-tick is-latest" d={`M${x} ${box.y + 22 + DEGREES.length * box.cell + 2}v9`} />
      <circle className="hbr-ring" cx={x} cy={y} r={8} />
      <circle className="hbr-mark is-latest" cx={x} cy={y} r={4} />
    </g>
  );
}

interface RunMarksProps {
  box: MapBox;
  name: string;
  shape: "square" | "circle";
  /** (degree, log10 λ) of each evaluation, in the order they are run. */
  places: ReadonlyArray<readonly [number, number]>;
  count: number;
  best: number;
  kinds: number;
  sliding: boolean;
}

/** One run on its map: the settings tried so far, the newest one, the best one, and the λ values seen. */
function RunMarks({ box, name, shape, places, count, best, kinds, sliding }: RunMarksProps) {
  const stripY = box.y + 22 + DEGREES.length * box.cell + 2;
  const tried = places.slice(0, count);
  const lambdas = [...new Set(tried.map(([, logLam]) => logLam))];
  return (
    <g>
      <Glyph className="hbr-mark" shape={shape} x={box.x + 8} y={box.y + 10} />
      <text className="hbr-title" x={box.x + 18} y={box.y + 15}>{name}</text>
      <text className="hbr-count" textAnchor="end" x={box.x + box.w - 4} y={box.y + 15}>{box.w < 140 ? `λ ${kinds}種` : `λ ${kinds}種類`}</text>
      {lambdas.map((logLam) => (
        <path className="hbr-lam-tick" d={`M${mapPoint(box, 2, logLam)[0].toFixed(1)} ${stripY}v9`} key={logLam} />
      ))}
      {tried.map(([d, logLam], index) => {
        const [x, y] = mapPoint(box, d, logLam);
        const latest = index === count - 1 && count < BUDGET && !sliding;
        return <Glyph className={latest ? "hbr-mark is-latest" : "hbr-mark"} key={index} shape={shape} x={x} y={y} />;
      })}
      {best !== -1 && (
        <circle className="hbr-ring" cx={mapPoint(box, ...places[best])[0]} cy={mapPoint(box, ...places[best])[1]} r={8.5} />
      )}
    </g>
  );
}

function Glyph({ shape, x, y, className }: { shape: "square" | "circle"; x: number; y: number; className: string }) {
  return shape === "square"
    ? <rect className={className} height={7.6} width={7.6} x={x - 3.8} y={y - 3.8} />
    : <circle className={className} cx={x} cy={y} r={4.2} />;
}

/** What the map's axes and its grey mean. */
function MapKey({ y, width, rows, score }: { y: number; width: number; rows: number; score: Score }) {
  const ramp = 56;
  const second = rows === 2 ? y + 30 : y + 13;
  const right = width - 4;
  return (
    <g>
      <text className="ex-axes-text" x={2} y={y + 13}>縦：次数　横：log₁₀ λ</text>
      <text className="ex-axes-text" textAnchor="end" x={right}  y={second}>大</text>
      {Array.from({ length: 8 }, (_, index) => (
        <rect
          fill={shade(0.13 * (1 / 0.13) ** (index / 7))} height={10} key={index} width={ramp / 8 + 0.4}
          x={right - 17 - ramp + (index * ramp) / 8} y={second - 10}
        />
      ))}
      <rect className="hbr-ramp" height={10} width={ramp} x={right - 17 - ramp} y={second - 10} />
      <text className="ex-axes-text" textAnchor="end" x={right - 21 - ramp} y={second}>
        濃さ：{score === "cv" ? "交差検証の点数" : "新しい5000点の点数"} 小
      </text>
    </g>
  );
}

type Tone = "grid" | "random" | "update";

interface CurvePanelProps {
  box: Rect;
  clipId: string;
  curves: ReadonlyArray<{ d: number; logLam: number; tone: Tone }>;
  legend: ReadonlyArray<{ tone: Tone; text: string }>;
  note?: string;
  showTruth: boolean;
}

/** The 30 points and the curve each shown setting stands for. Curves leaving the panel are cut off. */
function CurvePanel({ box, clipId, curves, legend, note, showTruth }: CurvePanelProps) {
  const rows = legend.length + (showTruth ? 1 : 0);
  const left = box.x + 26;
  const right = box.x + box.w - 6;
  const top = box.y + 6 + rows * 17;
  const bottom = box.y + box.h - 6;
  const px = (x: number) => left + ((x + 1) / 2) * (right - left);
  const py = (y: number) => bottom - ((y - CURVE_Y[0]) / (CURVE_Y[1] - CURVE_Y[0])) * (bottom - top);
  // Far outside the panel a value is only clipped anyway; bounding it keeps the path numbers sane.
  const path = (f: (x: number) => number) => CURVE_SAMPLES
    .map((x, index) => `${index === 0 ? "M" : "L"}${px(x).toFixed(1)} ${py(clamp(f(x), -60, 60)).toFixed(1)}`)
    .join("");
  return (
    <g>
      <rect className="hbr-panel" height={box.h} width={box.w} x={box.x} y={box.y} />
      {[-2, 0, 2].map((value) => (
        <g className="ex-axes" key={value}>
          <line x1={left} x2={right} y1={py(value)} y2={py(value)} />
          <text textAnchor="end" x={left - 5} y={py(value) + 4.5}>{fmt(value, 0)}</text>
        </g>
      ))}
      <clipPath id={clipId}>
        <rect height={bottom - top} width={right - left} x={left} y={top} />
      </clipPath>
      <g clipPath={`url(#${clipId})`}>
        {showTruth && <path className="hbr-truth" d={path(truth)} />}
        {DATA_X.map((x, index) => <circle className="hbr-datum" cx={px(x)} cy={py(DATA_Y[index])} key={index} r={2.6} />)}
        {curves.map((curve, index) => {
          const coefficients = fitCoefficients(curve.d, curve.logLam);
          return <path className={`hbr-curve is-${curve.tone}`} d={path((x) => curveValue(coefficients, x))} key={index} />;
        })}
      </g>
      {legend.map((item, index) => (
        <g key={item.tone}>
          <path className={`hbr-curve is-${item.tone}`} d={`M${box.x + 8} ${box.y + 12 + index * 17}h22`} />
          <text className="hbr-legend" x={box.x + 35} y={box.y + 16.5 + index * 17}>{item.text}</text>
        </g>
      ))}
      {showTruth && (
        <g>
          <path className="hbr-truth" d={`M${box.x + 8} ${box.y + 12 + legend.length * 17}h22`} />
          <text className="hbr-legend" x={box.x + 35} y={box.y + 16.5 + legend.length * 17}>真の曲線</text>
        </g>
      )}
      {note && <text className="hbr-note" textAnchor="end" x={right - 2} y={box.y + 17}>{note}</text>}
    </g>
  );
}

interface BestSoFarProps {
  box: Rect;
  count: number;
  grid: readonly number[];
  random: readonly number[];
  split: number;
  spread: boolean;
}

/** Lowest score after each evaluation, for both runs on one clock. */
function BestSoFar({ box, count, grid, random, split, spread }: BestSoFarProps) {
  const left = box.x + 36;
  const right = box.x + box.w - 104;
  const top = box.y + 26;
  const bottom = box.y + box.h - 22;
  const px = (k: number) => left + ((k - 1) / (BUDGET - 1)) * (right - left);
  const py = (value: number) => {
    const t = (Math.log10(value) - BEST_Y[0]) / (BEST_Y[1] - BEST_Y[0]);
    return bottom - clamp(t, 0, 1) * (bottom - top);
  };
  const stairs = (values: readonly number[]) => values.slice(0, count)
    .map((value, index) => (index === 0 ? `M${px(1)} ${py(value).toFixed(1)}` : `H${px(index + 1).toFixed(1)}V${py(value).toFixed(1)}`))
    .join("");
  const ends = count === 0 ? [] : [
    { name: "格子", value: grid[count - 1], y: py(grid[count - 1]) },
    { name: "ランダム", value: random[count - 1], y: py(random[count - 1]) },
  ];
  // The two labels sit beside their line ends; when the ends are close they are pushed apart.
  if (ends.length === 2 && Math.abs(ends[0].y - ends[1].y) < 17) {
    const middle = clamp((ends[0].y + ends[1].y) / 2, top + 8.5, bottom - 8.5);
    const upper = ends[0].y <= ends[1].y ? 0 : 1;
    ends[upper].y = middle - 8.5;
    ends[1 - upper].y = middle + 8.5;
  }
  const bandTop = py(Math.max(...RANDOM_BESTS));
  const bandBottom = py(Math.min(...RANDOM_BESTS));
  return (
    <g>
      <rect className="hbr-panel" height={box.h} width={box.w} x={box.x} y={box.y} />
      <text className="hbr-title" x={box.x + 6} y={box.y + 16}>これまでの最良の点数</text>
      <text className="ex-axes-text" textAnchor="end" x={box.x + box.w - 6} y={box.y + 16}>
        分け方 {split + 1} / {SPLITS}
      </text>
      {[0.15, 0.3, 0.6].map((value) => (
        <g className="ex-axes" key={value}>
          <line x1={left} x2={right} y1={py(value)} y2={py(value)} />
          <text textAnchor="end" x={left - 5} y={py(value) + 4.5}>{value}</text>
        </g>
      ))}
      {[1, 4, 8, 12, 16].map((k) => (
        <text className="ex-axes-text" key={k} textAnchor="middle" x={px(k)} y={bottom + 16}>{k === 16 ? "16回" : k}</text>
      ))}
      {spread && (
        <g>
          <rect className="hbr-band" height={bandBottom - bandTop} width={right - left} x={left} y={bandTop} />
          <text className="hbr-band-name" textAnchor="end" x={right - 3} y={bandTop - 6}>乱数200通り</text>
        </g>
      )}
      <path className="hbr-curve is-grid" d={stairs(grid)} />
      <path className="hbr-curve is-random" d={stairs(random)} />
      {ends.map((end) => (
        <text className="hbr-end" key={end.name} x={right + 6} y={end.y + 4.5}>
          {end.name} <tspan className="hbr-end-value">{fmt(end.value, 3)}</tspan>
        </text>
      ))}
    </g>
  );
}

interface ScoreBarsProps {
  box: Rect;
  grid: RacePoint | undefined;
  random: RacePoint | undefined;
  split: number;
  /** 0 = both bars at the score when chosen, 1 = the second bar at the score on fresh points. */
  reveal: number;
}

/** The two chosen settings, each with its score when chosen and its score on the fresh points. */
function ScoreBars({ box, grid, random, split, reveal }: ScoreBarsProps) {
  const left = box.x + 62;
  const length = Math.max(40, box.w - 62 - 132);
  const bar = (value: number) => (Math.min(value, BAR_MAX) / BAR_MAX) * length;
  const groups = [
    { name: "格子", point: grid },
    { name: "ランダム", point: random },
  ];
  return (
    <g>
      <rect className="hbr-panel" height={box.h} width={box.w} x={box.x} y={box.y} />
      <text className="hbr-title" x={box.x + 6} y={box.y + 16}>選んだ設定の点数</text>
      {groups.map(({ name, point }, index) => {
        if (!point) return null;
        const y = box.y + 28 + index * 44;
        const chosen = point.cv[split];
        const shown = chosen + (point.fresh - chosen) * reveal;
        return (
          <g key={name}>
            <text className="hbr-end" x={box.x + 6} y={y + 21}>{name}</text>
            <rect className="hbr-bar is-chosen" height={14} width={bar(chosen)} x={left} y={y} />
            <text className="ex-label" x={left + bar(chosen) + 6} y={y + 11.5}>選んだとき {fmt(chosen, 3)}</text>
            <rect className="hbr-bar is-fresh" height={14} width={bar(shown)} x={left} y={y + 18} />
            <text className="ex-label ex-label-strong" x={left + bar(shown) + 6} y={y + 29.5}>新しい5000点 {fmt(shown, 3)}</text>
          </g>
        );
      })}
    </g>
  );
}
