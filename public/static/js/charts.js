// Chart.js presets matching the dashboard design (blue rounded bars, quiet axes).

function shortDate(iso) {
  const d = new Date(`${iso}T00:00:00Z`);
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric", timeZone: "UTC" });
}

function seriesChart(canvas, series) {
  // series: [{label, color, data: [{date, count}]}]
  if (!window.Chart || !canvas) return null;
  const labels = series[0].data.map((p) => shortDate(p.date));
  const many = labels.length > 31;
  return new Chart(canvas, {
    type: "bar",
    data: {
      labels,
      datasets: series.map((s) => ({
        label: s.label,
        data: s.data.map((p) => p.count),
        backgroundColor: s.color,
        hoverBackgroundColor: "#0F4FD9",
        borderRadius: many ? 3 : 6,
        borderSkipped: false,
        maxBarThickness: 18,
        categoryPercentage: 0.7,
        barPercentage: 0.85,
      })),
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { display: false }, // pages render their own legend
        tooltip: {
          backgroundColor: "#101010", padding: 10, cornerRadius: 8, displayColors: series.length > 1,
          titleFont: { size: 11, weight: "500" }, bodyFont: { size: 13, weight: "600" },
        },
      },
      scales: {
        x: {
          grid: { display: false }, border: { display: false },
          ticks: { color: "#9CA3AF", font: { size: 11 }, maxRotation: 0, autoSkip: true, maxTicksLimit: many ? 8 : 10 },
        },
        y: {
          beginAtZero: true, border: { display: false },
          grid: { color: "#F0F0F0" },
          ticks: { color: "#9CA3AF", font: { size: 11 }, precision: 0, maxTicksLimit: 5 },
        },
      },
    },
  });
}

function doughnutChart(canvas, rows) {
  if (!window.Chart || !canvas || !rows.length) return null;
  const palette = ["#1662FF", "#8AADFF", "#3A3F47", "#B9CEFF", "#0C3FB0", "#D6D6D6"];
  return new Chart(canvas, {
    type: "doughnut",
    data: {
      labels: rows.map((r) => r.label),
      datasets: [{ data: rows.map((r) => r.count), backgroundColor: palette, borderWidth: 0, hoverOffset: 4 }],
    },
    options: {
      cutout: "72%",
      plugins: {
        legend: { position: "bottom", labels: { usePointStyle: true, pointStyle: "circle", boxWidth: 8, color: "#6B7280", font: { size: 12 } } },
        tooltip: { backgroundColor: "#101010", padding: 10, cornerRadius: 8 },
      },
    },
  });
}
