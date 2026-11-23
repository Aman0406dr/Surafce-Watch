import { fetchPage } from './scanner/request.js';
import { buildReport } from './scanner/report.js';

export async function scanTarget(target) {
  const started = performance.now();
  const page = await fetchPage(target);
  const report = buildReport(target, page);

  report.durationMs = Math.round(performance.now() - started);
  report.redirects = page.redirects;
  return report;
}
