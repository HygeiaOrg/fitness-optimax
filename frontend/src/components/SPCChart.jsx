import ReactECharts from 'echarts-for-react'
import './SPCChart.css'

// North Tyneside Barbells theme — mirrors the tokens in index.css.
// ECharts draws to canvas, so it needs literal colours rather than CSS vars.
const C = {
  line: '#46BCFF',
  ma3: '#8BD3FF',
  ma5: '#2E86C1',
  ma7: '#FFFFFF',
  limit: '#FF5C63',
  zoneA: 'rgba(255, 92, 99, 0.06)',
  golden: '#FFFFFF',
  goldenGlow: 'rgba(255, 255, 255, 0.8)',
  text: '#FFFFFF',
  secondary: '#B4B4B4',
  muted: '#8A8D93',
  border: '#2A2C30',
  grid: '#1E2023',
  tooltipBg: 'rgba(18, 19, 21, 0.96)',
  font: 'Montserrat, sans-serif',
}

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
    color: [C.line, C.ma3, C.ma5, C.ma7], // Main, MA3, MA5, MA7
    tooltip: {
      trigger: 'axis',
      backgroundColor: C.tooltipBg,
      borderColor: C.border,
      textStyle: { color: C.text, fontFamily: C.font },
      axisPointer: { type: 'line', lineStyle: { type: 'dashed', color: C.muted } },
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
      textStyle: { color: C.secondary, fontFamily: C.font }
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
      axisLine: { lineStyle: { color: C.border } },
      axisLabel: { color: C.secondary, fontFamily: C.font },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'value',
      scale: true,
      splitLine: { lineStyle: { color: C.grid } },
      axisLabel: { color: C.secondary, fontFamily: C.font }
    },
    series: [
      {
        name: 'Weight',
        type: 'line',
        data: weights,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { width: 2, color: C.line },
        itemStyle: { color: C.line },
        markLine: {
          silent: true,
          symbol: ['none', 'none'],
          label: { position: 'end', color: C.secondary, fontFamily: C.font },
          data: [
            { yAxis: cl, name: 'CL', lineStyle: { type: 'dashed', color: C.muted } },
            { yAxis: ucl, name: 'UCL', lineStyle: { type: 'dashed', color: C.limit } },
            { yAxis: lcl, name: 'LCL', lineStyle: { type: 'dashed', color: C.limit } }
          ]
        },
        markArea: {
          silent: true,
          itemStyle: { color: C.zoneA },
          data: [
            [{ yAxis: ucl }, { yAxis: ucl - (ucl - cl) / 3 }],
            [{ yAxis: lcl }, { yAxis: lcl + (cl - lcl) / 3 }]
          ]
        },
        markPoint: {
          data: [
            ...outOfControlPoints.map(p => ({
              ...p,
              itemStyle: { color: C.limit },
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
          color: C.golden,
          shadowBlur: 10,
          shadowColor: C.goldenGlow
        },
        zlevel: 1
      },
      {
        name: 'MA3',
        type: 'line',
        data: ma3,
        symbol: 'none',
        lineStyle: { width: 1.5, type: 'solid', color: C.ma3, opacity: 0.8 },
        itemStyle: { color: C.ma3 }  // keeps the legend swatch in sync with the line
      },
      {
        name: 'MA5',
        type: 'line',
        data: ma5,
        symbol: 'none',
        lineStyle: { width: 1.5, type: 'solid', color: C.ma5, opacity: 0.8 },
        itemStyle: { color: C.ma5 }  // keeps the legend swatch in sync with the line
      },
      {
        name: 'MA7',
        type: 'line',
        data: ma7,
        symbol: 'none',
        lineStyle: { width: 1.5, type: 'solid', color: C.ma7, opacity: 0.8 },
        itemStyle: { color: C.ma7 }  // keeps the legend swatch in sync with the line
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
