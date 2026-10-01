import { StrictMode, lazy } from "react";
import { createRoot } from "react-dom/client";

import App from "./App";

import "./components/PageOrientation.css";
import "./typography.css";

const RecordPage = lazy(() => import("./features/explorable/RecordPage"));
const recordId = /^#\/record\/([a-z0-9-]+)$/u.exec(window.location.hash)?.[1];

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    {recordId ? <RecordPage id={recordId} /> : <App />}
  </StrictMode>,
);
