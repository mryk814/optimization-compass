import { siteBaseUrl } from "../../data/base-url";

export function LicenseLinks() {
  const baseUrl = siteBaseUrl();
  return (
    <span aria-label="ライセンス">
      <a href={`${baseUrl}licenses/LICENSE.txt`}>Code: MIT</a>
      {" · "}
      <a href={`${baseUrl}licenses/DATA_LICENSE.txt`}>Data: CC BY 4.0</a>
      {" · "}
      <a href={`${baseUrl}licenses/CONTENT_LICENSE.txt`}>Content: CC BY 4.0</a>
      {" · "}
      <a href={`${baseUrl}licenses/NOTICE.txt`}>Notice</a>
    </span>
  );
}
