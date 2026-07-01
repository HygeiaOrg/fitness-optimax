import './AlertBadge.css'

const ALERT_CONFIG = {
  INCREASE_LOAD: { label: '↑ Increase', variant: 'burgundy' },
  SLIGHT_INCREASE: { label: '↑ Slight', variant: 'burgundy-light' },
  MICRO_INCREASE: { label: '↑ Micro', variant: 'burgundy-faint' },
  MAINTAIN: { label: '→ Maintain', variant: 'neutral' },
  NUDGE_REDUCE_REPS: { label: '⚡ Fewer reps', variant: 'gold' },
  NUDGE_INCREASE_REPS: { label: '⚡ More reps', variant: 'gold' },
  EXERCISE_ROTATION: { label: '🔄 Switch', variant: 'danger' },
  REVIEW_REQUIRED: { label: '⚠ Review', variant: 'danger' },
}

export default function AlertBadge({ alertType, momentum, compact = false }) {
  const isGolden = momentum === 'GOLDEN_CROSS'
  const config = ALERT_CONFIG[alertType] || ALERT_CONFIG.MAINTAIN

  if (isGolden) {
    return (
      <span className={`alert-badge alert-badge--golden ${compact ? 'alert-badge--compact' : ''}`} id={`alert-${alertType}`}>
        🔥 On Fire
      </span>
    )
  }

  return (
    <span className={`alert-badge alert-badge--${config.variant} ${compact ? 'alert-badge--compact' : ''}`} id={`alert-${alertType}`}>
      {config.label}
    </span>
  )
}
