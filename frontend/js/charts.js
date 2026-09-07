/**
 * Technical Hydrograph Charting Module
 * Renders technical 2D discharge hydrographs using Chart.js with clean engineering styling.
 */

let hydrographChartInstance = null;

function renderHydrographChart(hydrographData) {
  const ctx = document.getElementById('hydrographChart');
  if (!ctx) return;

  if (hydrographChartInstance) {
    hydrographChartInstance.destroy();
  }

  const times = hydrographData.time_minutes || [];
  const flows = hydrographData.discharge_m3s || [];

  hydrographChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: times,
      datasets: [{
        label: 'Discharge Q (m³/s)',
        data: flows,
        borderColor: '#1e40af',
        backgroundColor: 'rgba(30, 64, 175, 0.10)',
        fill: true,
        tension: 0.2,
        borderWidth: 2,
        pointRadius: 1.5,
        pointHoverRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 400 },
      plugins: {
        legend: {
          display: true,
          position: 'top',
          labels: {
            color: '#1e293b',
            boxWidth: 12,
            font: { size: 11, family: 'inherit' }
          }
        },
        tooltip: {
          backgroundColor: '#1e293b',
          titleFont: { size: 11 },
          bodyFont: { size: 11 },
          callbacks: {
            label: (ctx) => `Discharge: ${ctx.parsed.y.toLocaleString()} m³/s at ${ctx.parsed.x} min`
          }
        }
      },
      scales: {
        x: {
          title: {
            display: true,
            text: 'Time (minutes)',
            color: '#475569',
            font: { size: 11, weight: '500' }
          },
          ticks: { color: '#64748b', font: { size: 10 } },
          grid: { color: '#e2e8f0' }
        },
        y: {
          title: {
            display: true,
            text: 'Outflow Discharge (m³/s)',
            color: '#475569',
            font: { size: 11, weight: '500' }
          },
          ticks: { color: '#64748b', font: { size: 10 } },
          grid: { color: '#e2e8f0' },
          beginAtZero: true
        }
      }
    }
  });
}
