/**
 * Admin-vy: hanterar datakällor och förhandsgranskning av datafiler.
 */

function showError(message) {
  const container = document.getElementById('error-container');
  container.textContent = message;
  container.style.display = 'block';
}

function formatDate(dateStr) {
  if (!dateStr) return '–';
  const d = new Date(dateStr);
  if (isNaN(d)) return dateStr;
  return d.toLocaleDateString('sv-SE');
}

async function previewData(dataFile, btn) {
  const card = btn.closest('.source-card');
  let preview = card.querySelector('.data-preview');

  if (preview.style.display === 'block') {
    preview.style.display = 'none';
    btn.textContent = 'Förhandsgranska data';
    return;
  }

  btn.textContent = 'Laddar…';
  try {
    const res = await fetch(dataFile);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const text = await res.text();
    preview.textContent = text.slice(0, 2000);
    preview.style.display = 'block';
    btn.textContent = 'Dölj förhandsgranskning';
  } catch (err) {
    preview.textContent = `Kunde inte läsa filen: ${err.message}`;
    preview.style.display = 'block';
    btn.textContent = 'Förhandsgranska data';
  }
}

function renderSources(sources) {
  const list = document.getElementById('sources-list');

  if (!sources || sources.length === 0) {
    list.innerHTML = '<p>Inga datakällor hittades.</p>';
    return;
  }

  list.innerHTML = sources.map(src => `
    <div class="source-card">
      <h3>${src.source_name}</h3>
      <dl class="source-meta">
        <div>
          <dt>Källa</dt>
          <dd><a href="${src.url}" target="_blank" rel="noopener noreferrer">${src.url}</a></dd>
        </div>
        <div>
          <dt>Senast hämtad</dt>
          <dd>${formatDate(src.last_fetched)}</dd>
        </div>
        <div>
          <dt>Antal rader</dt>
          <dd>${src.row_count !== undefined ? src.row_count : '–'}</dd>
        </div>
        <div>
          <dt>Format</dt>
          <dd>${src.format || '–'}</dd>
        </div>
        <div>
          <dt>Licens</dt>
          <dd>${src.license || '–'}</dd>
        </div>
        <div>
          <dt>Skript</dt>
          <dd><code>${src.fetch_script || '–'}</code></dd>
        </div>
      </dl>
      <button class="btn-preview" onclick="previewData('${src.data_file}', this)">
        Förhandsgranska data
      </button>
      <div class="data-preview"></div>
    </div>
  `).join('');
}

async function loadSources() {
  try {
    const res = await fetch('data/sources.json');
    if (!res.ok) throw new Error(`HTTP ${res.status} — kunde inte hämta sources.json`);
    const sources = await res.json();
    renderSources(sources);
  } catch (err) {
    showError(`Fel vid inläsning av datakällor: ${err.message}`);
  }
}

document.addEventListener('DOMContentLoaded', loadSources);
