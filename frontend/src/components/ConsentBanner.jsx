import { useEffect, useState } from 'react'
import './ConsentBanner.css'

const CONSENT_KEY = 'fitness-optimax-consent'

export default function ConsentBanner() {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    if (!localStorage.getItem(CONSENT_KEY)) {
      setVisible(true)
    }
  }, [])

  function accept() {
    localStorage.setItem(CONSENT_KEY, JSON.stringify({ accepted: true, at: new Date().toISOString() }))
    setVisible(false)
  }

  if (!visible) return null

  return (
    <div className="consent-banner" role="dialog" aria-live="polite" aria-label="Data consent notice">
      <p className="consent-text">
        Fitness OptiMax stores the workout data you log (exercises, weights, reps and RPE) in a private
        database so it can calculate your training targets and progress charts. By continuing to use this
        app, you consent to that data being collected and processed for this purpose.
      </p>
      <button type="button" className="primary-button consent-accept" onClick={accept}>
        Accept
      </button>
    </div>
  )
}
