const COLORS = {
  ink: [30, 35, 40],
  muted: [100, 108, 116],
  accent: [210, 91, 24],
  line: [220, 224, 228],
  pale: [246, 247, 248],
};

const MARGIN = 18;
const FOOTER_SPACE = 16;

export async function downloadReportPdf(report) {
  const { jsPDF } = await import('jspdf');
  const pdf = new jsPDF({ unit: 'mm', format: 'a4' });
  const pageWidth = pdf.internal.pageSize.getWidth();
  const pageHeight = pdf.internal.pageSize.getHeight();
  const contentWidth = pageWidth - MARGIN * 2;
  const bottomLimit = pageHeight - FOOTER_SPACE;
  let y = MARGIN;

  function addPage() {
    pdf.addPage();
    y = MARGIN;
  }

  function ensureSpace(height) {
    if (y + height > bottomLimit) addPage();
  }

  function writeText(text, { size = 10, color = COLORS.ink, bold = false, indent = 0, gap = 2 } = {}) {
    pdf.setFont('helvetica', bold ? 'bold' : 'normal');
    pdf.setFontSize(size);
    pdf.setTextColor(...color);

    const lineHeight = size * 0.48;
    const lines = pdf.splitTextToSize(String(text ?? ''), contentWidth - indent);
    for (const line of lines) {
      ensureSpace(lineHeight);
      pdf.text(line, MARGIN + indent, y);
      y += lineHeight;
    }
    y += gap;
  }

  pdf.setFillColor(...COLORS.accent);
  pdf.rect(MARGIN, y, 2, 8, 'F');
  pdf.setFont('helvetica', 'bold');
  pdf.setFontSize(9);
  pdf.setTextColor(...COLORS.accent);
  pdf.text('SURFACE WATCH  /  WEB SECURITY', MARGIN + 5, y + 5.5);
  y += 15;

  writeText('Website security report', { size: 21, bold: true, gap: 2 });
  writeText(report.host || report.target || 'Website', { size: 13, bold: true, gap: 1 });
  writeText(report.finalUrl || report.target || '', { size: 9, color: COLORS.muted, gap: 5 });

  const summaryHeight = 29;
  ensureSpace(summaryHeight + 8);
  pdf.setFillColor(...COLORS.pale);
  pdf.roundedRect(MARGIN, y, contentWidth, summaryHeight, 2, 2, 'F');

  const scoreColumnWidth = 39;
  pdf.setFont('helvetica', 'normal');
  pdf.setFontSize(8);
  pdf.setTextColor(...COLORS.muted);
  pdf.text('SURFACE SCORE', MARGIN + 5, y + 8);
  pdf.setFont('helvetica', 'bold');
  pdf.setFontSize(17);
  pdf.setTextColor(...COLORS.ink);
  pdf.text(`${report.score ?? 0} / 100`, MARGIN + 5, y + 20);

  const levels = ['critical', 'high', 'medium', 'low', 'info'];
  const countsWidth = contentWidth - scoreColumnWidth - 8;
  const columnWidth = countsWidth / levels.length;
  pdf.setFont('helvetica', 'normal');
  pdf.setFontSize(7);
  levels.forEach((level, index) => {
    const x = MARGIN + scoreColumnWidth + index * columnWidth;
    pdf.setTextColor(...COLORS.muted);
    pdf.text(level.toUpperCase(), x, y + 10);
    pdf.setFont('helvetica', 'bold');
    pdf.setFontSize(11);
    pdf.setTextColor(...COLORS.ink);
    pdf.text(String(report.summary?.[level] || 0), x, y + 20);
    pdf.setFont('helvetica', 'normal');
    pdf.setFontSize(7);
  });
  y += summaryHeight + 7;

  writeText(`Scanned ${new Date(report.scannedAt).toLocaleString()}`, { size: 9, color: COLORS.muted, gap: 1 });
  writeText(`HTTP ${report.statusCode ?? '—'}  ·  ${report.durationMs ?? 0} ms  ·  ${(report.redirects || []).length} redirects`, {
    size: 9,
    color: COLORS.muted,
    gap: 5,
  });

  pdf.setDrawColor(...COLORS.line);
  pdf.line(MARGIN, y, pageWidth - MARGIN, y);
  y += 8;
  writeText(`Findings (${(report.findings || []).length})`, { size: 15, bold: true, gap: 5 });

  for (const finding of report.findings || []) {
    ensureSpace(18);

    pdf.setDrawColor(...COLORS.line);
    pdf.line(MARGIN, y, pageWidth - MARGIN, y);
    y += 6;

    writeText(`${finding.severity.toUpperCase()}  /  ${finding.category}`, {
      size: 8,
      color: COLORS.accent,
      bold: true,
      gap: 2,
    });
    writeText(finding.title, { size: 11, bold: true, gap: 2 });
    writeText(finding.detail, { size: 9, gap: 2 });
    writeText(`Recommendation: ${finding.recommendation}`, { size: 9, color: COLORS.muted, gap: 5 });
  }

  writeText(report.scopeNote || 'Passive configuration review.', { size: 8, color: COLORS.muted, gap: 2 });

  const pageCount = pdf.internal.getNumberOfPages();
  for (let page = 1; page <= pageCount; page += 1) {
    pdf.setPage(page);
    pdf.setDrawColor(...COLORS.line);
    pdf.line(MARGIN, pageHeight - 12, pageWidth - MARGIN, pageHeight - 12);
    pdf.setFont('helvetica', 'normal');
    pdf.setFontSize(8);
    pdf.setTextColor(...COLORS.muted);
    pdf.text('Surface Watch  ·  Passive configuration audit', MARGIN, pageHeight - 7);
    pdf.text(`${page} / ${pageCount}`, pageWidth - MARGIN, pageHeight - 7, { align: 'right' });
  }

  const filename = (report.host || 'report').replace(/[^a-z0-9.-]/gi, '-');
  pdf.save(`surface-watch-${filename}.pdf`);
}
