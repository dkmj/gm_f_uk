/**
 * bubble-chart.js — D3.js v7 bubbeldiagram för Klimatbudget Uppsala
 * Visar CO₂-utsläpp per sektor med interaktiv tidsslider och legendfilter.
 */

const SECTOR_COLORS = {
  'Transport':           '#2B7CE9',
  'Energi':              '#F5A623',
  'Bygg och anläggning': '#8B6D5C',
  'Jord- och skogsbruk': '#2D8A4E',
  'Konsumtion':          '#9B59B6',
  'Övriga områden':      '#95A5A6',
};

const MARGIN = { top: 40, right: 40, bottom: 60, left: 70 };

// Globalt tillstånd
let allData = [];
let hiddenAreas = new Set();
let currentYear = 2024;

// ── Datainläsning ────────────────────────────────────────────────────────────

async function loadData() {
  try {
    const response = await fetch('data/nvv_kommun_co2.json');
    if (!response.ok) {
      throw new Error(`HTTP-fel vid hämtning av data: ${response.status} ${response.statusText}`);
    }
    const json = await response.json();
    if (!json.sectors || !Array.isArray(json.sectors)) {
      throw new Error('Ogiltigt dataformat: fältet "sectors" saknas eller är inte en lista.');
    }
    allData = json.sectors;
    initChart();
  } catch (err) {
    showError(`Kunde inte ladda klimatdata. ${err.message}`);
  }
}

// ── Felvisning ───────────────────────────────────────────────────────────────

function showError(message) {
  const container = document.getElementById('error-container');
  container.textContent = message;
  container.classList.add('visible');
}

// ── Initiering ───────────────────────────────────────────────────────────────

function initChart() {
  // Hämta alla unika år från data
  const years = [...new Set(allData.map(d => d.year))].sort((a, b) => a - b);
  const minYear = years[0];
  const maxYear = years[years.length - 1];
  currentYear = maxYear;

  const slider = document.getElementById('year-slider');
  const yearDisplay = document.getElementById('year-display');

  slider.min = minYear;
  slider.max = maxYear;
  slider.value = maxYear;
  yearDisplay.textContent = maxYear;

  slider.addEventListener('input', () => {
    currentYear = +slider.value;
    yearDisplay.textContent = currentYear;
    updateChart();
  });

  buildLegend();
  updateChart();

  window.addEventListener('resize', updateChart);
}

// ── Legend ───────────────────────────────────────────────────────────────────

function buildLegend() {
  const legendEl = document.getElementById('legend');
  legendEl.innerHTML = '';

  const areas = Object.keys(SECTOR_COLORS);

  areas.forEach(area => {
    const btn = document.createElement('button');
    btn.className = 'legend-item';
    btn.setAttribute('role', 'checkbox');
    btn.setAttribute('aria-checked', 'true');
    btn.setAttribute('data-area', area);

    const dot = document.createElement('span');
    dot.className = 'legend-dot';
    dot.style.background = SECTOR_COLORS[area];

    const label = document.createTextNode(area);

    btn.appendChild(dot);
    btn.appendChild(label);

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

    legendEl.appendChild(btn);
  });
}

// ── Diagramuppdatering ───────────────────────────────────────────────────────

function updateChart() {
  const svg = document.getElementById('bubble-chart');
  const containerWidth = svg.parentElement.clientWidth || 600;
  const height = Math.min(500, containerWidth * 0.6);
  const isMobile = window.innerWidth < 1024;

  const width = containerWidth;
  const innerWidth  = width  - MARGIN.left - MARGIN.right;
  const innerHeight = height - MARGIN.top  - MARGIN.bottom;

  // Filtrera på år och dolda sektorer
  const filtered = allData.filter(
    d => d.year === currentYear && !hiddenAreas.has(d.area)
  );

  // Aggregera per sektor (summera om flera rader per area+år)
  const aggregated = d3.rollups(
    filtered,
    rows => ({
      area:       rows[0].area,
      co2e_kton:  d3.sum(rows, r => r.co2e_kton),
      share_pct:  d3.sum(rows, r => r.share_pct),
    }),
    d => d.area
  ).map(([, v]) => v);

  // ── Skalor ─────────────────────────────────────────────────────────────────

  const areas = aggregated.map(d => d.area);

  const xScale = d3.scaleBand()
    .domain(areas)
    .range([0, innerWidth])
    .padding(0.3);

  const maxCo2 = d3.max(aggregated, d => d.co2e_kton) || 1;
  const yScale = d3.scaleLinear()
    .domain([0, maxCo2 * 1.1])
    .range([innerHeight, 0])
    .nice();

  const maxShare = d3.max(aggregated, d => d.share_pct) || 1;
  const radiusRange = isMobile ? [8, 30] : [8, 50];
  const rScale = d3.scaleSqrt()
    .domain([0, maxShare])
    .range(radiusRange);

  // ── Rensa SVG (behåll title) ────────────────────────────────────────────────

  const svgEl = d3.select('#bubble-chart');
  svgEl.selectAll('*:not(title)').remove();
  svgEl
    .attr('width',  width)
    .attr('height', height)
    .attr('viewBox', `0 0 ${width} ${height}`);

  const g = svgEl.append('g')
    .attr('transform', `translate(${MARGIN.left},${MARGIN.top})`);

  // ── X-axel ─────────────────────────────────────────────────────────────────

  const xAxisG = g.append('g')
    .attr('transform', `translate(0,${innerHeight})`)
    .call(d3.axisBottom(xScale).tickSize(0));

  xAxisG.select('.domain').attr('stroke', '#DDE0E3');

  xAxisG.selectAll('text')
    .attr('transform', 'rotate(-30)')
    .attr('text-anchor', 'end')
    .attr('dx', '-0.4em')
    .attr('dy', '0.6em')
    .style('font-size', isMobile ? '0.7rem' : '0.8rem')
    .style('fill', '#4C576A');

  // ── Y-axel ─────────────────────────────────────────────────────────────────

  const yAxisG = g.append('g')
    .call(
      d3.axisLeft(yScale)
        .ticks(5)
        .tickFormat(d => `${d} kton`)
    );

  yAxisG.select('.domain').attr('stroke', '#DDE0E3');
  yAxisG.selectAll('text').style('fill', '#4C576A').style('font-size', '0.8rem');
  yAxisG.selectAll('.tick line').attr('stroke', '#DDE0E3');

  // Y-axel etikett
  g.append('text')
    .attr('transform', 'rotate(-90)')
    .attr('x', -innerHeight / 2)
    .attr('y', -MARGIN.left + 16)
    .attr('text-anchor', 'middle')
    .style('font-size', '0.8rem')
    .style('fill', '#4C576A')
    .text('CO₂-ekvivalenter (kton)');

  // ── Bubblor ────────────────────────────────────────────────────────────────

  const tooltip   = document.getElementById('tooltip');
  const detailPanel = document.getElementById('detail-panel');

  function showDetail(d) {
    detailPanel.innerHTML = `
      <h3>${d.area}</h3>
      <p><strong>Utsläpp:</strong> ${d.co2e_kton.toLocaleString('sv-SE')} kton CO₂e</p>
      <p><strong>Andel av totalt:</strong> ${d.share_pct.toFixed(1)} %</p>
      <p><strong>År:</strong> ${currentYear}</p>
    `;
    detailPanel.classList.add('visible');
  }

  const circles = g.selectAll('circle.bubble')
    .data(aggregated, d => d.area)
    .join('circle')
    .attr('class', 'bubble')
    .attr('cx', d => xScale(d.area) + xScale.bandwidth() / 2)
    .attr('cy', d => yScale(d.co2e_kton))
    .attr('r',  d => rScale(d.share_pct))
    .attr('fill', d => SECTOR_COLORS[d.area] || '#95A5A6')
    .attr('fill-opacity', 0.75)
    .attr('stroke', d => SECTOR_COLORS[d.area] || '#95A5A6')
    .attr('stroke-width', 1.5)
    .attr('tabindex', 0)
    .attr('role', 'button')
    .attr('aria-label', d =>
      `${d.area}: ${d.co2e_kton.toLocaleString('sv-SE')} kton CO₂e, ${d.share_pct.toFixed(1)} % av totalt, år ${currentYear}`
    )
    .style('cursor', 'pointer');

  // Desktop: hover-tooltip
  circles
    .on('mouseenter', function(event, d) {
      if (window.innerWidth >= 1024) {
        tooltip.innerHTML = `
          <strong>${d.area}</strong><br>
          ${d.co2e_kton.toLocaleString('sv-SE')} kton CO₂e<br>
          ${d.share_pct.toFixed(1)} % av totalt
        `;
        tooltip.setAttribute('aria-hidden', 'false');
        tooltip.classList.add('visible');
      }
    })
    .on('mousemove', function(event) {
      if (window.innerWidth >= 1024) {
        const container = document.querySelector('.chart-container');
        const rect = container.getBoundingClientRect();
        let left = event.clientX - rect.left + 12;
        let top  = event.clientY - rect.top  - 10;
        // Håll tooltip inom containern
        if (left + 230 > container.clientWidth) left -= 240;
        tooltip.style.left = `${left}px`;
        tooltip.style.top  = `${top}px`;
      }
    })
    .on('mouseleave', function() {
      tooltip.classList.remove('visible');
      tooltip.setAttribute('aria-hidden', 'true');
    });

  // Mobil: klick visar detaljpanel
  circles.on('click', function(event, d) {
    if (window.innerWidth < 1024) {
      showDetail(d);
    }
  });

  // Tangentbord: Enter/Mellanslag triggar detaljpanel
  circles.on('keydown', function(event, d) {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      showDetail(d);
    }
  });

  // ── Tillgänglig sammanfattning ─────────────────────────────────────────────

  const totalCo2 = d3.sum(aggregated, d => d.co2e_kton);
  const summaryParts = aggregated
    .sort((a, b) => b.co2e_kton - a.co2e_kton)
    .map(d => `${d.area} ${d.co2e_kton.toLocaleString('sv-SE')} kton`)
    .join(', ');

  document.getElementById('chart-summary').textContent =
    `Bubbeldiagram för ${currentYear}. Totalt ${totalCo2.toLocaleString('sv-SE')} kton CO₂e. Sektorer (störst till minst): ${summaryParts}.`;
}

// ── Starta ───────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', loadData);
