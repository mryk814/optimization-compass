export function siteBaseUrl(): string {
  return (import.meta as ImportMeta & { env: { BASE_URL: string } }).env.BASE_URL;
}
