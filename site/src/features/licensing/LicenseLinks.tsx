import { siteBaseUrl } from "../../data/base-url";

export function LicenseLinks() {
  const baseUrl = siteBaseUrl();
  return (
    <span aria-label="ライセンス">
      <a href={`${baseUrl}licenses/LICENSE.txt`}>コード: MIT</a>
      {" · "}
      <a href={`${baseUrl}licenses/DATA_LICENSE.txt`}>データ: CC BY 4.0</a>
      {" · "}
      <a href={`${baseUrl}licenses/CONTENT_LICENSE.txt`}>本文: CC BY 4.0</a>
      {" · "}
      <a href={`${baseUrl}licenses/NOTICE.txt`}>お知らせ</a>
    </span>
  );
}
