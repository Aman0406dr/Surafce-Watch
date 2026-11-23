import { useEffect, useState } from 'react';
import {
  Activity, AlertTriangle, ArrowDownToLine, ArrowRight, Check, CircleHelp,
  Clock3, Database, ExternalLink, Globe2, LoaderCircle, RefreshCw, Search,
  LogOut, Shield, ShieldAlert, ShieldCheck, Wifi, X,
} from 'lucide-react';
import { downloadReportPdf } from './exportPdf.js';

const SEVERITIES = ['critical', 'high', 'medium', 'low', 'info'];
const SEVERITY_COLORS = { critical: '#ff6654', high: '#ff7900', medium: '#ffc45c', low: '#9bc5de', info: '#62bd83' };
const shortDate = value => new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value));

function scoreLabel(score) {
  if (score >= 80) return 'Strong';
  if (score >= 55) return 'Needs attention';
  return 'At risk';
}

function FindingRow({ item, index }) {
  const Icon = item.severity === 'info' ? Check : item.severity === 'low' ? CircleHelp : ShieldAlert;
  return (
    <article className="finding-row" style={{ '--animation-delay': `${index * 55}ms` }}>
      <div className={`severity-mark severity-${item.severity}`}><Icon size={14} strokeWidth={2} /><span>{item.severity}</span></div>
      <div className="finding-main">
        <div className="finding-title-line"><h3>{item.title}</h3><span className="finding-category">{item.category}</span></div>
        <p>{item.detail}</p>
        <p className="finding-recommendation"><strong>Recommendation</strong><span>{item.recommendation}</span></p>
      </div>
    </article>
  );
}

function ScoreRing({ score }) {
  return (
    <div className={`score-ring ${score >= 80 ? 'ring-good' : score >= 55 ? 'ring-mid' : 'ring-low'}`} style={{ '--score-target': `${score * 3.6}deg` }}>
      <div className="score-center"><strong>{score}</strong><span>/ 100</span></div>
    </div>
  );
}

function SeverityChart({ summary }) {
  const counts = SEVERITIES.map(severity => ({ severity, count: summary?.[severity] || 0 }));
  const total = counts.reduce((sum, item) => sum + item.count, 0);
  let end = 0;
  const slices = counts.filter(item => item.count > 0).map(item => {
    const start = end;
    end += item.count / total * 100;
    return `${SEVERITY_COLORS[item.severity]} ${start}% ${end}%`;
  });
  const chartStyle = { background: total ? `conic-gradient(${slices.join(', ')})` : '#39332e' };

  return (
    <section className="severity-chart-panel" aria-label="Findings by severity">
      <div className="severity-donut" style={chartStyle} role="img" aria-label={`${total} total findings`}>
        <div className="severity-donut-center"><strong>{total}</strong><span>findings</span></div>
      </div>
      <ul className="severity-legend">
        {counts.map(item => <li key={item.severity}><span style={{ background: SEVERITY_COLORS[item.severity] }} />{item.severity}<strong>{item.count}</strong></li>)}
      </ul>
    </section>
  );
}

function AuthScreen({ mode, setMode, email, setEmail, password, setPassword, loading, error, onSubmit }) {
  const registering = mode === 'register';
  return (
    <div className="app-shell auth-shell">
      <header className="topbar"><a className="brand" href="#"><span className="brand-symbol"><Shield size={18} /></span><span>surface<span className="brand-light">watch</span></span></a><span className="product-label">PRIVATE SCAN WORKSPACE</span></header>
      <main className="auth-main">
        <form className="auth-panel" onSubmit={onSubmit}>
          <p className="eyebrow">ACCOUNT ACCESS</p>
          <h1>{registering ? 'Create your account.' : 'Welcome back.'}</h1>
          <p className="auth-description">{registering ? 'Your scan reports will be kept in your private workspace.' : 'Sign in to see your private scan history.'}</p>
          <label>Email address<input type="email" autoComplete="email" value={email} onChange={event => setEmail(event.target.value)} required maxLength={254} /></label>
          <label>Password<input type="password" autoComplete={registering ? 'new-password' : 'current-password'} value={password} onChange={event => setPassword(event.target.value)} required minLength={registering ? 10 : undefined} /></label>
          {registering && <p className="password-hint">Use at least 10 characters.</p>}
          {error && <p className="auth-error" role="alert">{error}</p>}
          <button className="scan-button auth-submit" type="submit" disabled={loading}>{loading ? 'Please wait...' : registering ? 'Create account' : 'Sign in'}</button>
          <p className="auth-switch">{registering ? 'Already registered?' : 'New to Surface Watch?'} <button type="button" onClick={() => setMode(registering ? 'login' : 'register')}>{registering ? 'Sign in' : 'Create an account'}</button></p>
        </form>
      </main>
    </div>
  );
}

export default function App() {
  const [user, setUser] = useState(null);
  const [authReady, setAuthReady] = useState(false);
  const [authMode, setAuthMode] = useState('login');
  const [authEmail, setAuthEmail] = useState('');
  const [authPassword, setAuthPassword] = useState('');
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState('');
  const [url, setUrl] = useState('');
  const [report, setReport] = useState(null);
  const [scans, setScans] = useState([]);
  const [storage, setStorage] = useState('memory');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function refreshHistory() {
    try {
      const [healthResponse, scansResponse] = await Promise.all([fetch('/api/health'), fetch('/api/scans')]);
      const health = await healthResponse.json();
      const result = await scansResponse.json();
      setStorage(health.storage || 'memory');
      setScans(result.scans || []);
    } catch {
      setError('Could not reach the local scanner. Check that the API server is running.');
    }
  }

  useEffect(() => {
    fetch('/api/auth/me')
      .then(response => response.json())
      .then(result => {
        setUser(result.user);
        if (result.user) refreshHistory();
      })
      .catch(() => setAuthError('Could not reach the sign-in service.'))
      .finally(() => setAuthReady(true));
  }, []);

  async function submitAuth(event) {
    event.preventDefault();
    setAuthLoading(true);
    setAuthError('');
    try {
      const response = await fetch(`/api/auth/${authMode}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: authEmail, password: authPassword }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || 'Could not authenticate.');
      setUser(result.user);
      setAuthPassword('');
      await refreshHistory();
    } catch (error) {
      setAuthError(error.message || 'Could not authenticate.');
    } finally {
      setAuthLoading(false);
    }
  }

  async function signOut() {
    await fetch('/api/auth/logout', { method: 'POST' });
    setUser(null);
    setScans([]);
    setReport(null);
    setUrl('');
  }

  async function runScan(event) {
    event?.preventDefault();
    setLoading(true);
    setError('');
    try {
      const response = await fetch('/api/scans', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || 'The scan could not be completed.');
      setReport(result.report);
      setStorage(result.storage || 'memory');
      await refreshHistory();
      document.querySelector('#assessment')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (scanError) {
      setError(scanError.message || 'The scan could not be completed.');
    } finally {
      setLoading(false);
    }
  }

  function openReport(item) {
    setReport(item);
    setUrl(item.target);
    document.querySelector('#assessment')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  const findingCount = report ? SEVERITIES.reduce((total, severity) => total + (report.summary?.[severity] || 0), 0) : 0;

  if (!authReady) return <div className="app-shell auth-loading">Loading account...</div>;
  if (!user) return <AuthScreen mode={authMode} setMode={setAuthMode} email={authEmail} setEmail={setAuthEmail} password={authPassword} setPassword={setAuthPassword} loading={authLoading} error={authError} onSubmit={submitAuth} />;

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#top"><span className="brand-symbol"><Shield size={18} /></span><span>surface<span className="brand-light">watch</span></span></a>
        <div className="topbar-right"><span className="product-label">EXTERNAL EXPOSURE</span><span className="account-email">{user.email}</span><span className={`storage-state ${storage === 'mongodb' ? 'state-persisted' : ''}`}><span className="status-dot" />{storage === 'mongodb' ? 'MongoDB connected' : 'Temporary history'}</span><button className="logout-button" type="button" onClick={signOut} title="Sign out" aria-label="Sign out"><LogOut size={15} /></button></div>
      </header>

      <main id="top">
        <section className="intro-section">
          <div className="intro-copy"><p className="eyebrow"><Activity size={13} /> SECURITY / OVERVIEW</p><h1>Know what your site<br className="desktop-break" /> reveals at the edge.</h1><p className="intro-text">A focused read on transport, headers, and browser-facing protections.</p></div>
          <div className="intro-note"><span className="note-rule" /><span>Public targets only<br />One bounded request</span></div>
        </section>

        <section className={`scan-panel ${loading ? 'is-scanning' : ''}`} aria-label="Start a website scan">
          <form className="scan-form" onSubmit={runScan}>
            <label className="url-field"><Globe2 size={17} /><span className="sr-only">Website URL</span><input type="url" placeholder="https://your-domain.com" value={url} onChange={event => setUrl(event.target.value)} required aria-label="Website URL to scan" /></label>
            <button className="scan-button" type="submit" disabled={loading || !url.trim()}>{loading ? <><LoaderCircle className="spin" size={16} /> Assessing</> : <>Run assessment <ArrowRight size={16} /></>}</button>
          </form>
          <div className="scan-panel-foot"><span><ShieldCheck size={14} aria-hidden="true" /> No crawling, payload injection, or exploit tests</span><span>HTTP / HTTPS</span></div>
          {error && <div className="error-banner" role="alert"><AlertTriangle size={16} /><span>{error}</span><button type="button" aria-label="Dismiss error" onClick={() => setError('')}><X size={16} /></button></div>}
        </section>

        {report && <section className="assessment" id="assessment">
          <div className="section-heading report-heading"><div><p className="eyebrow">LATEST ASSESSMENT</p><h2>{report.host}</h2><a className="report-url" href={report.finalUrl} target="_blank" rel="noreferrer">{report.finalUrl}<ExternalLink size={12} /></a></div><div className="report-actions"><span className="scan-date"><Clock3 size={14} />{shortDate(report.scannedAt)}</span><button className="outline-button" type="button" onClick={() => runScan()} disabled={loading}><RefreshCw size={14} /> Rescan</button><button className="download-button" type="button" onClick={() => downloadReportPdf(report)}><ArrowDownToLine size={15} /> Export PDF</button></div></div>
          <div className="overview-grid">
            <div className="score-panel"><ScoreRing score={report.score} /><div className="score-copy"><span className="eyebrow">SURFACE SCORE</span><strong>{scoreLabel(report.score)}</strong><span>{findingCount} observations across {new Set(report.findings.map(item => item.category)).size} categories</span></div></div>
            <div className="severity-grid">{SEVERITIES.slice(0, 4).map(severity => <div className={`severity-card card-${severity}`} key={severity}><span className="severity-card-label">{severity}</span><strong>{report.summary?.[severity] || 0}</strong><span>{severity === 'critical' || severity === 'high' ? 'priority' : 'observed'}</span></div>)}</div>
            <SeverityChart summary={report.summary} />
          </div>
          <div className="report-facts"><span><strong>HTTP</strong> {report.statusCode}</span><span><strong>Completed</strong> {report.durationMs} ms</span><span><strong>Redirects</strong> {report.redirects?.length || 0}</span><span><strong>Page title</strong> {report.pageTitle || 'Not detected'}</span></div>
          <div className="findings-heading"><div><p className="eyebrow">REVIEW AND REMEDIATE</p><h2>Findings <span>{findingCount}</span></h2></div><span className="sort-caption">Sorted by severity</span></div>
          <div className="findings-list">{report.findings.length ? report.findings.map((item, index) => <FindingRow item={item} index={index} key={`${item.title}-${index}`} />) : <div className="no-findings"><ShieldCheck size={22} /><span>No configured checks returned a finding. This is not a guarantee that the site is secure.</span></div>}</div>
          <p className="scope-note"><ShieldCheck size={15} /><span>{report.scopeNote} Results are indicators, not a substitute for a full security review.</span></p>
        </section>}

        <section className="history-section">
          <div className="section-heading"><div><p className="eyebrow">YOUR ACTIVITY</p><h2>Recent assessments</h2></div><div className="history-caption">{storage === 'mongodb' ? <><Database size={14} /> Saved to MongoDB</> : <><Wifi size={14} /> Session only</>}</div></div>
          {scans.length ? <div className="history-table-wrap"><table className="history-table"><thead><tr><th>Target</th><th>Last scanned</th><th>Score</th><th>Findings</th><th aria-label="Open report" /></tr></thead><tbody>{scans.map(item => <tr key={item._id} onClick={() => openReport(item)} tabIndex={0} onKeyDown={event => event.key === 'Enter' && openReport(item)}><td><span className="history-domain"><Globe2 size={15} />{item.host}</span><span className="history-url">{item.finalUrl}</span></td><td>{shortDate(item.scannedAt)}</td><td><span className={`history-score ${item.score >= 80 ? 'text-good' : item.score >= 55 ? 'text-mid' : 'text-low'}`}>{item.score}<small>/100</small></span></td><td><span className="history-findings"><b className="high-count">{(item.summary?.critical || 0) + (item.summary?.high || 0)} high</b><span>{item.summary?.medium || 0} medium</span></span></td><td><ArrowRight size={15} /></td></tr>)}</tbody></table></div> : <div className="history-empty"><div className="empty-icon"><Search size={19} /></div><div><strong>No assessments yet</strong><span>Your completed scans will appear here.</span></div></div>}
        </section>

        <footer className="page-footer"><span><Shield size={14} /> Surface Watch <span className="footer-divider">/</span> Passive configuration audit</span><span>For authorized security testing only</span></footer>
      </main>
    </div>
  );
}
