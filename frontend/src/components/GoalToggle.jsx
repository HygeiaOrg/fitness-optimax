import { useState } from 'react'
import { updateTrainingGoal } from '../services/api'
import './GoalToggle.css'

export default function GoalToggle({ exerciseGroup, initialGoal, onGoalChange }) {
  const [goal, setGoal] = useState(initialGoal)
  const [isLoading, setIsLoading] = useState(false)

  const handleToggle = async (newGoal) => {
    if (goal === newGoal) return
    setIsLoading(true)
    try {
      await updateTrainingGoal(exerciseGroup, newGoal)
      setGoal(newGoal)
      if (onGoalChange) onGoalChange(newGoal)
    } catch (err) {
      console.error('Failed to update goal', err)
      // Ideally show a toast notification here
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className={`goal-toggle ${isLoading ? 'is-loading' : ''}`}>
      <button
        className={`goal-toggle-btn ${goal === 'STRENGTH' ? 'is-active' : ''}`}
        onClick={() => handleToggle('STRENGTH')}
        disabled={isLoading}
      >
        Strength
      </button>
      <button
        className={`goal-toggle-btn ${goal === 'HYPERTROPHY' ? 'is-active' : ''}`}
        onClick={() => handleToggle('HYPERTROPHY')}
        disabled={isLoading}
      >
        Hypertrophy
      </button>
    </div>
  )
}
