import ReactECharts from 'echarts-for-react'
import './SPCChart.css'

export default function SPCChart({ data }) {
  if (!data || !data.sessions || data.sessions.length === 0) return null

  const sessions = data.sessions
  const { cl, ucl, lcl } = data.control_limits

  // Extract series data
  const dates = sessions.map(s => s.workout_date)
  const weights = sessions.map(s => s.total_weight)
  const ma3 = sessions.map(s => s.rolling_avg_3)
  const ma5 = sessions.map(s => s.rolling_avg_5)
  const ma7 = sessions.map(s => s.rolling_avg_7)

  // Identify out of control and golden cross points
  const outOfControlPoints = []
  const goldenCrossPoints = []

  sessions.forEach((s, i) => {
    if (s.is_out_of_control) {
      outOfControlPoints.push({
        coord: [i, s.total_weight],
        value: s.total_weight,
        name: 'Violation'
      })
    }
    if (s.momentum_signal === 'GOLDEN_CROSS') {
      goldenCrossPoints.push({
        value: [i, s.total_weight],
        name: 'Golden Cross'
      })
    }
  })

  // ECharts Option Configuration
  const option = {
    color: ['#773141', '#773141', '#9B4D5E', '#FFB612'], // Main, MA3, MA5, MA7
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#E5E7EB',
      textStyle: { color: '#1A1A1A' },
      axisPointer: { type: 'line', lineStyle: { type: 'dashed', color: '#9CA3AF' } },
      formatter: function (params) {
        let res = `<div style="font-weight:600; margin-bottom:4px;">${params[0].axisValue}</div>`
        params.forEach(p => {
          if (p.value !== undefined && p.value !== null) {
            res += `<div><span style="display:inline-block;margin-right:5px;border-radius:10px;width:9px;height:9px;background-color:${p.color}"></span>${p.seriesName}: ${p.value.toFixed(1)}</div>`
          }
        })
        return res
      }
    },
    legend: {
      data: ['Weight', 'MA3', 'MA5', 'MA7'],
      bottom: 0,
      icon: 'circle',
      textStyle: { color: '#6B7280' }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '10%',
      top: '5%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: '#E5E7EB' } },
      axisLabel: { color: '#6B7280' },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'value',
      scale: true,
      splitLine: { lineStyle: { color: '#F3F4F6' } },
      axisLabel: { color: '#6B7280' }
    },
    series: [
      {
        name: 'Weight',
        type: 'line',
        data: weights,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { width: 2, color: '#773141' },
        itemStyle: { color: '#773141' },
        markLine: {
          silent: true,
          symbol: ['none', 'none'],
          label: { position: 'end', color: '#6B7280' },
          data: [
            { yAxis: cl, name: 'CL', lineStyle: { type: 'dashed', color: '#9CA3AF' } },
            { yAxis: ucl, name: 'UCL', lineStyle: { type: 'dashed', color: '#DC2626' } },
            { yAxis: lcl, name: 'LCL', lineStyle: { type: 'dashed', color: '#DC2626' } }
          ]
        },
        markArea: {
          silent: true,
          itemStyle: { color: 'rgba(220, 38, 38, 0.05)' },
          data: [
            [{ yAxis: ucl }, { yAxis: ucl - (ucl - cl) / 3 }],
            [{ yAxis: lcl }, { yAxis: lcl + (cl - lcl) / 3 }]
          ]
        },
        markPoint: {
          data: [
            ...outOfControlPoints.map(p => ({
              ...p,
              itemStyle: { color: '#DC2626' },
              symbol: 'circle',
              symbolSize: 12
            }))
          ]
        }
      },
      {
        name: 'Golden Cross Pulse',
        type: 'effectScatter',
        coordinateSystem: 'cartesian2d',
        data: goldenCrossPoints,
        symbolSize: 14,
        showEffectOn: 'render',
        rippleEffect: {
          brushType: 'stroke',
          scale: 4,
          period: 4
        },
        itemStyle: {
          color: '#FFB612',
          shadowBlur: 10,
          shadowColor: 'rgba(255, 182, 18, 0.8)'
        },
        zlevel: 1
      },
      {
        name: 'MA3',
        type: 'line',
        data: ma3,
        symbol: 'none',
        lineStyle: { width: 1.5, type: 'solid', color: '#773141', opacity: 0.8 }
      },
      {
        name: 'MA5',
        type: 'line',
        data: ma5,
        symbol: 'none',
        lineStyle: { width: 1.5, type: 'solid', color: '#9B4D5E', opacity: 0.8 }
      },
      {
        name: 'MA7',
        type: 'line',
        data: ma7,
        symbol: 'none',
        lineStyle: { width: 1.5, type: 'solid', color: '#FFB612', opacity: 0.8 }
      }
    ]
  }

  return (
    <div className="spc-chart-container">
      <ReactECharts 
        option={option} 
        style={{ height: '400px', width: '100%' }}
        notMerge={true}
        lazyUpdate={true}
      />
    </div>
  )
}
