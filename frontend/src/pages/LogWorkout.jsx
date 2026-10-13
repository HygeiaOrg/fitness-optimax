import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Header from '../components/Header'
import OneRepMaxPanel from '../components/OneRepMaxPanel'
import { fetchOneRepMaxes, logWorkout, saveOneRepMax } from '../services/api'
import { EXERCISE_CATEGORIES, baseLiftFor, usesOneRm, weightAtPercent } from '../data/exercises'
import './LogWorkout.css'

export default function LogWorkout() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  
  const [formData, setFormData] = useState({
    athlete_name: 'John Hartley', // Default for now
    exercise_group: '',
    sets: '',
    total_reps: '',
    total_weight: '',
    rpe: ''
  })

  // 1RMs keyed by lift, the chosen working %, and whether Total Weight is
  // being filled from that % (stops as soon as the athlete types their own).
  const [oneRms, setOneRms] = useState({})
  const [oneRmLoadError, setOneRmLoadError] = useState(null)
  const [percent, setPercent] = useState('')
  const [weightAuto, setWeightAuto] = useState(true)

  useEffect(() => {
    let cancelled = false
    fetchOneRepMaxes(formData.athlete_name)
      .then(map => { if (!cancelled) { setOneRms(map); setOneRmLoadError(null) } })
      .catch(err => { if (!cancelled) setOneRmLoadError(err.message) })
    return () => { cancelled = true }
  }, [formData.athlete_name])

  const baseLift = formData.exercise_group ? baseLiftFor(formData.exercise_group) : null
  const oneRm = baseLift ? oneRms[baseLift] : undefined

  // Total Weight is session volume: kg on the bar × total reps.
  // While auto is on, a value that can't be worked out any more (no %, reps
  // or 1RM) is cleared rather than left behind from a previous choice.
  const autoTotal = (data, pct, rm, auto) => {
    if (!auto) return data
    const reps = parseInt(data.total_reps)
    if (!pct || !rm || !(reps > 0)) return { ...data, total_weight: '' }
    return { ...data, total_weight: String(weightAtPercent(rm, Number(pct)) * reps) }
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    if (name === 'exercise_group') {
      setPercent('')
      setFormData(prev => (weightAuto ? { ...prev, exercise_group: value, total_weight: '' } : { ...prev, exercise_group: value }))
      return
    }
    if (name === 'total_weight') setWeightAuto(false)
    setFormData(prev => autoTotal({ ...prev, [name]: value }, percent, oneRm, name === 'total_weight' ? false : weightAuto))
  }

  const handlePercentChange = (value) => {
    setPercent(value)
    setWeightAuto(true)
    setFormData(prev => autoTotal(prev, value, oneRm, true))
  }

  const handleSaveOneRm = async (lift, kg) => {
    setOneRms(prev => ({ ...prev, [lift]: kg }))
    setFormData(prev => autoTotal(prev, percent, kg, weightAuto))
    try {
      await saveOneRepMax(formData.athlete_name, lift, kg)
      return { saved: true }
    } catch (err) {
      return { saved: false, error: err.message }
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    
    try {
      // Basic validation
      if (!formData.exercise_group || !formData.sets || !formData.total_reps || !formData.total_weight || !formData.rpe) {
        throw new Error('Please fill in all fields')
      }
      
      await logWorkout({
        athlete_name: formData.athlete_name,
        exercise_group: formData.exercise_group,
        sets: parseInt(formData.sets),
        total_reps: parseInt(formData.total_reps),
        total_weight: parseFloat(formData.total_weight),
        rpe: parseInt(formData.rpe)
      })
      
      // Success, go back to dashboard
      navigate('/')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="log-workout-page animate-fade-in">
      <Header 
        title="Log Workout" 
        backTo="/"
        subtitle="Record your session data"
      />

      <main className="log-workout-main">
        <form className="log-workout-form" onSubmit={handleSubmit}>
          {error && <div className="form-error">{error}</div>}
          
          <div className="form-group">
            <label htmlFor="exercise_group">Exercise</label>
            <select
              id="exercise_group"
              name="exercise_group"
              value={formData.exercise_group}
              onChange={handleChange}
              required
              className="form-select"
            >
              <option value="" disabled>Select an exercise…</option>
              {EXERCISE_CATEGORIES.map(category => (
                <optgroup key={category.label} label={category.label}>
                  {category.exercises.map(exercise => (
                    <option key={exercise} value={exercise}>{exercise}</option>
                  ))}
                </optgroup>
              ))}
            </select>
          </div>

          {formData.exercise_group && usesOneRm(formData.exercise_group) && (
            <OneRepMaxPanel
              key={formData.exercise_group}
              exercise={formData.exercise_group}
              baseLift={baseLift}
              oneRm={oneRm}
              percent={percent}
              onPercentChange={handlePercentChange}
              onSaveOneRm={handleSaveOneRm}
              loadError={oneRmLoadError}
            />
          )}
          
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="sets">Sets</label>
              <input 
                type="number" 
                id="sets" 
                name="sets" 
                min="1"
                placeholder="e.g. 4"
                value={formData.sets}
                onChange={handleChange}
                required
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="total_reps">
                Total Reps
                <span className="label-hint"> (all sets combined)</span>
              </label>
              <input 
                type="number" 
                id="total_reps" 
                name="total_reps" 
                min="1"
                placeholder="e.g. 32"
                value={formData.total_reps}
                onChange={handleChange}
                required
              />
              {formData.sets && formData.total_reps && (
                <small className="form-help reps-hint">
                  ≈ {Math.round(parseInt(formData.total_reps) / parseInt(formData.sets))} reps per set
                </small>
              )}
            </div>
          </div>
          
          <div className="form-group">
            <label htmlFor="total_weight">Total Weight (kg)</label>
            <input 
              type="number" 
              id="total_weight" 
              name="total_weight" 
              step="0.1"
              min="0"
              placeholder="e.g. 240"
              value={formData.total_weight}
              onChange={handleChange}
              required
            />
            {percent && oneRm && weightAuto && formData.total_reps && (
              <small className="form-help reps-hint">
                Auto: {weightAtPercent(oneRm, Number(percent))} kg × {formData.total_reps} reps. Type to override.
              </small>
            )}
            {percent && oneRm && weightAuto && !formData.total_reps && (
              <small className="form-help">Enter total reps to fill this in from your {percent}%.</small>
            )}
          </div>
          
          <div className="form-group">
            <label htmlFor="rpe">RPE (1-10)</label>
            <input 
              type="number" 
              id="rpe" 
              name="rpe" 
              min="1"
              max="10"
              placeholder="Rate of Perceived Exertion"
              value={formData.rpe}
              onChange={handleChange}
              required
            />
            <small className="form-help">10 = Absolute maximum effort</small>
          </div>
          
          <button 
            type="submit" 
            className="primary-button submit-button"
            disabled={loading}
          >
            {loading ? 'Saving...' : 'Save Workout'}
          </button>
        </form>
      </main>
    </div>
  )
}
