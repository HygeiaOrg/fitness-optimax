import { useEffect, useState } from 'react'
import { fetchWeightClasses, registerAthlete } from '../services/api'
import './OnboardingGate.css'

const SEX_OPTIONS = [
  { value: 'female', label: 'Female' },
  { value: 'male', label: 'Male' },
]

const AGE_OPTIONS = [
  { value: '18_25', label: '18–25' },
  { value: '26_35', label: '26–35' },
  { value: 'masters_35_plus', label: 'Masters (35+)' },
  { value: 'under_18', label: 'Under 18' },
]

export default function RegistrationForm({ onRegistered }) {
  const [weightClasses, setWeightClasses] = useState(null)
  const [loadError, setLoadError] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const [form, setForm] = useState({
    name: '', email: '', sex_category: 'female', age_category: '18_25', weight_category: '',
  })

  useEffect(() => {
    let cancelled = false
    fetchWeightClasses()
      .then(classes => { if (!cancelled) setWeightClasses(classes) })
      .catch(err => { if (!cancelled) setLoadError(err.message) })
    return () => { cancelled = true }
  }, [])

  const classOptions = weightClasses ? weightClasses[form.sex_category] : []

  function handleChange(e) {
    const { name, value } = e.target
    // Weight classes differ by sex category, so a stale selection from the
    // other list must not silently survive the switch.
    if (name === 'sex_category') {
      setForm(prev => ({ ...prev, sex_category: value, weight_category: '' }))
      return
    }
    setForm(prev => ({ ...prev, [name]: value }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      const athlete = await registerAthlete(form)
      onRegistered(athlete.athlete_id)
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form className="onboarding-form" onSubmit={handleSubmit}>
      <h2>Welcome to Fitness OptiMax</h2>
      <p className="onboarding-intro">
        Create your athlete profile for North Tyneside Barbells. You'll be asked
        how your data can be used on the next step.
      </p>

      {error && <div className="form-error">{error}</div>}
      {loadError && <div className="form-error">Couldn't load weight classes: {loadError}</div>}

      <div className="form-group">
        <label htmlFor="athlete-name">Name</label>
        <input id="athlete-name" name="name" value={form.name} onChange={handleChange} required />
      </div>

      <div className="form-group">
        <label htmlFor="athlete-email">Email</label>
        <input id="athlete-email" name="email" type="email" value={form.email} onChange={handleChange} required />
      </div>

      <div className="form-row">
        <div className="form-group">
          <label htmlFor="sex_category">Sex category</label>
          <select
            id="sex_category" name="sex_category" className="form-select"
            value={form.sex_category} onChange={handleChange}
          >
            {SEX_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="age_category">Age category</label>
          <select
            id="age_category" name="age_category" className="form-select"
            value={form.age_category} onChange={handleChange}
          >
            {AGE_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>
      </div>

      <div className="form-group">
        <label htmlFor="weight_category">Weight category</label>
        <select
          id="weight_category" name="weight_category" className="form-select"
          value={form.weight_category} onChange={handleChange} required disabled={!weightClasses}
        >
          <option value="" disabled>Select a weight class…</option>
          {classOptions?.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      <button type="submit" className="primary-button onboarding-submit" disabled={submitting}>
        {submitting ? 'Creating profile…' : 'Continue'}
      </button>
    </form>
  )
}
