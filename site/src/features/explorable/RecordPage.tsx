import { Suspense, useEffect } from "react";

import { EXPLORABLE_COMPONENTS } from "./registry";
import { SceneRecordingContext } from "./useSceneTour";

import "./explorable.css";

/**
 * `#/record/<id>`: the figure alone, in its guided scene, laid out for a 16:9 frame.
 * `site/scripts/record-scene.mjs` drives it through `window.__ocScene`; it is not linked
 * from the site and renders outside the app chrome.
 */
export default function RecordPage({ id }: { id: string }) {
  const Figure = EXPLORABLE_COMPONENTS[id];
  useEffect(() => {
    document.body.style.margin = "0";
  }, []);
  if (!Figure) return <p role="alert">unknown explorable: {id}</p>;
  return (
    <SceneRecordingContext.Provider value>
      <div className="explorable ex-record" data-explorable-id={id}>
        <Suspense fallback={null}>
          <Figure />
        </Suspense>
      </div>
    </SceneRecordingContext.Provider>
  );
}
