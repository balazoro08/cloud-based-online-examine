/* Distraction-Free Exam Engine */

let currentAttempt = null;
let currentQuestionIndex = 0;
let userAnswers = {}; // { question_id: selected_option_id }
let timerInterval = null;
let secondsRemaining = 0;

async function initExamEngine() {
  checkAuthGuard("student");
  const urlParams = new URLSearchParams(window.location.search);
  const attemptId = urlParams.get("attempt_id");

  if (!attemptId) {
    showToast("Invalid exam session", "danger");
    window.location.href = "/static/student/dashboard.html";
    return;
  }

  try {
    const data = await apiFetch(`/attempts/${attemptId}`);
    currentAttempt = data;
    userAnswers = data.saved_answers || {};

    // Check if attempt is already submitted
    if (data.status === "submitted") {
      window.location.href = `/static/student/result.html?attempt_id=${attemptId}`;
      return;
    }

    document.getElementById("exam-header-title").textContent = data.exam_title;
    document.getElementById("total-q-badge").textContent = `${data.questions.length} Questions`;

    // Use server-calculated remaining seconds
    secondsRemaining = data.remaining_seconds !== undefined ? data.remaining_seconds : (data.duration_minutes * 60);

    startTimer();
    renderQuestion(0);
    renderQuestionPalette();

  } catch (err) {
    showToast(err.message || "Failed to load examination environment", "danger");
  }
}

function startTimer() {
  const timerElem = document.getElementById("timer-display");

  function updateDisplay() {
    if (secondsRemaining <= 0) {
      clearInterval(timerInterval);
      if (timerElem) timerElem.textContent = "00:00:00";
      showToast("Time expired! Submitting your exam automatically...", "warning");
      submitExam(true);
      return;
    }

    const hrs = Math.floor(secondsRemaining / 3600);
    const mins = Math.floor((secondsRemaining % 3600) / 60);
    const secs = secondsRemaining % 60;

    const formatted = `${hrs > 0 ? String(hrs).padStart(2, '0') + ':' : ''}${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    if (timerElem) timerElem.textContent = formatted;

    secondsRemaining--;
  }

  updateDisplay();
  timerInterval = setInterval(updateDisplay, 1000);
}

function renderQuestion(index) {
  if (!currentAttempt || !currentAttempt.questions[index]) return;
  currentQuestionIndex = index;
  const q = currentAttempt.questions[index];

  document.getElementById("q-number-label").textContent = `Question ${index + 1} of ${currentAttempt.questions.length}`;
  document.getElementById("q-marks-label").textContent = `[${q.marks} Marks]`;
  document.getElementById("q-text-display").textContent = q.question_text;

  const optionsContainer = document.getElementById("options-display");
  const selectedOptId = userAnswers[q.id];

  optionsContainer.innerHTML = q.options.map(opt => {
    const isSelected = selectedOptId === opt.id;
    return `
      <div class="option-card ${isSelected ? 'selected' : ''}" onclick="selectOption(${q.id}, ${opt.id})">
        <input type="radio" class="option-radio" name="option_choice" value="${opt.id}" ${isSelected ? 'checked' : ''}>
        <span>${opt.option_text}</span>
      </div>
    `;
  }).join("");

  // Update Next/Prev buttons
  const prevBtn = document.getElementById("btn-prev");
  const nextBtn = document.getElementById("btn-next");
  if (prevBtn) prevBtn.disabled = index === 0;
  if (nextBtn) nextBtn.textContent = index === currentAttempt.questions.length - 1 ? "Review & Submit" : "Next Question →";

  renderQuestionPalette();
}

async function selectOption(questionId, optionId) {
  userAnswers[questionId] = optionId;
  renderQuestion(currentQuestionIndex);

  // Trigger API Autosave
  const statusElem = document.getElementById("autosave-indicator");
  if (statusElem) statusElem.textContent = "Saving...";

  try {
    await apiFetch(`/attempts/${currentAttempt.attempt_id}/answers`, {
      method: "POST",
      body: JSON.stringify({ question_id: questionId, selected_option_id: optionId })
    });
    if (statusElem) statusElem.textContent = "Saved";
  } catch (err) {
    if (statusElem) statusElem.textContent = "Autosave error";
  }
}

function navigateQuestion(direction) {
  const newIndex = currentQuestionIndex + direction;
  if (newIndex >= 0 && newIndex < currentAttempt.questions.length) {
    renderQuestion(newIndex);
  } else if (newIndex === currentAttempt.questions.length) {
    openSubmitModal();
  }
}

function renderQuestionPalette() {
  const palette = document.getElementById("palette-container");
  if (!palette || !currentAttempt) return;

  palette.innerHTML = currentAttempt.questions.map((q, idx) => {
    const isAnswered = userAnswers[q.id] !== undefined && userAnswers[q.id] !== null;
    const isCurrent = idx === currentQuestionIndex;

    let btnClass = "palette-btn";
    if (isAnswered) btnClass += " answered";
    if (isCurrent) btnClass += " current";

    return `<button class="${btnClass}" onclick="renderQuestion(${idx})">${idx + 1}</button>`;
  }).join("");
}

function openSubmitModal() {
  const total = currentAttempt.questions.length;
  const answered = Object.keys(userAnswers).length;
  const unanswered = total - answered;

  document.getElementById("modal-total-q").textContent = total;
  document.getElementById("modal-ans-q").textContent = answered;
  document.getElementById("modal-unans-q").textContent = unanswered;

  openModal("submit-exam-modal");
}

async function submitExam(isAuto = false) {
  if (timerInterval) clearInterval(timerInterval);

  try {
    showToast("Submitting answers & evaluating score...", "info");
    const data = await apiFetch(`/attempts/${currentAttempt.attempt_id}/submit`, { method: "POST" });
    showToast("Exam submitted successfully!", "success");
    setTimeout(() => {
      window.location.href = `/static/student/result.html?attempt_id=${currentAttempt.attempt_id}`;
    }, 600);
  } catch (err) {
    showToast(err.message || "Error submitting exam", "danger");
  }
}
