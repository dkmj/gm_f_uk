/* quiz.js — Gapminder-stil quiz för Klimatbudget Uppsala */

const state = {
  questions: [],
  currentIndex: 0,
  score: 0
};

async function loadQuiz() {
  const errorContainer = document.getElementById('error-container');
  const quizContent = document.getElementById('quiz-content');

  try {
    const response = await fetch('data/quiz.json');
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const data = await response.json();

    if (!data.questions || data.questions.length === 0) {
      throw new Error('Inga quizfrågor laddade...');
    }

    state.questions = data.questions;
    state.currentIndex = 0;
    state.score = 0;
    showQuestion();
  } catch (err) {
    errorContainer.textContent = err.message === 'Inga quizfrågor laddade...'
      ? err.message
      : 'Kunde inte ladda quizfrågor. Försök igen senare.';
    errorContainer.classList.add('visible');
    quizContent.innerHTML = '';
  }
}

function showQuestion() {
  const quizContent = document.getElementById('quiz-content');
  const q = state.questions[state.currentIndex];
  const total = state.questions.length;
  const progressPercent = (state.currentIndex / total) * 100;

  quizContent.innerHTML = `
    <p class="progress">Fråga ${state.currentIndex + 1} av ${total}</p>
    <div class="progress-bar" role="progressbar" aria-valuenow="${state.currentIndex}" aria-valuemin="0" aria-valuemax="${total}">
      <div class="progress-fill" style="width: ${progressPercent}%"></div>
    </div>

    <p class="question-text">${q.question}</p>

    <div class="options" id="options-list">
      ${q.options.map((opt, i) => `
        <button class="option-btn" data-index="${i}" onclick="handleAnswer(${i})">
          ${opt}
        </button>
      `).join('')}
    </div>

    <div class="feedback" id="feedback" role="status" aria-live="polite"></div>

    <button class="next-btn" id="next-btn" onclick="advanceQuiz()">
      ${state.currentIndex + 1 < total ? 'Nästa fråga →' : 'Se resultat →'}
    </button>
  `;
}

function handleAnswer(selectedIndex) {
  const q = state.questions[state.currentIndex];
  const buttons = document.querySelectorAll('.option-btn');
  const feedback = document.getElementById('feedback');
  const nextBtn = document.getElementById('next-btn');

  // Inaktivera alla knappar
  buttons.forEach(btn => {
    btn.disabled = true;
  });

  const isCorrect = selectedIndex === q.correct;

  if (isCorrect) {
    state.score += 1;
    buttons[selectedIndex].classList.add('correct');
    feedback.className = 'feedback visible correct';
    feedback.innerHTML = `
      <strong>Rätt!</strong> ${q.explanation}
      <p class="feedback-source">Källa: ${q.source}</p>
    `;
  } else {
    buttons[selectedIndex].classList.add('wrong');
    buttons[q.correct].classList.add('correct');
    feedback.className = 'feedback visible wrong';
    feedback.innerHTML = `
      <strong>Fel.</strong> Rätt svar: <strong>${q.options[q.correct]}</strong>. ${q.explanation}
      <p class="feedback-source">Källa: ${q.source}</p>
    `;
  }

  nextBtn.classList.add('visible');
}

function advanceQuiz() {
  state.currentIndex += 1;
  if (state.currentIndex < state.questions.length) {
    showQuestion();
  } else {
    showResults();
  }
}

function showResults() {
  const quizContent = document.getElementById('quiz-content');
  const total = state.questions.length;
  const randomChance = Math.round((total / 4) * 10) / 10;

  let betyg;
  if (state.score === total) {
    betyg = 'Utmärkt! Du kan din klimatdata.';
  } else if (state.score >= Math.ceil(total / 2)) {
    betyg = 'Bra jobbat! Du har god koll på Uppsalas klimatarbete.';
  } else if (state.score > randomChance) {
    betyg = 'Lite bättre än slumpen — fortsätt utforska klimatdatan!';
  } else {
    betyg = 'Det finns mer att lära — utforska bubbeldiagrammet för mer insikt.';
  }

  quizContent.innerHTML = `
    <div class="results">
      <h2>Ditt resultat</h2>
      <p class="score">${state.score} / ${total}</p>
      <p class="score-context">
        ${betyg}<br>
        (Slumpmässig gissning ger i snitt ${randomChance.toFixed(1)} rätt av ${total}.)
      </p>
      <div class="results-links">
        <a href="bubble.html" class="bubble-link">Utforska utsläppen i bubbeldiagrammet →</a>
        <button class="restart-btn" onclick="restartQuiz()">Gör quizet igen</button>
      </div>
    </div>
  `;
}

function restartQuiz() {
  state.currentIndex = 0;
  state.score = 0;
  showQuestion();
}

// Starta quizet
loadQuiz();
