import { useEffect, useState } from 'react'
import { fetchAthlete, fetchConsentStatus } from '../services/api'
import RegistrationForm from './RegistrationForm'
import ConsentGate from './ConsentGate'
import './OnboardingGate.css'

const ATHLETE_ID_KEY = 'fitness-optimax-athlete-id'
const REQUIRED_CONSENT = 'data_storage'

function hasRequiredConsent(consents) {
  const required = consents?.find(c => c.consent_type === REQUIRED_CONSENT)
  return Boolean(required?.granted && required?.current)
}

/**
 * Blocks the app (issue #16) until an athlete is registered (issue #18) and
 * has granted the required data_storage consent at the current notice
 * version. Renders as an overlay on top of `children` rather than swapping
 * them out, so a privacy-notice link can open in a new tab without needing
 * its own route to be reachable mid-gate.
 */
export default function OnboardingGate({ children }) {
  const [step, setStep] = useState('loading') // 'loading' | 'register' | 'consent' | 'ready'
  const [athleteId, setAthleteId] = useState(null)

  useEffect(() => {
    let cancelled = false

    async function check() {
      const storedId = localStorage.getItem(ATHLETE_ID_KEY)
      if (!storedId) {
        if (!cancelled) setStep('register')
        return
      }
      try {
        await fetchAthlete(storedId)
        const status = await fetchConsentStatus(storedId)
        if (cancelled) return
        setAthleteId(storedId)
        setStep(hasRequiredConsent(status.consents) ? 'ready' : 'consent')
      } catch (err) {
        if (cancelled) return
        if (err.status === 404) {
          // Stale/deleted id left over from a previous visit — start fresh.
          localStorage.removeItem(ATHLETE_ID_KEY)
          setStep('register')
        } else {
          // A transient API failure shouldn't lock an already-consented
          // returning athlete out of an otherwise-working app.
          setStep('ready')
        }
      }
    }

    check()
    return () => { cancelled = true }
  }, [])

  function handleRegistered(id) {
    localStorage.setItem(ATHLETE_ID_KEY, id)
    setAthleteId(id)
    setStep('consent')
  }

  return (
    <>
      {children}
      {step !== 'ready' && (
        <div className="onboarding-overlay" role="dialog" aria-modal="true" aria-label="Athlete registration and consent">
          <div className="onboarding-card">
            {step === 'loading' && <p className="onboarding-loading">Checking your profile…</p>}
            {step === 'register' && <RegistrationForm onRegistered={handleRegistered} />}
            {step === 'consent' && (
              <ConsentGate athleteId={athleteId} onConsented={() => setStep('ready')} />
            )}
          </div>
        </div>
      )}
    </>
  )
}
