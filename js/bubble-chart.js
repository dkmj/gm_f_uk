/**
 * bubble-chart.js — Utökat D3.js v7 bubbeldiagram för Klimatbudget Uppsala
 * Dynamiska axlar, legendfilter och play/pause-animation.
 */

const SECTOR_COLORS = {
  'Transport':           '#2B7CE9',
  'Energi':              '#F5A623',
  'Bygg och anläggning': '#8B6D5C',
  'Jord- och skogsbruk': '#2D8A4E',
  'Konsumtion':          '#9B59B6',
  'Övriga områden':      '#95A5A6',
};

const MARGIN = { top: 20, right: 20, bottom: 50, left: 65 };

// ── Globalt tillstånd ────────────────────────────────────────────────────────

let allData = [];
let metadata = {};
let hiddenAreas = new Set();
let currentYear = 2024;
let xDim = 'co2e_kton';
let yDim = 'share_pct';
let sizeDim = 'population';
let playInterval = null;
let prefersReducedMotion = false;

// ── Datainläsning ────────────────────────────────────────────────────────────

async function loadData() {
  try {
    const response = await fetch('data/bubble_data.json');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const json = await response.json();
    allData = json.data || [];
    metadata = json.metadata || {};
    if (allData.length === 0) {
      showError('Data kunde inte laddas. Kontrollera att data/bubble_data.json finns.');
      return;
    }
    prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    initChart();
  } catch (err) {
    showError('Data kunde inte laddas. Kontrollera att data/bubble_data.json finns.');
  }
}

function showError(message) {
  const el = document.getElementById('error-container');
  el.textContent = message;
  el.classList.add('visible');
}

// ── Initiering ───────────────────────────────────────────────────────────────

function initChart() {
  const years = [...new Set(allData.map(d => d.year))].sort((a, b) => a - b);
  currentYear = years[years.length - 1];

  const slider = document.getElementById('year-slider');
  slider.min = years[0];
  slider.max = years[years.length - 1];
  slider.value = currentYear;
  document.getElementById('year-display').textContent = currentYear;

  slider.addEventListener('input', () => {
    pauseAnimation();
    currentYear = +slider.value;
    document.getElementById('year-display').textContent = currentYear;
    updateChart();
  });

  // Play-knapp
  const playBtn = document.getElementById('play-btn');
  if (years.length <= 1) {
    playBtn.disabled = true;
    playBtn.title = 'Animering kräver data för flera år';
  } else {
    playBtn.addEventListener('click', togglePlay);
  }

  populateDropdowns();
  buildLegend('legend-desktop');
  buildLegend('legend-mobile');
  updateChart();

  window.addEventListener('resize', () => {
    if (allData.length > 0) updateChart();
  });
}

// ── Dropdowns ────────────────────────────────────────────────────────────────

function getAvailableDimensions() {
  const dims = metadata.dimensions || {};
  const numericDims = Object.keys(dims).filter(key => {
    return allData.some(d => !hiddenAreas.has(d.area) && d[key] !== null && d[key] !== undefined);
  });
  return numericDims;
}

function populateDropdowns() {
  const dims = getAvailableDimensions();
  const dimLabels = metadata.dimensions || {};

  const desktopIds = ['x-axis-select', 'y-axis-select', 'size-select'];
  const mobileIds = ['x-axis-mobile', 'y-axis-mobile', 'size-mobile'];
  const defaults = [xDim, yDim, sizeDim];

  [desktopIds, mobileIds].forEach(ids => {
    ids.forEach((id, i) => {
      const select = document.getElementById(id);
      if (!select) return;
      select.innerHTML = '';

      // "Lika stor" som alternativ för storlek
      if (i === 2) {
        const opt = document.createElement('option');
        opt.value = '_equal';
        opt.textContent = 'Lika stor';
        select.appendChild(opt);
      }

      dims.forEach(dim => {
        const opt = document.createElement('option');
        opt.value = dim;
        opt.textContent = dimLabels[dim]?.label || dim;
        if (dim === defaults[i]) opt.selected = true;
        select.appendChild(opt);
      });

      select.addEventListener('change', () => {
        pauseAnimation();
        const val = select.value;
        if (i === 0) xDim = val;
        if (i === 1) yDim = val;
        if (i === 2) sizeDim = val;
        syncDropdowns(i, val);
        updateChart();
      });
    });
  });
}

function syncDropdowns(index, value) {
  const ids = [
    ['x-axis-select', 'x-axis-mobile'],
    ['y-axis-select', 'y-axis-mobile'],
    ['size-select', 'size-mobile'],
  ];
  ids[index].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = value;
  });
}

// ── Legend ────────────────────────────────────────────────────────────────────

function buildLegend(containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = '';

  Object.entries(SECTOR_COLORS).forEach(([area, color]) => {
    const btn = document.createElement('button');
    btn.className = 'legend-item';
    btn.setAttribute('role', 'checkbox');
    btn.setAttribute('aria-checked', 'true');
    btn.innerHTML = `<span class="legend-dot" style="background:${color}"></span>${area}`;

    btn.addEventListener('click', () => {
      if (hiddenAreas.has(area)) {
        hiddenAreas.delete(area);
        btn.classList.remove('dimmed');
        btn.setAttribute('aria-checked', 'true');
      } else {
        hiddenAreas.add(area);
        btn.classList.add('dimmed');
        btn.setAttribute('aria-checked', 'false');
      }
      updateChart();
    });

    container.appendChild(btn);
  });
}

// ── Play/pause-animation ─────────────────────────────────────────────────────

function togglePlay() {
  if (playInterval) {
    pauseAnimation();
  } else {
    startAnimation();
  }
}

function startAnimation() {
  const years = [...new Set(allData.map(d => d.year))].sort((a, b) => a - b);
  const maxYear = years[years.length - 1];

  if (currentYear >= maxYear) {
    currentYear = years[0];
  }

  const btn = document.getElementById('play-btn');
  btn.textContent = '⏸';
  btn.setAttribute('aria-label', 'Pausa animation');

  function step() {
    const nextIndex = years.indexOf(currentYear) + 1;
    if (nextIndex >= years.length) {
      pauseAnimation();
      return;
    }
    currentYear = years[nextIndex];
    document.getElementById('year-slider').value = currentYear;
    document.getElementById('year-display').textContent = currentYear;
    updateChart(true);
  }

  step();
  playInterval = setInterval(step, 1200);
}

function pauseAnimation() {
  if (playInterval) {
    clearInterval(playInterval);
    playInterval = null;
  }
  const btn = document.getElementById('play-btn');
  btn.textContent = '▶';
  btn.setAttribute('aria-label', 'Spela animation');
}

// ── Diagramuppdatering ───────────────────────────────────────────────────────

function updateChart(animated = false) {
  const chartContainer = document.querySelector('.chart-container');
  const width = chartContainer.clientWidth || 600;
  const height = Math.min(500, width * 0.65);
  const isMobile = window.innerWidth < 1024;

  const innerW = width - MARGIN.left - MARGIN.right;
  const innerH = height - MARGIN.top - MARGIN.bottom;

  // Filtrera data
  const yearData = allData.filter(d =>
    d.year === currentYear &&
    !hiddenAreas.has(d.area) &&
    d[xDim] !== null && d[xDim] !== undefined &&
    d[yDim] !== null && d[yDim] !== undefined
  );

  // Visa/dölj tomma tillstånd
  const emptyState = document.getElementById('empty-state');
  if (yearData.length === 0) {
    emptyState.classList.add('visible');
  } else {
    emptyState.classList.remove('visible');
  }

  // Skalor — domän baserad på ALL data (stabila skalor)
  const allVisible = allData.filter(d => d[xDim] !== null && d[yDim] !== null);

  const xExtent = d3.extent(allVisible, d => d[xDim]);
  const yExtent = d3.extent(allVisible, d => d[yDim]);

  const xScale = d3.scaleLinear()
    .domain([0, (xExtent[1] || 1) * 1.1])
    .range([0, innerW])
    .nice();

  const yScale = d3.scaleLinear()
    .domain([0, (yExtent[1] || 1) * 1.1])
    .range([innerH, 0])
    .nice();

  let rScale;
  if (sizeDim === '_equal') {
    rScale = () => isMobile ? 18 : 28;
  } else {
    const sizeValues = allData.filter(d => d[sizeDim] !== null).map(d => d[sizeDim]);
    const maxSize = d3.max(sizeValues) || 1;
    rScale = d3.scaleSqrt()
      .domain([0, maxSize])
      .range([6, isMobile ? 28 : 45]);
  }

  // SVG
  const svgEl = d3.select('#bubble-chart');
  const transitionDuration = (animated && !prefersReducedMotion) ? 800 : 0;

  // Första rendering — rensa allt
  if (svgEl.select('g.chart-g').empty()) {
    svgEl.selectAll('*:not(title)').remove();
    svgEl
      .attr('width', width)
      .attr('height', height)
      .attr('viewBox', `0 0 ${width} ${height}`);
    svgEl.append('g').attr('class', 'chart-g')
      .attr('transform', `translate(${MARGIN.left},${MARGIN.top})`);
    svgEl.select('g.chart-g').append('g').attr('class', 'x-axis-g')
      .attr('transform', `translate(0,${innerH})`);
    svgEl.select('g.chart-g').append('g').attr('class', 'y-axis-g');
    svgEl.select('g.chart-g').append('text').attr('class', 'x-label');
    svgEl.select('g.chart-g').append('text').attr('class', 'y-label');
  } else {
    svgEl.attr('width', width).attr('height', height).attr('viewBox', `0 0 ${width} ${height}`);
  }

  const g = svgEl.select('g.chart-g');
  const dimLabels = metadata.dimensions || {};

  // Axlar
  const xAxisG = g.select('.x-axis-g');
  xAxisG.transition().duration(transitionDuration)
    .call(d3.axisBottom(xScale).ticks(6));
  xAxisG.select('.domain').attr('stroke', '#DDE0E3');
  xAxisG.selectAll('text').style('fill', '#4C576A').style('font-size', '0.8rem');

  const yAxisG = g.select('.y-axis-g');
  yAxisG.transition().duration(transitionDuration)
    .call(d3.axisLeft(yScale).ticks(6));
  yAxisG.select('.domain').attr('stroke', '#DDE0E3');
  yAxisG.selectAll('text').style('fill', '#4C576A').style('font-size', '0.8rem');

  // Axeletiketter
  g.select('.x-label')
    .attr('x', innerW / 2)
    .attr('y', innerH + 40)
    .attr('text-anchor', 'middle')
    .style('font-size', '0.85rem')
    .style('fill', '#4C576A')
    .text(dimLabels[xDim]?.label || xDim);

  g.select('.y-label')
    .attr('transform', 'rotate(-90)')
    .attr('x', -innerH / 2)
    .attr('y', -MARGIN.left + 16)
    .attr('text-anchor', 'middle')
    .style('font-size', '0.85rem')
    .style('fill', '#4C576A')
    .text(dimLabels[yDim]?.label || yDim);

  // Bubblor (join-pattern med transition)
  const tooltip = document.getElementById('tooltip');
  const detailPanel = document.getElementById('detail-panel');

  const circles = g.selectAll('circle.bubble')
    .data(yearData, d => d.area);

  circles.exit()
    .transition().duration(transitionDuration)
    .attr('r', 0)
    .remove();

  const enter = circles.enter()
    .append('circle')
    .attr('class', 'bubble')
    .attr('cx', d => xScale(d[xDim]))
    .attr('cy', d => yScale(d[yDim]))
    .attr('r', 0)
    .attr('fill', d => SECTOR_COLORS[d.area] || '#95A5A6')
    .attr('fill-opacity', 0.75)
    .attr('stroke', d => SECTOR_COLORS[d.area] || '#95A5A6')
    .attr('stroke-width', 1.5)
    .attr('tabindex', 0)
    .attr('role', 'button')
    .style('cursor', 'pointer');

  const merged = enter.merge(circles);

  merged
    .attr('aria-label', d => buildAriaLabel(d))
    .transition().duration(transitionDuration)
    .attr('cx', d => xScale(d[xDim]))
    .attr('cy', d => yScale(d[yDim]))
    .attr('r', d => {
      if (sizeDim === '_equal') return rScale();
      return d[sizeDim] !== null ? rScale(d[sizeDim]) : rScale(0);
    });

  // Event-handlers (på ej-övergångande element)
  merged
    .on('mouseenter', function(event, d) {
      if (window.innerWidth >= 1024) {
        tooltip.innerHTML = buildTooltipHTML(d);
        tooltip.classList.add('visible');
        tooltip.setAttribute('aria-hidden', 'false');
      }
    })
    .on('mousemove', function(event) {
      if (window.innerWidth >= 1024) {
        const rect = chartContainer.getBoundingClientRect();
        let left = event.clientX - rect.left + 12;
        let top = event.clientY - rect.top - 10;
        if (left + 260 > chartContainer.clientWidth) left -= 280;
        tooltip.style.left = `${left}px`;
        tooltip.style.top = `${top}px`;
      }
    })
    .on('mouseleave', function() {
      tooltip.classList.remove('visible');
      tooltip.setAttribute('aria-hidden', 'true');
    })
    .on('click', function(event, d) {
      showDetailPanel(d);
    })
    .on('keydown', function(event, d) {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        showDetailPanel(d);
      }
    });

  // Tillgänglig sammanfattning
  updateSummary(yearData);
}

// ── Hjälpfunktioner ──────────────────────────────────────────────────────────

function buildTooltipHTML(d) {
  const dims = metadata.dimensions || {};
  let html = `<strong>${d.area}</strong> (${d.year})<br>`;

  Object.entries(dims).forEach(([key, info]) => {
    if (d[key] !== null && d[key] !== undefined) {
      const val = typeof d[key] === 'number'
        ? d[key].toLocaleString('sv-SE', { maximumFractionDigits: 1 })
        : d[key];
      html += `${info.label}: ${val}<br>`;
    }
  });

  return html;
}

function buildAriaLabel(d) {
  const dims = metadata.dimensions || {};
  const parts = [`${d.area}, ${d.year}`];
  Object.entries(dims).forEach(([key, info]) => {
    if (d[key] !== null && d[key] !== undefined) {
      parts.push(`${info.label}: ${d[key]}`);
    }
  });
  return parts.join(', ');
}

function showDetailPanel(d) {
  const panel = document.getElementById('detail-panel');
  const dims = metadata.dimensions || {};
  let html = `<h3>${d.area} (${d.year})</h3>`;

  Object.entries(dims).forEach(([key, info]) => {
    if (d[key] !== null && d[key] !== undefined) {
      const val = typeof d[key] === 'number'
        ? d[key].toLocaleString('sv-SE', { maximumFractionDigits: 1 })
        : d[key];
      html += `<p><strong>${info.label}:</strong> ${val} ${info.unit}</p>`;
    }
  });

  panel.innerHTML = html;
  panel.classList.add('visible');
}

function updateSummary(data) {
  const sorted = [...data].sort((a, b) => (b[yDim] || 0) - (a[yDim] || 0));
  const parts = sorted.map(d => `${d.area}: ${d[yDim]?.toLocaleString('sv-SE') || '–'}`);
  document.getElementById('chart-summary').textContent =
    `Bubbeldiagram ${currentYear}. ${parts.join(', ')}.`;
}

// ── Starta ───────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', loadData);
