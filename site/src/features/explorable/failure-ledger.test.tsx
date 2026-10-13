import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import FailureLedger from "./FailureLedger";

afterEach(cleanup);

const choose = (name: string) => fireEvent.click(screen.getByRole("radio", { name }));

describe("FailureLedger", () => {
  it("starts with failures kept as statuses: 4 successes, 3 failures, 13 of 20 calls left", () => {
    render(<FailureLedger />);

    expect(screen.getByRole("meter", { name: /評価回数の消費/u })).toHaveAttribute("aria-valuenow", "7");
    expect(screen.getByText(/評価回数 7 \/ 20。成功 4、失敗 3（クラッシュ 1、時間切れ 1、物理的にありえない出力 1）。失敗も1回に数えるので、残りは 13 回です。/u)).toBeTruthy();
    expect(
      screen.getAllByText(/成功だけの平均は、u₁＜0\.5 の側が 0\.1025、u₁≥0\.5 の側が 0\.0308 です。/u).length,
    ).toBeGreaterThan(0);
  });

  it("the ledger table lists the seven calls with a status each and no value for failures", () => {
    render(<FailureLedger />);

    const ledger = screen.getByRole("region", { name: "評価の台帳" });
    const body = within(ledger).getAllByRole("row").slice(1);
    expect(body).toHaveLength(7);
    expect(within(body[1]).getByText("クラッシュ")).toBeTruthy();
    expect(within(body[1]).getByText("値なし")).toBeTruthy();
    expect(within(body[3]).getByText("時間切れ")).toBeTruthy();
    expect(within(body[6]).getByText("物理的にありえない出力")).toBeTruthy();
    expect(within(body[2]).getByText("0.1025")).toBeTruthy();
  });

  it("the penalty policy (P = 10) pulls the half means to 6.7008 and 2.5231", () => {
    render(<FailureLedger />);

    choose("罰則値に置き換える");

    expect(
      screen.getAllByText(/失敗 3 件を P = 10 の値にすると、平均は u₁＜0\.5 の側が 6\.7008、u₁≥0\.5 の側が 2\.5231 になります。/u).length,
    ).toBeGreaterThan(0);
    expect(screen.getByText("1.025%")).toBeTruthy();
  });

  it("P = 0 ties three failures with the real best value", () => {
    render(<FailureLedger />);
    choose("罰則値に置き換える");

    fireEvent.change(screen.getByRole("slider", { name: /罰則値 P/u }), { target: { value: "0" } });

    expect(screen.getAllByText(/評価1、評価2、評価4、評価7/u).length).toBeGreaterThan(0);
    expect(screen.getByText(/失敗が最良と同点です/u)).toBeTruthy();
  });

  it("the penalty slider is disabled while failures are kept as statuses", () => {
    render(<FailureLedger />);

    expect(screen.getByRole("slider", { name: /罰則値 P/u })).toBeDisabled();
    choose("罰則値に置き換える");
    expect(screen.getByRole("slider", { name: /罰則値 P/u })).not.toBeDisabled();
  });

  it("a probe next to the crash gets no value under the status policy and the penalty under the other", () => {
    render(<FailureLedger />);

    expect(
      screen.getAllByText(/試す点 \(0\.20, 0\.04\) に最も近い記録は評価2（クラッシュ、距離 0\.051）です。失敗には値がないので、この点の値は予想しません。最も近い成功は評価3で、距離は 0\.257 です。この点が実行できるかは、台帳からは分かりません。/u).length,
    ).toBeGreaterThan(0);

    choose("罰則値に置き換える");
    expect(
      screen.getAllByText(/この点の値を 10 と予想します。実行できるかどうかは分かっていないのに、悪い値だと言い切っています。/u).length,
    ).toBeGreaterThan(0);
  });

  it("only a probe outside [0, 1] is a known violation, and it uses no budget", () => {
    render(<FailureLedger />);

    fireEvent.change(screen.getByRole("slider", { name: /試す点 u₁/u }), { target: { value: "1.1" } });

    expect(
      screen.getAllByText(/試す点 \(1\.10, 0\.04\) は、u₁が範囲 \[0, 1\] の外です。実行する前に違反と分かるので、評価回数を使わず、台帳にも入れません。/u).length,
    ).toBeGreaterThan(0);
    expect(screen.getByRole("meter", { name: /評価回数の消費/u })).toHaveAttribute("aria-valuenow", "7");
  });

  it("shrinking N to 2 leaves 18 calls with one success and one crash", () => {
    render(<FailureLedger />);

    fireEvent.change(screen.getByRole("slider", { name: /ここまでの評価回数 N/u }), { target: { value: "2" } });

    expect(screen.getByText(/評価回数 2 \/ 20。成功 1、失敗 1（クラッシュ 1、時間切れ 0、物理的にありえない出力 0）。失敗も1回に数えるので、残りは 18 回です。/u)).toBeTruthy();
  });
});
