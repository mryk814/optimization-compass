/**
 * Reader-facing framing of each explorable. This mirrors
 * `src/optimization_compass/resources/explorables.json`, which is the authority;
 * `explorable.test.tsx` fails when the two drift apart.
 */
import type { SceneBeat } from "./scene";

export interface ExplorableMeta {
  question: string;
  fixedConditions: string;
  notImplied: string;
  /** Guided scene (ADR 0018). Empty when the figure has none. */
  beats: readonly SceneBeat[];
}

export const EXPLORABLE_META: Readonly<Record<string, ExplorableMeta>> = {
  "gradient-descent-valley": {
    question: "同じ更新式でも、learning rateと谷の細長さで、収束・遅い収束・振動・発散が切り替わるのはなぜか。",
    fixedConditions: "目的関数は f(x,y)=(x-1)^2+κ(y+2)^2 に固定し、勾配は解析式で厳密に与える。",
    notImplied: "一般的な手法の優劣や、実問題で良いlearning rateを示すものではない。",
    beats: [
      {
        settings: { method: "gd", eta: 0.02, kappa: 20 },
        durationS: 8,
        captionJa: "ηが小さいと、急なy方向はすぐ落ち着くが、ゆるやかなx方向は1回に4%しか縮まず、100回でも収束しない。",
        narrationJa: "学習率イータが小さいと、急なワイ方向はすぐに落ち着きます。けれど、ゆるやかなエックス方向は一回に四パーセントしか縮まず、百回たっても収束しません。",
      },
      {
        settings: { method: "gd", eta: 0.045, kappa: 20 },
        durationS: 8,
        captionJa: "ηを上げるとx方向は速くなるが、y方向は符号を変えて往復し始める。",
        narrationJa: "イータを上げると、エックス方向は速くなります。その代わり、急なワイ方向では一歩が行き過ぎて、谷を左右に往復し始めます。",
      },
      {
        settings: { method: "gd", eta: 0.053, kappa: 20, x0: 5, y0: -1.5 },
        durationS: 7,
        captionJa: "安定限界 1/κ = 0.05 を少しでも超えると、y方向の往復が毎回広がって発散する。",
        narrationJa: "イータが安定限界の〇・〇五をわずかに超えただけで、往復の幅は毎回広がり、発散します。限界を決めたのは、いちばん急な方向でした。",
      },
      {
        settings: { method: "gd", eta: 0.3, kappa: 2 },
        durationS: 7,
        captionJa: "谷が丸い（κが小さい）と限界が広がり、大きなηで両方向とも速く縮む。",
        narrationJa: "谷が丸くなると、安定限界が広がります。大きなイータが使えて、どちらの方向も数回で縮みます。",
      },
      {
        settings: { method: "momentum", eta: 0.02, kappa: 20, beta: 0.6 },
        durationS: 8,
        captionJa: "細長い谷のままでも、Momentumは直前の動きを持ち越して、ゆるやかな方向を加速する。",
        narrationJa: "細長い谷のままでも、モメンタムは直前の動きを持ち越すことで、ゆるやかなエックス方向を加速できます。",
      },
    ],
  },
  "lp-vertex-walk": {
    question: "線形目的の最適解が、なぜ実行可能領域の頂点だけを調べれば見つかるのか。",
    fixedConditions: "2変数・2本の不等式と非負制約からなる固定のLP（max 3x+2y の係数を動かす）。",
    notImplied: "実際のprimal simplex実装のpivot ruleや計算量を示すものではない。隣の頂点へ移る動きは教育用の模式化である。",
    beats: [],
  },
  "convexity-chord": {
    question: "関数が凸であるとは、グラフ上の任意の2点を結ぶ線分がグラフより下へ入らないことだと、どう確かめられるか。",
    fixedConditions: "1変数の3つの固定関数を使い、点a・bと混合比θを動かして定義の不等式を数値で確かめる。",
    notImplied: "有限個の点の確認は凸性の証明ではない。可行集合の凸性も別に確認が必要である。",
    beats: [],
  },
};
