import { useEffect, useState } from 'react'
import { ArrowDownRight, ArrowUpRight, Check, ChevronRight, CircleAlert, Clock3, FileText, Flag, Inbox, LockKeyhole, Mail, RefreshCw, Reply, Search, ShieldCheck, Sparkles, X } from 'lucide-react'

const API = '/api'
export type ViewName = 'Dashboard' | 'Inbox' | 'Priority' | 'Action Items' | 'Draft Replies' | 'Follow-ups' | 'Calendar' | 'Agent Runs' | 'Audit Logs' | 'Lab Studio' | 'Settings' | 'Agent plan' | 'Email detail'

type Email = { id: string; sender: string; recipients: string[]; subject: string; body: string; timestamp: string; read: boolean; sender_category: string; content_type: string; priority: string; tags: string[]; requires_reply: boolean }
type Draft = { id: string; email_id: string; body: string; status: string; confidence?: number; source_template?: string }
type Stats = { total_emails: number; unread: number; high_priority: number; pending_replies: number; action_items: number; follow_ups: number; pending_approvals: number; priority_distribution: Record<string, number>; category_distribution: Record<string, number> }
type AgentRun = { id: string; status: string; current_node: string; retry_count: number; requires_approval: boolean; started_at: string; steps: Array<{ id: string; agent_name: string; status: string; input_summary: string; output_summary: string; email_id?: string; duration_ms?: number }> }
type RunDetails = { run: AgentRun; results: Array<{ email_id: string; nodes: Array<{ node: string; status: string; duration_ms?: number; output_summary: string }>; priority: { priority: string }; classification: { sender_category: string }; validation: { passed: boolean; requires_human_review: boolean }; draft_reply: { status: string }; archived: boolean }>; merge?: { processed_count: number; failed_email_ids: string[]; max_observed_workers?: number; duration_ms?: number; merge_rule?: string } }
type Analysis = { classification?: { sender_category: string; content_type: string; tags: string[]; confidence: number; sender_verified: boolean }; priority?: { priority: string; urgency_score: number; reason: string; detected_deadline?: string; requires_human_review: boolean }; draft_reply?: { body: string; explanation: string; prior_reply_used: boolean; source_template?: string; confidence: number; status: string }; action_items?: Array<{ task: string; deadline?: string; owner: string; status: string }>; follow_up?: { recommended: boolean; reason: string }; calendar_suggestion?: { meeting_detected: boolean; proposed_time?: string; participants: string[]; recommendation: string; requires_confirmation: boolean }; approval_status?: string; archived?: boolean }
type AuditEntry = { id?: string; timestamp?: string; run_id?: string; agent?: string; action?: string; status?: string; email_id?: string; details?: Record<string, unknown>; input?: unknown; output?: unknown }
type GenericRow = Record<string, string | number | boolean | null | undefined>
type Props = { view: ViewName; selectedEmailId: string | null; onOpenEmail: (emailId: string) => void }

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API}${path}`)
  if (!response.ok) throw new Error(`Request failed: ${path}`)
  return response.json() as Promise<T>
}

async function postJson<T>(path: string, body?: unknown, method = 'POST'): Promise<T> {
  const response = await fetch(`${API}${path}`, { method, headers: { 'Content-Type': 'application/json' }, body: body === undefined ? undefined : JSON.stringify(body) })
  if (!response.ok) {
    const message = await response.json().catch(() => null) as { detail?: string } | null
    throw new Error(message?.detail ?? `Request failed: ${path}`)
  }
  return response.json() as Promise<T>
}

const priorityClass = (priority: string) => `priority-pill ${priority.toLowerCase()}`
const formatDate = (value?: string) => value ? new Date(value).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—'

export default function WorkspaceView({ view, selectedEmailId, onOpenEmail }: Props) {
  const [emails, setEmails] = useState<Email[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [drafts, setDrafts] = useState<Draft[]>([])
  const [runs, setRuns] = useState<AgentRun[]>([])
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null)
  const [runDetails, setRunDetails] = useState<RunDetails | null>(null)
  const [audit, setAudit] = useState<AuditEntry[]>([])
  const [actions, setActions] = useState<GenericRow[]>([])
  const [followUps, setFollowUps] = useState<GenericRow[]>([])
  const [calendar, setCalendar] = useState<GenericRow[]>([])
  const [email, setEmail] = useState<Email | null>(null)
  const [analysis, setAnalysis] = useState<Analysis | null>(null)
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState('All')
  const [draftBody, setDraftBody] = useState('')
  const [owner, setOwner] = useState('faculty@kletech.ac.in')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  async function refresh() {
    const [emailRows, statsRow, draftRows, runRows, auditRows, actionRows, followRows, calendarRows] = await Promise.all([
      getJson<Email[]>('/emails'), getJson<Stats>('/dashboard/stats'), getJson<Draft[]>('/drafts'), getJson<AgentRun[]>('/agent/runs'),
      getJson<AuditEntry[]>('/audit-logs'), getJson<GenericRow[]>('/action-items'), getJson<GenericRow[]>('/follow-ups'), getJson<GenericRow[]>('/calendar/suggestions'),
    ])
    setEmails(emailRows); setStats(statsRow); setDrafts(draftRows); setRuns(runRows); setAudit(auditRows); setActions(actionRows); setFollowUps(followRows); setCalendar(calendarRows)
  }

  useEffect(() => {
    let live = true
    setError('')
    Promise.all([
      getJson<Email[]>('/emails'), getJson<Stats>('/dashboard/stats'), getJson<Draft[]>('/drafts'), getJson<AgentRun[]>('/agent/runs'),
      getJson<AuditEntry[]>('/audit-logs'), getJson<GenericRow[]>('/action-items'), getJson<GenericRow[]>('/follow-ups'), getJson<GenericRow[]>('/calendar/suggestions'),
    ]).then(([emailRows, statsRow, draftRows, runRows, auditRows, actionRows, followRows, calendarRows]) => {
      if (!live) return
      setEmails(emailRows); setStats(statsRow); setDrafts(draftRows); setRuns(runRows); setAudit(auditRows); setActions(actionRows); setFollowUps(followRows); setCalendar(calendarRows)
      if (!selectedRunId && runRows[0]) setSelectedRunId(runRows[0].id)
    }).catch((cause: unknown) => { if (live) setError(cause instanceof Error ? cause.message : 'Could not load data') })
    if (view === 'Email detail' && selectedEmailId) {
      Promise.all([getJson<Email>(`/emails/${selectedEmailId}`), getJson<Analysis>(`/emails/${selectedEmailId}/analysis`)]).then(([emailRow, analysisRow]) => {
        if (!live) return
        setEmail(emailRow); setAnalysis(analysisRow); setDraftBody(drafts.find((item) => item.email_id === selectedEmailId && item.status === 'draft')?.body ?? analysisRow.draft_reply?.body ?? '')
      }).catch((cause: unknown) => { if (live) setError(cause instanceof Error ? cause.message : 'Could not load email') })
    }
    return () => { live = false }
  }, [view, selectedEmailId])

  useEffect(() => {
    if (view !== 'Agent Runs' || !selectedRunId) return
    let live = true
    getJson<RunDetails>(`/agent/runs/${selectedRunId}`).then((data) => { if (live) setRunDetails(data) }).catch((cause: unknown) => { if (live) setError(cause instanceof Error ? cause.message : 'Could not load run') })
    return () => { live = false }
  }, [view, selectedRunId])

  async function draftAction(action: 'save' | 'approve' | 'reject' | 'regenerate') {
    if (!email) return
    setBusy(true); setError(''); setNotice('')
    try {
      const existing = drafts.find((item) => item.email_id === email.id && item.status === 'draft')
      if (action === 'save') {
        if (existing) await postJson(`/drafts/${existing.id}`, { body: draftBody }, 'PUT')
        else await postJson('/drafts', { email_id: email.id, body: draftBody, confidence: analysis?.draft_reply?.confidence ?? 0.5 })
      } else if (existing && action === 'approve') await postJson(`/drafts/${existing.id}/approve`, { approved_by: owner })
      else if (existing && action === 'reject') await postJson(`/drafts/${existing.id}/reject`, { approved_by: owner })
      else if (existing && action === 'regenerate') {
        const generated = await postJson<Draft>(`/drafts/${existing.id}/regenerate`)
        setDraftBody(generated.body)
      } else if (action === 'regenerate') {
        const generated = await postJson<Draft>('/drafts', { email_id: email.id, body: analysis?.draft_reply?.body ?? draftBody, confidence: analysis?.draft_reply?.confidence ?? 0.5, source_template: analysis?.draft_reply?.source_template })
        setDraftBody(generated.body)
      } else if (action === 'approve' || action === 'reject') {
        await postJson('/drafts', { email_id: email.id, body: draftBody, confidence: analysis?.draft_reply?.confidence ?? 0.5 })
        const saved = await getJson<Draft[]>('/drafts')
        setDrafts(saved)
        const fresh = saved.find((item) => item.email_id === email.id && item.status === 'draft')
        if (fresh) await postJson(`/drafts/${fresh.id}/${action}`, { approved_by: owner })
      }
      setNotice(action === 'approve' ? 'Draft approved. It remains a draft; nothing was sent.' : action === 'reject' ? 'Draft rejected and logged.' : action === 'regenerate' ? 'Draft regenerated for review.' : 'Draft saved.')
      await refresh()
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Draft action failed') }
    finally { setBusy(false) }
  }

  async function decideRun(decision: 'approve' | 'reject') {
    if (!runDetails) return
    setBusy(true); setError('')
    try {
      await postJson(`/agent/runs/${runDetails.run.id}/${decision}`, { approved_by: owner })
      setRunDetails(await getJson<RunDetails>(`/agent/runs/${runDetails.run.id}`))
      await refresh()
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Run decision failed') }
    finally { setBusy(false) }
  }

  const pageTitles: Record<ViewName, [string, string]> = {
    Dashboard: ['Inbox overview', 'A live view of triage, workload, and pending owner decisions.'], Inbox: ['Inbox', 'Twenty sample messages, ready for a governed triage run.'], Priority: ['Priority queue', 'Messages ordered for time-sensitive review.'], 'Action Items': ['Action items', 'Tasks extracted from messages plus the seeded task list.'], 'Draft Replies': ['Draft replies', 'Review, edit, approve, or reject. Approval never sends a message.'], 'Follow-ups': ['Follow-up queue', 'Reminder suggestions from explicit follow-up signals and unanswered requests.'], Calendar: ['Calendar suggestions', 'Proposed meeting times checked against the mock calendar.'], 'Agent Runs': ['Agent runs', 'Fan-out workers, node progress, merge summary, and the owner gate.'], 'Audit Logs': ['Audit log', 'Traceable tool calls, node steps, merge actions, and decisions.'], 'Lab Studio': ['Advanced lab studio', 'Evidence, operations, governance, and capstone workflows.'], Settings: ['Settings', 'Connector and safety configuration for this demonstration.'], 'Agent plan': ['Agent plan', 'Clarify the request, revise the plan, and lock it before execution.'], 'Email detail': ['Email detail', 'Original message and generated analysis.'],
  }
  const [title, subtitle] = pageTitles[view]
  const filteredEmails = emails.filter((item) => {
    const matchesSearch = `${item.sender} ${item.subject} ${item.body}`.toLowerCase().includes(search.toLowerCase())
    const matchesFilter = filter === 'All' || (filter === 'Unread' && !item.read) || (filter === 'Needs Reply' && item.requires_reply) || (filter === 'Action Item' && /please|submit|review|deadline|confirm/i.test(item.body)) || item.sender_category.toLowerCase() === filter.toLowerCase() || ((filter === 'High Priority') && ['HIGH', 'URGENT'].includes(item.priority))
    return matchesSearch && matchesFilter
  })

  return <div className="workspace-view">
    <div className="view-heading"><div><div className="eyebrow">EMAIL ORGANIZER <span>·</span> LABS 1–8</div><h1>{title}</h1><p>{subtitle}</p></div>{view !== 'Settings' && <span className="mock-tag"><span className="status-dot" /> MOCK DATA</span>}</div>
    {error && <div className="view-alert error-message" role="alert"><CircleAlert size={15} />{error}</div>}
    {notice && <div className="view-alert success-message" role="status"><Check size={15} />{notice}</div>}

    {view === 'Dashboard' && stats && <>
      <div className="stat-grid">{[['Total emails', stats.total_emails, 'in mock mailbox'], ['Unread', stats.unread, 'need a first look'], ['High priority', stats.high_priority, 'urgent + high'], ['Pending replies', stats.pending_replies, 'owner review'], ['Action items', stats.action_items, 'open tasks'], ['Follow-ups', stats.follow_ups, 'suggested']].map(([label, value, caption]) => <div className="stat-tile" key={String(label)}><small>{label}</small><strong>{value}</strong><span>{caption}</span></div>)}</div>
      <div className="dashboard-grid"><section className="surface"><div className="surface-heading"><div><h2>Priority distribution</h2><p>Inbox records by verified mock label</p></div><Flag size={17} /></div>{Object.entries(stats.priority_distribution).map(([label, value]) => <div className="bar-row" key={label}><span>{label}</span><div className="bar-track"><i className={`bar-fill ${label.toLowerCase()}`} style={{ width: `${Math.max(5, value / stats.total_emails * 100)}%` }} /></div><b>{value}</b></div>)}</section><section className="surface"><div className="surface-heading"><div><h2>Sender categories</h2><p>Contact-verified sample distribution</p></div><Inbox size={17} /></div><div className="category-list">{Object.entries(stats.category_distribution).map(([label, value]) => <div key={label}><span className="category-mark" />{label}<strong>{value}</strong></div>)}</div></section></div>
      <div className="dashboard-grid lower-grid"><section className="surface"><div className="surface-heading"><div><h2>Recent messages</h2><p>Open a message to inspect the analysis</p></div><button className="text-button" onClick={() => onOpenEmail(emails[0]?.id ?? '')}>Open inbox <ChevronRight size={14} /></button></div><EmailTable emails={emails.slice(0, 5)} onOpenEmail={onOpenEmail} /></section><section className="surface approval-surface"><div className="surface-heading"><div><h2>Pending approvals</h2><p>{stats.pending_approvals} saved drafts await review</p></div><LockKeyhole size={17} /></div>{drafts.filter((draft) => draft.status === 'draft').slice(0, 4).map((draft) => <button className="approval-row" key={draft.id} onClick={() => onOpenEmail(draft.email_id)}><span className="approval-icon"><ReplyIcon /></span><span><strong>{emails.find((row) => row.id === draft.email_id)?.subject ?? draft.email_id}</strong><small>AI draft · requires owner decision</small></span><ChevronRight size={15} /></button>)}{drafts.every((draft) => draft.status !== 'draft') && <p className="quiet-empty">No saved drafts are waiting. Run the agent to prepare a review batch.</p>}</section></div>
      <section className="activity-strip"><Sparkles size={15} /><span>Coordinator ready</span><b>Mock mode</b><span>Human review is required before any draft is approved. No send operation is available.</span></section>
    </>}

    {(view === 'Inbox' || view === 'Priority') && <section className="surface inbox-surface"><div className="inbox-toolbar"><div className="search-field"><Search size={15} /><input aria-label="Search inbox" placeholder="Search sender, subject, or message" value={search} onChange={(event) => setSearch(event.target.value)} /></div><div className="filter-strip">{(view === 'Priority' ? ['All', 'URGENT', 'HIGH', 'MEDIUM'] : ['All', 'Unread', 'High Priority', 'Student', 'Faculty', 'Administration', 'Vendor', 'Needs Reply', 'Action Item']).map((item) => <button key={item} className={filter === item ? 'selected' : ''} onClick={() => setFilter(item)}>{item}</button>)}</div></div><EmailTable emails={view === 'Priority' ? filteredEmails.filter((item) => ['HIGH', 'URGENT'].includes(item.priority)) : filteredEmails} onOpenEmail={onOpenEmail} /></section>}

    {view === 'Email detail' && email && analysis && <div className="detail-layout"><section className="surface message-surface"><div className="message-top"><span className="sender-avatar">{email.sender.slice(0, 1).toUpperCase()}</span><div><strong>{email.sender}</strong><small>to {email.recipients.join(', ')} · {formatDate(email.timestamp)}</small></div><span className={priorityClass(analysis.priority?.priority ?? email.priority)}>{analysis.priority?.priority ?? email.priority}</span></div><h2>{email.subject}</h2><div className="message-body">{email.body}</div><div className="tag-row">{email.tags.map((tag) => <span key={tag}>{tag}</span>)}</div></section><section className="surface analysis-surface"><div className="surface-heading"><div><h2>Agent analysis</h2><p>Structured outputs · confidence-aware</p></div><Sparkles size={17} /></div><div className="analysis-block"><small>CLASSIFICATION</small><strong>{analysis.classification?.sender_category} <span>·</span> {analysis.classification?.content_type}</strong><p>{analysis.classification?.sender_verified ? 'Sender category matched to contacts' : 'Sender needs human verification'} · {Math.round((analysis.classification?.confidence ?? 0) * 100)}% confidence</p></div><div className="analysis-block"><small>PRIORITY & URGENCY</small><strong>{analysis.priority?.priority} · score {analysis.priority?.urgency_score}</strong><p>{analysis.priority?.reason}</p>{analysis.priority?.detected_deadline && <p>Detected signal: {analysis.priority.detected_deadline}</p>}</div><div className="analysis-block"><small>ACTION ITEMS</small>{analysis.action_items?.length ? analysis.action_items.map((item, index) => <p key={index}><Check size={13} /> {item.task} · {item.status}{item.deadline ? ` · ${item.deadline}` : ''}</p>) : <p>No action item detected.</p>}</div><div className="analysis-block"><small>FOLLOW-UP & CALENDAR</small><p>{analysis.follow_up?.recommended ? analysis.follow_up.reason : 'No follow-up suggested.'}</p><p>{analysis.calendar_suggestion?.recommendation}</p></div></section><section className="surface draft-surface"><div className="surface-heading"><div><h2>Proposed reply</h2><p><ShieldCheck size={13} /> AI-generated — requires human approval</p></div><span className="review-badge">{drafts.find((item) => item.email_id === email.id)?.status ?? 'DRAFT ONLY'}</span></div><textarea aria-label="Draft reply content" value={draftBody} onChange={(event) => setDraftBody(event.target.value)} disabled={drafts.some((item) => item.email_id === email.id && item.status !== 'draft')} rows={7} /><div className="draft-explanation">{analysis.draft_reply?.explanation} {analysis.draft_reply?.prior_reply_used && <b>Previous reply used</b>}</div><div className="draft-toolbar"><label>Mailbox owner <input value={owner} onChange={(event) => setOwner(event.target.value)} /></label><div className="draft-actions"><button className="secondary-button" onClick={() => void draftAction('regenerate')} disabled={busy}><RefreshCw size={14} />Regenerate</button><button className="secondary-button" onClick={() => void draftAction('save')} disabled={busy}><FileText size={14} />Save draft</button><button className="danger-button" onClick={() => void draftAction('reject')} disabled={busy}><X size={14} />Reject</button><button className="primary-button" onClick={() => void draftAction('approve')} disabled={busy}><Check size={14} />Approve draft</button></div></div>{drafts.some((item) => item.email_id === email.id && item.status === 'approved') && <div className="locked-banner">Approved by owner. Status remains draft; this application does not send email.</div>}</section></div>}

    {view === 'Action Items' && <section className="surface list-surface"><div className="surface-heading"><div><h2>Open work</h2><p>Items stay pending until a person marks them complete.</p></div><Clock3 size={17} /></div>{actions.map((item, index) => <div className="data-row" key={String(item.id ?? index)}><span className="task-state">○</span><div><strong>{String(item.title ?? item.task ?? 'Action item')}</strong><small>{String(item.owner ?? 'mailbox owner')} · {item.email_id ? `Email ${String(item.email_id)}` : 'Task list'}</small></div><span className="due-date">{String(item.deadline ?? 'No deadline')}</span><span className="status-label">{String(item.status ?? 'pending')}</span></div>)}</section>}

    {view === 'Draft Replies' && <section className="surface list-surface"><div className="surface-heading"><div><h2>Saved drafts</h2><p>Approved drafts remain unsent; decisions are recorded.</p></div><Reply size={17} /></div>{drafts.map((draft) => <button className="data-row row-button" key={draft.id} onClick={() => onOpenEmail(draft.email_id)}><span className="draft-status-dot" /><div><strong>{emails.find((item) => item.id === draft.email_id)?.subject ?? draft.email_id}</strong><small>{draft.source_template ?? 'Original draft'} · confidence {Math.round((draft.confidence ?? 0) * 100)}%</small></div><span className={`status-label ${draft.status}`}>{draft.status}</span><ChevronRight size={15} /></button>)}</section>}

    {view === 'Follow-ups' && <section className="surface list-surface"><div className="surface-heading"><div><h2>Reminder suggestions</h2><p>Suggestions only; no reminders are scheduled automatically.</p></div><Clock3 size={17} /></div>{followUps.length ? followUps.map((item, index) => <button className="data-row row-button" key={String(item.email_id ?? index)} onClick={() => onOpenEmail(String(item.email_id))}><span className="priority-mark high" /><div><strong>{emails.find((row) => row.id === item.email_id)?.subject ?? String(item.email_id)}</strong><small>{String(item.reason)}</small></div><span className="status-label">SUGGESTED</span><ChevronRight size={15} /></button>) : <EmptyState text="Run the organizer to generate follow-up suggestions." />}</section>}

    {view === 'Calendar' && <section className="surface list-surface"><div className="surface-heading"><div><h2>Meeting suggestions</h2><p>Nothing is confirmed or booked automatically.</p></div><CalendarIcon /></div>{calendar.length ? calendar.map((item, index) => <button className="data-row row-button" key={String(item.email_id ?? index)} onClick={() => onOpenEmail(String(item.email_id))}><span className="calendar-date">{String(item.proposed_time ?? 'TBD')}</span><div><strong>{emails.find((row) => row.id === item.email_id)?.subject ?? String(item.email_id)}</strong><small>{String(item.recommendation)}</small></div><span className="status-label">OWNER CONFIRMATION</span><ChevronRight size={15} /></button>) : <EmptyState text="Run the organizer to identify proposed meeting times." />}</section>}

    {view === 'Agent Runs' && <div className="run-layout"><section className="surface run-list"><div className="surface-heading"><div><h2>Run history</h2><p>{runs.length} run(s)</p></div><Sparkles size={17} /></div>{runs.map((run) => <button className={`run-row ${selectedRunId === run.id ? 'selected' : ''}`} key={run.id} onClick={() => setSelectedRunId(run.id)}><span className="run-indicator" /><span><strong>{run.id}</strong><small>{run.status.replaceAll('_', ' ')} · {run.current_node}</small></span><ChevronRight size={15} /></button>)}</section><section className="surface run-detail"><div className="surface-heading"><div><h2>{runDetails?.run.id ?? 'Select a run'}</h2><p>{runDetails ? `${runDetails.run.status.replaceAll('_', ' ')} · ${runDetails.results.length} email results` : 'Run details appear here.'}</p></div>{runDetails && <span className="review-badge">{runDetails.run.status.toUpperCase()}</span>}</div>{runDetails && <><div className="graph-summary"><span><b>{runDetails.merge?.max_observed_workers ?? '—'}</b>peak workers</span><span><b>{runDetails.merge?.duration_ms?.toFixed(0) ?? '—'} ms</b>elapsed</span><span><b>{runDetails.run.retry_count}</b>retries</span><span><b>{runDetails.merge?.failed_email_ids.length ?? 0}</b>failed</span></div><div className="node-list">{(runDetails.results[0]?.nodes ?? []).map((node, index) => <div className="node-row" key={`${node.node}-${index}`}><span className="node-check"><Check size={12} /></span><div><strong>{node.node.replaceAll('_', ' ')}</strong><small>{node.output_summary || node.status}</small></div><span>{node.duration_ms?.toFixed(1) ?? '—'} ms</span></div>)}<div className="node-row waiting"><span className="node-check"><LockKeyhole size={12} /></span><div><strong>HUMAN REVIEW</strong><small>Approval gate · no send action</small></div><span>{runDetails.run.status.replaceAll('_', ' ')}</span></div>{runDetails.run.status === 'completed' && <div className="node-row"><span className="node-check"><Check size={12} /></span><div><strong>ARCHIVE & LOGGING</strong><small>Owner-approved results</small></div><span>completed</span></div>}</div>{runDetails.run.status === 'waiting_for_approval' && <div className="run-decision"><label>Approver <input value={owner} onChange={(event) => setOwner(event.target.value)} /></label><button className="danger-button" onClick={() => void decideRun('reject')} disabled={busy}><X size={14} />Reject batch</button><button className="primary-button" onClick={() => void decideRun('approve')} disabled={busy}><Check size={14} />Approve & archive</button></div>}<div className="result-list"><strong>Fan-in results</strong>{runDetails.results.slice(0, 8).map((result) => <button key={result.email_id} onClick={() => onOpenEmail(result.email_id)}><span className={priorityClass(result.priority.priority)}>{result.priority.priority}</span><span>{emails.find((row) => row.id === result.email_id)?.subject ?? result.email_id}</span><ChevronRight size={14} /></button>)}</div></>}</section></div>}

    {view === 'Audit Logs' && <section className="surface audit-surface"><div className="surface-heading"><div><h2>System trace</h2><p>Every tool call, graph step, approval, and merge event is retained for this server session.</p></div><Clock3 size={17} /></div><div className="audit-head"><span>TIME</span><span>RUN / EMAIL</span><span>AGENT</span><span>ACTION</span><span>STATUS</span></div>{audit.map((entry, index) => <div className="audit-row" key={entry.id ?? index}><span>{formatDate(entry.timestamp)}</span><span>{entry.run_id ?? entry.email_id ?? '—'}</span><span>{entry.agent ?? '—'}</span><span>{entry.action ?? '—'}<small>{entry.details ? JSON.stringify(entry.details).slice(0, 120) : ''}</small></span><span className={`status-label ${String(entry.status ?? '').toLowerCase()}`}>{entry.status ?? 'logged'}</span></div>)}</section>}

    {view === 'Settings' && <section className="settings-grid"><div className="surface setting-row"><span className="setting-symbol"><Inbox size={17} /></span><div><h2>Mailbox connector</h2><p>MockEmailConnector · 20 seeded college messages</p></div><span className="setting-state">CONNECTED</span></div><div className="surface setting-row"><span className="setting-symbol"><ShieldCheck size={17} /></span><div><h2>Human approval</h2><p>Required before draft approval and archive. No send API exists.</p></div><span className="setting-state">ENFORCED</span></div><div className="surface setting-row"><span className="setting-symbol"><Sparkles size={17} /></span><div><h2>AI provider</h2><p>Deterministic mock skills · provider can be added behind the skill interface.</p></div><span className="setting-state">MOCK MODE</span></div><div className="surface setting-row"><span className="setting-symbol"><LockKeyhole size={17} /></span><div><h2>Memory</h2><p>SQLite contacts, prior replies, and email retrieval; current run state is ephemeral.</p></div><span className="setting-state">LOCAL</span></div></section>}

    <div className="view-footer"><span><LockKeyhole size={13} /> AI-generated drafts require human approval · never auto-sent</span><span>{emails.length} MOCK MESSAGES</span></div>
  </div>
}

function EmailTable({ emails, onOpenEmail }: { emails: Email[]; onOpenEmail: (id: string) => void }) {
  return <div className="email-table">{emails.map((email) => <button className={`email-row ${email.read ? '' : 'unread'}`} key={email.id} onClick={() => onOpenEmail(email.id)}><span className="unread-mark" /><span className="email-sender">{email.sender.split('@')[0].replace('.', ' ')}</span><span className="email-content"><strong>{email.subject}</strong><small>{email.body}</small><span className="tag-row">{email.tags.slice(0, 2).map((tag) => <i key={tag}>{tag}</i>)}</span></span><span className="email-meta"><span className={priorityClass(email.priority)}>{email.priority}</span><small>{email.sender_category}</small><small>{formatDate(email.timestamp)}</small></span>{email.requires_reply && <span className="reply-indicator"><ArrowDownRight size={14} /></span>}</button>)}{emails.length === 0 && <EmptyState text="No emails match the selected filter." />}</div>
}

function EmptyState({ text }: { text: string }) { return <div className="quiet-empty">{text}</div> }
function ReplyIcon() { return <Mail size={15} /> }
function CalendarIcon() { return <ArrowUpRight size={17} /> }
