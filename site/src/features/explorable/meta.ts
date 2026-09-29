/**
 * Reader-facing framing of each explorable. This mirrors
 * `src/optimization_compass/resources/explorables.json`, which is the authority;
 * `explorable.test.tsx` fails when the two drift apart.
 */
export interface ExplorableMeta {
  question: string;
  fixedConditions: string;
  notImplied: string;
}

export const EXPLORABLE_META: Readonly<Record<string, ExplorableMeta>> = {
  "gradient-descent-valley": {
    question: "同じ更新式でも、learning rateと谷の細長さで、収束・遅い収束・振動・発散が切り替わるのはなぜか。",
    fixedConditions: "目的関数は f(x,y)=(x-1)^2+κ(y+2)^2 に固定し、勾配は解析式で厳密に与える。",
    notImplied: "一般的な手法の優劣や、実問題で良いlearning rateを示すものではない。",
  },
  "lp-vertex-walk": {
    question: "線形目的の最適解が、なぜ実行可能領域の頂点だけを調べれば見つかるのか。",
    fixedConditions: "2変数・2本の不等式と非負制約からなる固定のLP（max 3x+2y の係数を動かす）。",
    notImplied: "実際のprimal simplex実装のpivot ruleや計算量を示すものではない。隣の頂点へ移る動きは教育用の模式化である。",
  },
  "convexity-chord": {
    question: "関数が凸であるとは、グラフ上の任意の2点を結ぶ線分がグラフより下へ入らないことだと、どう確かめられるか。",
    fixedConditions: "1変数の3つの固定関数を使い、点a・bと混合比θを動かして定義の不等式を数値で確かめる。",
    notImplied: "有限個の点の確認は凸性の証明ではない。可行集合の凸性も別に確認が必要である。",
  },
};
