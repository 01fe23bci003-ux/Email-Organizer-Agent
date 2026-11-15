import { useState } from 'react'
import { Activity, ArrowRight, Bell, Check, ChevronDown, CircleHelp, ClipboardList, Inbox, LockKeyhole, Mail, Pencil, Plus, Settings, Sparkles, X, ListChecks, CalendarDays, History, FileClock, Flag, Reply, FlaskConical } from 'lucide-react'
import WorkspaceView, { type ViewName } from './WorkspaceView'
import AdvancedLabsView from './AdvancedLabsView'

type Plan = {
  id: string
  request: string
  goal: string
  clarification_questions: string[]
  steps: string[]
  approval_required: boolean
  status: 'review' | 'locked'
  requirements: {
    mailbox_scope: string
    priority_categories: string[]
    date_range: string
    standard_response_library_available: boolean
  }
  categories: string[]
}

const API = '/api'

export default function App() {
  const [request, setRequest] = useState('Organize my inbox and prepare replies.')
  const [plan, setPlan] = useState<Plan | null>(null)
  const [goal, setGoal] = useState('')
  const [stepsText, setStepsText] = useState('')
  const [editing, setEditing] = useState(false)
  const [mergeVendor, setMergeVendor] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [view, setView] = useState<ViewName>('Dashboard')
  const [selectedEmailId, setSelectedEmailId] = useState<string | null>(null)
  const [lastRunId, setLastRunId] = useState<string | null>(null)

  async function createPlan() {
    setBusy(true)
    setError('')
    try {
      const response = await fetch(`${API}/agent/plan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ request }),
      })
      if (!response.ok) throw new Error('Could not create a plan. Is the backend running?')
      const next: Plan = await response.json()
      setPlan(next)
      setGoal(next.goal)
      setStepsText(next.steps.join('\n'))
      setEditing(false)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Unexpected error')
    } finally {
      setBusy(false)
    }
  }

  async function revisePlan() {
    if (!plan) return
    setBusy(true)
    setError('')
    try {
      const response = await fetch(`${API}/agent/plan/${plan.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ goal, steps: stepsText.split('\n').filter((step) => step.trim()), merge_vendor_into_other: mergeVendor }),
      })
      if (!response.ok) throw new Error('Plan revision could not be saved.')
      setPlan(await response.json())
      setEditing(false)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Unexpected error')
    } finally {
      setBusy(false)
    }
  }

  async function lockPlan() {
    if (!plan) return
    setBusy(true)
    setError('')
    try {
      const response = await fetch(`${API}/agent/plan/${plan.id}/lock`, { method: 'POST' })
      if (!response.ok) throw new Error('Could not lock the plan.')
      setPlan(await response.json())
      setEditing(false)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Unexpected error')
    } finally {
      setBusy(false)
    }
  }

  async function runAgent() {
    if (!plan || plan.status !== 'locked') return
    setBusy(true)
    setError('')
    try {
      const emailsResponse = await fetch(`${API}/emails`)
      if (!emailsResponse.ok) throw new Error('Could not load the mock inbox.')
      const emails = await emailsResponse.json() as Array<{ id: string }>
      const response = await fetch(`${API}/agent/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ plan_id: plan.id, email_ids: emails.map((email) => email.id), max_workers: 4 }),
      })
      if (!response.ok) throw new Error('Agent run failed. Check that the backend is running and the plan is locked.')
      const output = await response.json() as { run: { id: string } }
      setLastRunId(output.run.id)
      setView('Agent Runs')
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Unexpected error')
    } finally {
      setBusy(false)
    }
  }

  const navigation = [
    { label: 'Dashboard', icon: Activity },
    { label: 'Inbox', icon: Inbox },
    { label: 'Priority', icon: Flag },
    { label: 'Action Items', icon: ListChecks },
    { label: 'Draft Replies', icon: Reply },
    { label: 'Follow-ups', icon: FileClock },
    { label: 'Calendar', icon: CalendarDays },
    { label: 'Agent Runs', icon: Sparkles },
    { label: 'Audit Logs', icon: History },
    { label: 'Lab Studio', icon: FlaskConical },
    { label: 'Agent plan', icon: ClipboardList },
    { label: 'Settings', icon: Settings },
  ] as const

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><span className="brand-mark"><Mail size={19} /></span><span>inbox / agent</span></div>
        <div className="workspace-label">WORKSPACE <ChevronDown size={13} /></div>
        <nav aria-label="Main navigation">
          {navigation.map(({ label, icon: Icon }) => <button key={label} className={`nav-item ${view === label ? 'active' : ''}`} onClick={() => setView(label)}><Icon size={17} />{label}{label === 'Inbox' && <span className="nav-count">20</span>}</button>)}
        </nav>
        <div className="sidebar-bottom">
          <div className="lab-chip"><span className="pulse" />LABS 01-14 <span>Agent worklet</span></div>
          <div className="profile"><div className="avatar">AY</div><div><strong>Aman Yaligar</strong><small>Mailbox owner</small></div><ChevronDown size={15} /></div>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div className="crumb">Agent workspace <span>/</span> <strong>{view}</strong></div>
          <div className="top-status"><span className="status-dot" /> Mock mode <span className="top-divider" /> <Bell size={16} aria-label="Notifications" /><div className="top-profile">AM</div></div>
        </header>

        <section className="content">
          {view === 'Lab Studio' ? <AdvancedLabsView /> : view === 'Agent plan' ? <>
          <div className="page-heading">
            <div><div className="eyebrow">LAB 01 <span>·</span> CLARIFY / PLAN / REVIEW</div><h1>Give the inbox a plan.</h1><p>Set the goal, inspect the agent's approach, then lock it before any work begins.</p></div>
            <div className="plan-state"><span className={plan?.status === 'locked' ? 'state-icon locked' : 'state-icon'}>{plan?.status === 'locked' ? <LockKeyhole size={16} /> : <Pencil size={16} />}</span><span><small>PLAN STATUS</small><strong>{plan?.status === 'locked' ? 'Locked' : plan ? 'Under review' : 'Not started'}</strong></span></div>
          </div>

          <div className="work-grid">
            <section className="request-panel">
              <div className="panel-topline"><span className="step-number">01</span><div><h2>Your request</h2><p>Tell the coordinator what outcome you want.</p></div></div>
              <label htmlFor="request" className="field-label">REQUEST</label>
              <textarea id="request" value={request} onChange={(event) => setRequest(event.target.value)} disabled={plan?.status === 'locked'} rows={5} />
              <div className="request-footer"><span><Sparkles size={14} /> Coordinator will clarify gaps</span><button className="primary-button" onClick={createPlan} disabled={busy || request.trim().length < 3 || plan?.status === 'locked'}>{busy ? 'Working…' : plan ? 'Regenerate plan' : 'Create plan'}<ArrowRight size={16} /></button></div>
              {error && <p className="error-message" role="alert">{error}</p>}
            </section>

            <section className="flow-panel">
              <div className="panel-topline"><span className="step-number">02</span><div><h2>Agent loop</h2><p>Planning is reviewed before execution.</p></div></div>
              <div className="flow-list">
                <div className="flow-row done"><span className="flow-node"><Check size={13} /></span><span>Clarify request</span><small>{plan ? 'COMPLETE' : 'READY'}</small></div>
                <div className="flow-connector" />
                <div className={`flow-row ${plan ? 'done' : ''}`}><span className="flow-node">{plan ? <Check size={13} /> : '2'}</span><span>Build execution plan</span><small>{plan ? 'COMPLETE' : 'WAITING'}</small></div>
                <div className="flow-connector" />
                <div className={`flow-row ${plan ? 'current' : ''}`}><span className="flow-node">3</span><span>Review / revise</span><small>{plan ? 'IN REVIEW' : 'WAITING'}</small></div>
                <div className="flow-connector" />
                <div className={`flow-row ${plan?.status === 'locked' ? 'done' : ''}`}><span className="flow-node">{plan?.status === 'locked' ? <Check size={13} /> : '4'}</span><span>Lock plan</span><small>{plan?.status === 'locked' ? 'LOCKED' : 'HUMAN GATE'}</small></div>
              </div>
              <div className="gate-note"><LockKeyhole size={15} /><span>No inbox actions run until you approve and lock this plan.</span></div>
            </section>
          </div>

          {plan ? <section className="plan-panel">
            <div className="plan-header"><div className="panel-topline"><span className="step-number">03</span><div><h2>Execution plan</h2><p>Review each step. You can revise the plan before locking.</p></div></div><span className={`review-badge ${plan.status}`}>{plan.status === 'locked' ? <><LockKeyhole size={13} /> LOCKED</> : <><Pencil size={13} /> REVIEW REQUIRED</>}</span></div>
            <div className="plan-body">
              <div className="clarify-box"><div className="clarify-title"><CircleHelp size={16} /> CLARIFYING QUESTIONS</div>{plan.clarification_questions.map((question, index) => <p key={index}><span>{String(index + 1).padStart(2, '0')}</span>{question}</p>)}</div>
              <div className="requirements-grid"><span>MAILBOX SCOPE<strong>{plan.requirements.mailbox_scope.replaceAll('_', ' ')}</strong></span><span>PRIORITY CATEGORIES<strong>{plan.requirements.priority_categories.join(', ')}</strong></span><span>DATE RANGE<strong>{plan.requirements.date_range.replaceAll('_', ' ')}</strong></span><span>REPLY LIBRARY<strong>{plan.requirements.standard_response_library_available ? 'Available' : 'Not available'}</strong></span></div>
              <div className="goal-field"><label className="field-label" htmlFor="goal">GOAL</label>{editing ? <input id="goal" value={goal} onChange={(event) => setGoal(event.target.value)} /> : <div className="goal-text">{plan.goal}</div>}</div>
              <div className="steps-field"><div className="field-label">PROPOSED STEPS <span>{plan.steps.length} steps</span></div>{editing ? <><textarea aria-label="Plan steps, one per line" value={stepsText} onChange={(event) => setStepsText(event.target.value)} rows={6} /><label className="merge-option"><input type="checkbox" checked={mergeVendor} onChange={(event) => setMergeVendor(event.target.checked)} /> Owner feedback: merge Vendor into Other</label></> : <ol className="steps-list">{plan.steps.map((step, index) => <li key={`${index}-${step}`}><span>{String(index + 1).padStart(2, '0')}</span>{step}</li>)}</ol>}</div>
            </div>
            <div className="plan-actions">{plan.status === 'review' && <>{editing ? <><button className="secondary-button" onClick={() => { setEditing(false); setGoal(plan.goal); setStepsText(plan.steps.join('\n')) }}><X size={15} />Cancel</button><button className="secondary-button" onClick={revisePlan} disabled={busy}><Check size={15} />Save revision</button></> : <button className="secondary-button" onClick={() => setEditing(true)}><Pencil size={15} />Edit plan</button>}<div className="action-spacer" /><button className="primary-button lock-button" onClick={lockPlan} disabled={busy || editing}><LockKeyhole size={15} />Approve & lock plan</button></>}</div>
            {plan.status === 'locked' && <><div className="locked-banner"><Check size={16} /> Plan locked. Execution will process the selected inbox in parallel; no emails will be sent.</div><div className="plan-run-action"><button className="primary-button" onClick={runAgent} disabled={busy}><Sparkles size={15} />{busy ? 'Running parallel workers…' : 'Run organizer on 20 mock emails'}<ArrowRight size={15} /></button>{lastRunId && <span>Latest run: {lastRunId}</span>}</div></>}
          </section> : <section className="empty-plan"><div className="empty-icon"><ClipboardList size={21} /></div><div><strong>Your plan will appear here</strong><p>Submit a request to start the coordinator's clarify → plan → review loop.</p></div><Plus size={18} /></section>}

          <footer className="content-footer"><span><LockKeyhole size={13} /> Draft only · Human approval required for consequential actions</span><span>EMAIL ORGANIZER <b>·</b> LABS 1–8</span></footer>
          </> : <WorkspaceView view={view} selectedEmailId={selectedEmailId} onOpenEmail={(emailId: string) => { setSelectedEmailId(emailId); setView('Email detail') }} />}
        </section>
      </main>
    </div>
  )
}
