import { useState } from 'react'
import { recordConsent } from '../services/api'
import './OnboardingGate.css'

// TODO: swap for the club's real contact address before this reaches real athletes.
const PRIVACY_CONTACT = '[club contact email]'

export default function ConsentGate({ athleteId, onConsented }) {
  const [storeData, setStoreData] = useState(false)
  const [shareLogs, setShareLogs] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    if (!storeData) return
    setError(null)
    setSubmitting(true)
    try {
      // Both decisions are recorded, even "no" for the optional one — that's
      // an explicit choice at this notice_version, not an unanswered question.
      await recordConsent(athleteId, 'data_storage', storeData)
      await recordConsent(athleteId, 'share_logs', shareLogs)
      onConsented()
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form className="onboarding-form" onSubmit={handleSubmit}>
      <h2>Your data, how we use it</h2>
      <p className="onboarding-intro">
        Fitness OptiMax is run by North Tyneside Barbells. We collect your name,
        email, age and weight category, and the lifts, sets, loads and session
        notes you log, to calculate your training targets and track your
        progress. Only you and your coach can see this unless you choose to
        share it below. It's kept until you withdraw consent or ask us to
        delete it.
      </p>

      {error && <div className="form-error">{error}</div>}

      <label className="onboarding-checkbox">
        <input type="checkbox" checked={storeData} onChange={e => setStoreData(e.target.checked)} />
        <span><strong>Required.</strong> Store and use my training data to track my performance.</span>
      </label>

      <label className="onboarding-checkbox">
        <input type="checkbox" checked={shareLogs} onChange={e => setShareLogs(e.target.checked)} />
        <span><strong>Optional.</strong> Show my lift logs to other club members.</span>
      </label>

      <p className="onboarding-footnote">
        Read the <a href="/privacy" target="_blank" rel="noopener noreferrer">full privacy notice</a>.
        Questions, or want your data deleted? Email {PRIVACY_CONTACT}.
      </p>

      <button type="submit" className="primary-button onboarding-submit" disabled={!storeData || submitting}>
        {submitting ? 'Saving…' : 'Accept and continue'}
      </button>
    </form>
  )
}
