function finding(severity, category, title, detail, recommendation) {
  return { severity, category, title, detail, recommendation };
}

function checkHeaders(headers, findings) {
  const checks = [
    ['content-security-policy', 'medium', 'Content Security Policy is missing', 'Add a restrictive Content-Security-Policy and tune it to the resources this site uses.'],
    ['x-content-type-options', 'low', 'MIME-sniffing protection is missing', 'Set X-Content-Type-Options: nosniff.'],
    ['referrer-policy', 'low', 'Referrer-Policy is missing', 'Set an explicit Referrer-Policy such as strict-origin-when-cross-origin.'],
    ['permissions-policy', 'low', 'Permissions-Policy is missing', 'Disable browser features the site does not need with a Permissions-Policy.'],
  ];

  for (const [header, severity, title, recommendation] of checks) {
    if (!headers[header]) {
      findings.push(finding(severity, 'HTTP headers', title, `The response did not include ${header}.`, recommendation));
    }
  }

  const csp = (headers['content-security-policy'] || '').toLowerCase();
  if (!headers['x-frame-options'] && !csp.includes('frame-ancestors')) {
    findings.push(finding('medium', 'HTTP headers', 'Clickjacking protection is missing', 'Neither X-Frame-Options nor a CSP frame-ancestors directive was observed.', 'Set X-Frame-Options or restrict framing with CSP frame-ancestors.'));
  }
}

function checkCookies(cookies, isHttps, findings) {
  for (const cookie of cookies) {
    const name = cookie.split('=', 1)[0].trim().slice(0, 80) || '(unnamed cookie)';
    const attributes = new Set(cookie.split(';').slice(1).map(part => part.trim().split('=', 1)[0].toLowerCase()));

    if (isHttps && !attributes.has('secure')) {
      findings.push(finding('medium', 'Cookies', `Cookie may be sent without Secure: ${name}`, 'A Set-Cookie response did not include the Secure attribute.', 'Add the Secure attribute to cookies that should only travel over HTTPS.'));
    }
    if (!attributes.has('httponly')) {
      findings.push(finding('medium', 'Cookies', `Cookie is readable by scripts: ${name}`, 'A Set-Cookie response did not include the HttpOnly attribute.', 'Add HttpOnly to cookies that do not need to be accessed by client-side scripts.'));
    }
    if (!attributes.has('samesite')) {
      findings.push(finding('low', 'Cookies', `SameSite is not set: ${name}`, 'A Set-Cookie response did not specify SameSite.', 'Set an intentional SameSite policy, commonly Lax, for this cookie.'));
    }
  }
}

function sortFindings(findings) {
  const order = { critical: 0, high: 1, medium: 2, low: 3, info: 4 };
  findings.sort((a, b) => order[a.severity] - order[b.severity]
    || a.category.localeCompare(b.category)
    || a.title.localeCompare(b.title));
}

function getScore(findings) {
  const points = { critical: 35, high: 20, medium: 10, low: 3, info: 0 };
  const lostPoints = findings.reduce((total, item) => total + points[item.severity], 0);
  return Math.max(0, 100 - lostPoints);
}

function getSummary(findings) {
  const severities = ['critical', 'high', 'medium', 'low', 'info'];
  return Object.fromEntries(severities.map(severity => [
    severity,
    findings.filter(item => item.severity === severity).length,
  ]));
}

export function buildReport(target, page) {
  const { finalUrl, headers, body, statusCode } = page;
  const contentType = headers['content-type'] || '';
  const isHttps = new URL(finalUrl).protocol === 'https:';
  const findings = [];

  if (isHttps) {
    findings.push(finding('info', 'Transport', 'HTTPS certificate validated', 'The HTTPS connection completed with certificate verification enabled.', 'Keep the certificate renewed and serve the entire site over HTTPS.'));
  } else {
    findings.push(finding('high', 'Transport', 'HTTPS is not enabled', 'The final page is served over an unencrypted HTTP connection.', 'Redirect visitors to HTTPS and enable a valid TLS certificate.'));
  }

  checkHeaders(headers, findings);
  if (isHttps && !headers['strict-transport-security']) {
    findings.push(finding('medium', 'HTTP headers', 'HSTS is missing', 'The HTTPS response did not include Strict-Transport-Security.', 'After confirming all subdomains support HTTPS, configure an appropriate HSTS max-age.'));
  }

  checkCookies(headers['set-cookie'] || [], isHttps, findings);

  for (const [header, label] of [['server', 'Server'], ['x-powered-by', 'X-Powered-By']]) {
    if (headers[header]) {
      findings.push(finding('low', 'Information disclosure', `${label} header is exposed`, `The response identifies software in the ${label} header.`, `Remove or minimize the ${label} header where practical.`));
    }
  }

  const html = contentType.toLowerCase().includes('html') ? body.toString('utf8') : '';
  const pageTitle = (html.match(/<title[^>]*>([\s\S]*?)<\/title\s*>/i)?.[1] || '')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, 200);

  sortFindings(findings);
  return {
    target,
    finalUrl,
    host: new URL(finalUrl).hostname.replace(/^\[|\]$/g, ''),
    scannedAt: new Date(),
    durationMs: 0,
    statusCode,
    contentType,
    pageTitle,
    redirects: [],
    score: getScore(findings),
    findings,
    summary: getSummary(findings),
    scopeNote: 'One bounded GET request; no crawling, payload injection, authentication attempts, or exploit tests.',
  };
}
