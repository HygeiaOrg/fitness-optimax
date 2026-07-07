import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Header from '../components/Header'
import { logWorkout } from '../services/api'
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

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
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
            <label htmlFor="exercise_group">Exercise Group</label>
            <input 
              type="text" 
              id="exercise_group" 
              name="exercise_group" 
              placeholder="e.g. Upper Body, Chest"
              value={formData.exercise_group}
              onChange={handleChange}
              required
            />
          </div>
          
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="sets">Sets</label>
              <input 
                type="number" 
                id="sets" 
                name="sets" 
                min="1"
                placeholder="e.g. 3"
                value={formData.sets}
                onChange={handleChange}
                required
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="total_reps">Total Reps</label>
              <input 
                type="number" 
                id="total_reps" 
                name="total_reps" 
                min="1"
                placeholder="e.g. 24"
                value={formData.total_reps}
                onChange={handleChange}
                required
              />
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
