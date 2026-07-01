import './SummaryStats.css'

export default function SummaryStats({ stats }) {
  if (!stats) return null;

  return (
    <div className="summary-stats">
      <div className="stat-item">
        <div className="stat-label">Rolling Avg (3-Session)</div>
        <div className="stat-value">
          {stats.rollingAvg ? `${stats.rollingAvg.toFixed(1)} kg` : '—'}
        </div>
      </div>
      <div className="stat-item">
        <div className="stat-label">RPE (3-Session)</div>
        <div className="stat-value">
          {stats.rpeAvg ? stats.rpeAvg.toFixed(1) : '—'}
        </div>
      </div>
      <div className="stat-item">
        <div className="stat-label">Total Sessions</div>
        <div className="stat-value">{stats.totalSessions || 0}</div>
      </div>
    </div>
  )
}
