import { traceEventLabel, type PlaybackSpeed } from "../../contracts/trace";
import { PLAYBACK_SPEEDS, type PlaybackController } from "./usePlayback";

export function PlaybackControls({ playback }: { playback: PlaybackController }) {
  const atStart = playback.currentFrameIndex === 0;
  const atEnd = playback.currentFrameIndex === playback.frames.length - 1;
  const eventLabel = traceEventLabel(playback.currentFrame);
  return (
    <section className="playback-controls" aria-label="アルゴリズム再生コントロール">
      <div className="playback-status" aria-live="polite">
        <strong>{eventLabel}</strong>
        <span>
          Frame {playback.currentFrameIndex + 1}/{playback.frames.length}
          {" · "}評価 {playback.currentFrame.oracle_evaluations}
        </span>
      </div>
      <div className="playback-actions">
        <button
          aria-label="1フレーム戻る"
          disabled={atStart}
          onClick={playback.stepBackward}
          type="button"
        >
          ←
        </button>
        <button onClick={playback.togglePlayback} type="button">
          {playback.isPlaying ? "一時停止" : "再生"}
        </button>
        <button
          aria-label="1フレーム進む"
          disabled={atEnd}
          onClick={playback.stepForward}
          type="button"
        >
          →
        </button>
        <button
          aria-label={playback.direction === "forward" ? "逆再生にする" : "順再生にする"}
          onClick={playback.reverse}
          type="button"
        >
          {playback.direction === "forward" ? "Reverse" : "Forward"}
        </button>
        <label>
          <span>再生速度</span>
          <select
            aria-label="再生速度"
            onChange={(event) => playback.setSpeed(Number(event.target.value) as PlaybackSpeed)}
            value={String(playback.speed)}
          >
            {PLAYBACK_SPEEDS.map((speed) => (
              <option key={speed} value={speed}>{speed}×</option>
            ))}
          </select>
        </label>
      </div>
      <label className="playback-seek">
        <span>フレーム位置</span>
        <input
          aria-label="フレーム位置"
          max={playback.frames.length - 1}
          min={0}
          onChange={(event) => playback.seekToFrame(Number(event.target.value))}
          step={1}
          type="range"
          value={playback.currentFrameIndex}
        />
      </label>
      <label className="playback-evaluation-seek">
        <span>評価回数位置</span>
        <input
          aria-label="評価回数位置"
          max={playback.frames.at(-1)?.oracle_evaluations ?? 0}
          min={0}
          onChange={(event) => playback.seekToEvaluation(Number(event.target.value))}
          step={1}
          type="number"
          value={playback.currentFrame.oracle_evaluations}
        />
      </label>
    </section>
  );
}
