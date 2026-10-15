import { useState } from 'react'
import { PERCENT_OPTIONS, weightAtPercent } from '../data/exercises'
import './OneRepMaxPanel.css'

/**
 * Shows the athlete's 1RM for the lift an exercise is based on, lets them
 * record or update it, and offers a % of 1RM picker that turns into kg.
 */
export default function OneRepMaxPanel({ exercise, baseLift, liftOptions = [], onLiftChange, oneRm, percent, onPercentChange, onSaveOneRm, loadError }) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState('')
  const [saving, setSaving] = useState(false)
  const [saveNote, setSaveNote] = useState(null)

  const hasOneRm = typeof oneRm === 'number' && oneRm > 0
  const showInput = editing || !hasOneRm
  const perRep = hasOneRm && percent ? weightAtPercent(oneRm, Number(percent)) : null

  const startEdit = () => {
    setDraft(hasOneRm ? String(oneRm) : '')
    setSaveNote(null)
    setEditing(true)
  }

  const save = async () => {
    const kg = parseFloat(draft)
    if (!(kg > 0 && kg <= 500)) {
      setSaveNote({ kind: 'error', text: 'Enter a 1RM between 0.5 and 500 kg' })
      return
    }
    setSaving(true)
    setSaveNote(null)
    const result = await onSaveOneRm(baseLift, kg)
    setSaving(false)
    setEditing(false)
    setDraft('')
    if (!result.saved) {
      setSaveNote({ kind: 'warn', text: `Couldn't save to your profile (${result.error}). Using ${kg} kg for this session.` })
    }
  }

  return (
    <section className="orm-panel" aria-label="Percentage of one rep max">
      <div className="orm-head">
        <span className="orm-title">% of 1RM</span>
        {baseLift !== exercise && liftOptions.length <= 1 && <span className="orm-based">based on your {baseLift} 1RM</span>}
      </div>

      {liftOptions.length > 1 && (
        <div className="form-group">
          <label htmlFor="orm-lift">Based on your 1RM for</label>
          <select id="orm-lift" className="form-select" value={baseLift} onChange={e => onLiftChange(e.target.value)}>
            {liftOptions.map(l => <option key={l} value={l}>{l}</option>)}
          </select>
        </div>
      )}

      {showInput ? (
        <div className="orm-edit">
          <label htmlFor="orm-input" className="orm-label">{baseLift} 1RM (kg)</label>
          <div className="orm-edit-row">
            <input
              id="orm-input"
              type="number"
              inputMode="decimal"
              step="0.5"
              min="0.5"
              max="500"
              placeholder="e.g. 100"
              value={draft}
              onChange={e => setDraft(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); save() } }}
            />
            <button type="button" className="orm-btn orm-btn-primary" onClick={save} disabled={saving || !draft}>
              {saving ? 'Saving…' : 'Save'}
            </button>
            {editing && hasOneRm && (
              <button type="button" className="orm-btn" onClick={() => setEditing(false)}>Cancel</button>
            )}
          </div>
          {!hasOneRm && (
            <small className="form-help">
              No {baseLift} 1RM recorded yet{loadError ? ' (couldn’t load your 1RMs)' : ''}. Add it to get working weights.
            </small>
          )}
        </div>
      ) : (
        <div className="orm-current">
          <span className="orm-value">{oneRm} kg</span>
          <span className="orm-value-label">{baseLift} 1RM</span>
          <button type="button" className="orm-link" onClick={startEdit}>Update</button>
        </div>
      )}

      {saveNote && <small className={`orm-note orm-note-${saveNote.kind}`}>{saveNote.text}</small>}

      <div className="form-group">
        <label htmlFor="percent_1rm">Working %</label>
        <select
          id="percent_1rm"
          className="form-select"
          value={percent}
          onChange={e => onPercentChange(e.target.value)}
          disabled={!hasOneRm}
        >
          <option value="">{hasOneRm ? 'Choose a percentage…' : 'Add your 1RM first'}</option>
          {PERCENT_OPTIONS.map(p => (
            <option key={p} value={p}>
              {p}%{hasOneRm ? `  ·  ${weightAtPercent(oneRm, p)} kg` : ''}
            </option>
          ))}
        </select>
      </div>

      {perRep !== null && (
        <div className="orm-result" aria-live="polite">
          <span className="orm-result-kg">{perRep} kg</span>
          <span className="orm-result-label">on the bar · {percent}% of {oneRm} kg</span>
        </div>
      )}
    </section>
  )
}
