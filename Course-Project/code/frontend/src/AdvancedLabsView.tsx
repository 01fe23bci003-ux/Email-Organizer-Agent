import { useEffect, useState } from 'react'
import { AlertTriangle, Check, ChevronRight, Clock3, FileSearch, FlaskConical, GitBranch, LockKeyhole, Play, RotateCcw, ShieldCheck } from 'lucide-react'

const API = '/api'

type LabRecord = {
  id: string
  lab: number
  workflow: string
  created_at: string
  [key: string]: unknown
}

type LabInfo = { number: number; title: string; mode: string; output: string }
type Overview = { labs: LabInfo[]; history: LabRecord[] }
type Data = Record<string, unknown>

const labIcons = [FileSearch, AlertTriangle, GitBranch, ShieldCheck, FlaskConical, LockKeyhole]

async function requestJson<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  const response = await fetch(`${API}${path}`, {
    method,
    headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => null) as { detail?: string } | null
    throw new Error(error?.detail ?? `Request failed (${response.status})`)
  }
  return response.json() as Promise<T>
}

const text = (value: unknown) => typeof value === 'string' || typeof value === 'number' ? String(value) : ''
const rows = (value: unknown): Data[] => Array.isArray(value) ? value.filter((item): item is Data => typeof item === 'object' && item !== null && !Array.isArray(item)) : []
const prettyTime = (value: unknown) => text(value) ? new Date(text(value)).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : ''

export default function AdvancedLabsView() {
  const [overview, setOverview] = useState<Overview>({ labs: [], history: [] })
  const [activeLab, setActiveLab] = useState(9)
  const [result, setResult] = useState<LabRecord | null>(null)
  const [researchQuestion, setResearchQuestion] = useState('What deadlines and project review requests need faculty attention?')
  const [incident, setIncident] = useState('A deployment health check failed after a release.')
  const [requirement, setRequirement] = useState('Prepare a cited inbox brief and require faculty approval before consequential actions.')
  const [action, setAction] = useState('Review cited inbox findings')
  const [risk, setRisk] = useState('high')
  const [evidence, setEvidence] = useState('Cited mock inbox messages and generated acceptance checks')
  const [domainQuestion, setDomainQuestion] = useState('Which course access and assignment deadline issues need CSE AI faculty follow-up?')
  const [objective, setObjective] = useState('Create a cited faculty brief for urgent academic deadlines and project reviews.')
  const [owner, setOwner] = useState('faculty@kletech.ac.in')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  async function refresh() {
    setOverview(await requestJson<Overview>('/labs/advanced'))
  }

  useEffect(() => {
    let active = true
    requestJson<Overview>('/labs/advanced').then((data) => {
      if (active) setOverview(data)
    }).catch((cause: unknown) => {
      if (active) setError(cause instanceof Error ? cause.message : 'Could not load lab history')
    })
    return () => { active = false }
  }, [])

  async function runLab() {
    setBusy(true)
    setError('')
    setNotice('')
    try {
      const endpoints: Record<number, [string, Data]> = {
        9: ['/labs/research', { question: researchQuestion }],
        10: ['/labs/operations/diagnose', { incident }],
        11: ['/labs/sdlc/run', { requirement }],
        12: ['/labs/governance/evaluate', { action, risk_level: risk, evidence }],
        13: ['/labs/domain/run', { question: domainQuestion }],
        14: ['/labs/capstone/run', { objective }],
      }
      const [path, body] = endpoints[activeLab]
      setResult(await requestJson<LabRecord>(path, 'POST', body))
      await refresh()
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Lab run failed')
    } finally {
      setBusy(false)
    }
  }

  async function decideCapstone(decision: 'approve' | 'reject') {
    if (!result) return
    setBusy(true)
    setError('')
    setNotice('')
    try {
      const updated = await requestJson<LabRecord>(`/labs/capstone/${result.id}/${decision}`, 'POST', { approved_by: owner })
      setResult(updated)
      setNotice(decision === 'approve' ? `Capstone approved by ${owner}.` : `Capstone rejected by ${owner}.`)
      await refresh()
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Decision could not be saved')
    } finally {
      setBusy(false)
    }
  }

  const currentLab = overview.labs.find((lab) => lab.number === activeLab)
  const output = result?.lab === activeLab ? result : null

  return <div className="workspace-view advanced-labs">
    <div className="view-heading"><div><div className="eyebrow">EMAIL ORGANIZER <span>·</span> LABS 9–14</div><h1>Advanced lab studio</h1><p>Evidence, operations, governance, and capstone workflows for the email organizer.</p></div><span className="mock-tag"><span className="status-dot" /> MOCK / SIMULATED</span></div>
    {error && <div className="view-alert error-message" role="alert">{error}</div>}
    {notice && <div className="view-alert success-message" role="status"><Check size={15} />{notice}</div>}

    <div className="lab-tabs" role="tablist" aria-label="Advanced labs">
      {overview.labs.map((lab, index) => {
        const Icon = labIcons[index]
        return <button key={lab.number} role="tab" aria-selected={activeLab === lab.number} className={activeLab === lab.number ? 'selected' : ''} onClick={() => setActiveLab(lab.number)}>
          <Icon size={15} /><span><small>LAB {String(lab.number).padStart(2, '0')}</small><strong>{lab.title}</strong></span>
        </button>
      })}
    </div>

    <div className="lab-studio-grid">
      <section className="surface lab-workbench">
        <div className="surface-heading"><div><h2>{currentLab?.title ?? 'Advanced lab'}</h2><p>{currentLab?.mode} · {currentLab?.output}</p></div><FlaskConical size={17} /></div>
        {activeLab === 9 && <label className="lab-field">RESEARCH QUESTION<textarea rows={4} value={researchQuestion} onChange={(event) => setResearchQuestion(event.target.value)} /></label>}
        {activeLab === 10 && <><label className="lab-field">INCIDENT REPORT<textarea rows={4} value={incident} onChange={(event) => setIncident(event.target.value)} /></label><div className="simulation-note"><AlertTriangle size={15} />Simulation only. No cloud account is connected and no rollback is executed.</div></>}
        {activeLab === 11 && <label className="lab-field">REQUIREMENT<textarea rows={4} value={requirement} onChange={(event) => setRequirement(event.target.value)} /></label>}
        {activeLab === 12 && <><label className="lab-field">PROPOSED ACTION<input value={action} onChange={(event) => setAction(event.target.value)} /></label><div className="lab-inline-fields"><label className="lab-field">RISK LEVEL<select value={risk} onChange={(event) => setRisk(event.target.value)}><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option></select></label><label className="lab-field">EVIDENCE<input value={evidence} onChange={(event) => setEvidence(event.target.value)} /></label></div></>}
        {activeLab === 13 && <label className="lab-field">CSE (AI) QUESTION<textarea rows={4} value={domainQuestion} onChange={(event) => setDomainQuestion(event.target.value)} /></label>}
        {activeLab === 14 && <label className="lab-field">CAPSTONE OBJECTIVE<textarea rows={4} value={objective} onChange={(event) => setObjective(event.target.value)} /></label>}
        <button className="primary-button lab-run-button" onClick={runLab} disabled={busy}><Play size={15} />{busy ? 'Running…' : activeLab === 14 ? 'Run capstone pipeline' : 'Run lab workflow'}<ChevronRight size={15} /></button>
        {output && activeLab === 14 && output.status === 'waiting_for_approval' && <div className="capstone-decision"><label className="lab-field">REVIEWER IDENTITY<input value={owner} onChange={(event) => setOwner(event.target.value)} /></label><div><button className="primary-button" onClick={() => decideCapstone('approve')} disabled={busy || owner.trim().length < 3}><Check size={14} />Approve</button><button className="secondary-button" onClick={() => decideCapstone('reject')} disabled={busy || owner.trim().length < 3}><RotateCcw size={14} />Reject</button></div></div>}
      </section>

      <section className="surface lab-output">
        <div className="surface-heading"><div><h2>{output ? 'Run output' : 'Evidence & output'}</h2><p>{output ? `${output.id} · ${prettyTime(output.created_at)}` : 'Run a workflow to inspect its evidence and decisions.'}</p></div><Clock3 size={17} /></div>
        {output ? <LabOutput lab={activeLab} data={output} /> : <div className="lab-empty"><FlaskConical size={23} /><strong>Ready to run</strong><span>Inputs are processed by deterministic mock workflows. Results and decisions appear here.</span></div>}
      </section>
    </div>

    <section className="surface lab-history">
      <div className="surface-heading"><div><h2>Recent lab runs</h2><p>{overview.history.length} recorded run(s) · persistent audit events are in Audit Logs</p></div><Clock3 size={17} /></div>
      {overview.history.length ? <div className="lab-history-list">{overview.history.map((item) => <button key={item.id} onClick={() => { setActiveLab(item.lab); setResult(item); setError('') }}><span className="history-lab">LAB {String(item.lab).padStart(2, '0')}</span><span className="history-name"><strong>{text(item.workflow).replaceAll('_', ' ')}</strong><small>{text(item.question ?? item.incident ?? item.requirement ?? item.action ?? item.objective)}</small></span><span className="status-label">{text(item.status ?? item.decision ?? 'RECORDED').replaceAll('_', ' ')}</span><ChevronRight size={15} /></button>)}</div> : <div className="quiet-empty">No advanced lab runs yet.</div>}
    </section>
    <div className="view-footer"><span><LockKeyhole size={13} /> Human approval required for consequential actions · no send operation exists</span><span>LABS 1–14</span></div>
  </div>
}

function LabOutput({ lab, data }: { lab: number; data: LabRecord }) {
  if (lab === 9) return <><div className="lab-result-banner"><strong>{text(data.summary)}</strong><small>{text(data.question)}</small></div><div className="lab-source-list">{rows(data.sources).map((source) => <article key={text(source.email_id)}><span className="source-citation">{text(source.citation)}</span><strong>{text(source.subject)}</strong><small>{text(source.sender)} · {text(source.category)}</small><p>{text(source.excerpt)}</p></article>)}</div><div className="lab-limitations">{(Array.isArray(data.limitations) ? data.limitations : []).map((item) => <span key={text(item)}>{text(item)}</span>)}</div></>
  if (lab === 10) return <><div className="simulation-note"><AlertTriangle size={15} />{text(data.environment)} · rollback is not performed</div><div className="lab-result-banner"><strong>{text(data.status).replaceAll('_', ' ')}</strong><p>{text(data.recommendation)}</p></div><div className="lab-check-list">{rows(data.checks).map((check) => <div key={text(check.name)}><span>{text(check.name)}</span><strong>{text(check.result).replaceAll('_', ' ')}</strong><small>{text(check.detail)}</small></div>)}</div><ol className="lab-steps">{(Array.isArray(data.recovery_steps) ? data.recovery_steps : []).map((step) => <li key={text(step)}>{text(step)}</li>)}</ol></>
  if (lab === 11) return <><div className="lab-result-banner"><strong>{text(data.status).replaceAll('_', ' ')}</strong><small>{text(data.requirement)}</small></div><h3 className="lab-subheading">Acceptance criteria</h3><ul className="lab-criteria">{(Array.isArray(data.acceptance_criteria) ? data.acceptance_criteria : []).map((item) => <li key={text(item)}>{text(item)}</li>)}</ul><h3 className="lab-subheading">Generated checks</h3><div className="lab-check-list">{rows(data.generated_tests).map((check) => <div key={text(check.name)}><span>{text(check.name)}</span><strong className={check.passed ? 'check-pass' : 'check-fail'}>{check.passed ? 'PASS' : 'FAIL'}</strong></div>)}</div><p className="lab-footnote">{text(data.note)}</p></>
  if (lab === 12) return <><div className={`governance-decision ${text(data.decision)}`}><ShieldCheck size={20} /><span><small>POLICY DECISION</small><strong>{text(data.decision).replaceAll('_', ' ')}</strong></span></div><div className="lab-result-banner"><strong>{text(data.reason)}</strong><small>{text(data.action)} · {text(data.risk_level)} risk</small></div><div className="rollback-note"><RotateCcw size={15} /><span><strong>Rollback plan</strong><small>{text(data.rollback_plan)}</small></span></div></>
  if (lab === 13) return <><div className="lab-result-banner"><strong>{text(data.domain)}</strong><small>{text(data.question)} · {text(data.status).replaceAll('_', ' ')}</small></div><div className="lab-source-list">{rows(data.findings).map((finding, index) => <article key={`${text(finding.evidence)}-${index}`}><span className="source-citation">{text(finding.evidence)}</span><strong>{text(finding.finding)}</strong><p>{text(finding.excerpt)}</p></article>)}</div><div className="rollback-note"><ShieldCheck size={15} /><span><strong>Recommendation</strong><small>{text(data.recommendation)}</small></span></div></>
  return <><div className={`governance-decision ${text(data.status)}`}><LockKeyhole size={20} /><span><small>CAPSTONE STATUS</small><strong>{text(data.status).replaceAll('_', ' ')}</strong></span></div><div className="capstone-stages">{rows(data.stages).map((stage) => <div key={text(stage.stage)}><Check size={14} /><span><strong>{text(stage.stage).replaceAll('_', ' ')}</strong><small>{text(stage.status).replaceAll('_', ' ')} · record {text(stage.record_id)}</small></span></div>)}</div>{data.approved_by && <p className="lab-footnote">Decision recorded by {text(data.approved_by)}.</p>}</>
}