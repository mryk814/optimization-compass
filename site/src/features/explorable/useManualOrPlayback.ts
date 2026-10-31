import { useCallback, useEffect, useState } from "react";

import type { Timeline } from "./useTimeline";

/**
 * A control value that the reader sets with a slider and that a playback can also drive.
 * Moving the slider stops the playback and hands the value back to the slider; while the
 * timeline is playing or has moved off its start, the value follows the timeline.
 *
 * `startFinished` shows the finished playback state on first render (the convention for
 * figures that open on the answer); otherwise the figure opens on the slider's value.
 */
export function useManualOrPlayback(
  timeline: Timeline,
  initial: number,
  valueAt: (position: number) => number,
  startFinished: boolean,
) {
  const [manual, setManual] = useState(initial);
  const { finish, seek } = timeline;
  useEffect(() => {
    if (startFinished) finish();
    // Only on mount: later changes are the reader's.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  const playback = timeline.playing || timeline.position > 0;
  const value = playback ? valueAt(timeline.position) : manual;
  const set = useCallback((next: number) => {
    seek(0);
    setManual(next);
  }, [seek]);
  return { value, set, playback };
}
