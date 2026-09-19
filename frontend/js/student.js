/* Student Portal Logic */

async function initStudentDashboard() {
  checkAuthGuard("student");
  loadAvailableExams();
  loadStudentHistory(3); // load top 3 recent history
}

async function loadAvailableExams() {
  const container = document.getElementById("available-exams-container");
  if (!container) return;

  try {
    const exams = await apiFetch("/exams");
    
    if (exams.length === 0) {
      container.innerHTML = `<div class="card" style="grid-column: 1/-1; text-align:center; padding:32px;">No active examinations currently available. Please check back later!</div>`;
      return;
    }

    container.innerHTML = exams.map(e => `
      <div class="card card-hover" style="display:flex; flex-direction:column; justify-between:space-between; gap:16px;">
        <div>
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <span class="badge badge-info">${e.subject_name || "General"}</span>
            <span class="badge badge-secondary">${e.duration_minutes} Mins</span>
          </div>
          <h3 style="font-size:18px; margin-bottom:8px;">${e.title}</h3>
          <p style="color:var(--text-muted); font-size:14px;">${e.description || "No description provided."}</p>
        </div>
        <div style="border-top: 1px solid var(--border-color); padding-top:14px; display:flex; justify-content:space-between; align-items:center;">
          <span style="font-size:13px; color:var(--text-muted); font-weight:600;">${e.question_count} Questions • ${e.total_marks} Marks</span>
          <button class="btn btn-primary btn-sm" onclick="startExamAttempt(${e.id})">Start Exam</button>
        </div>
      </div>
    `).join("");
  } catch (err) {
    showToast("Failed to load available exams", "danger");
  }
}

async function startExamAttempt(examId) {
  try {
    showToast("Initializing examination environment...", "info");
    const data = await apiFetch(`/exams/${examId}/start`, { method: "POST" });
    window.location.href = `/static/student/exam.html?attempt_id=${data.attempt_id}`;
  } catch (err) {
    showToast(err.message || "Failed to start exam", "danger");
  }
}

async function loadStudentHistory(limit = null) {
  const tbody = document.getElementById("student-history-body");
  if (!tbody) return;

  try {
    let results = await apiFetch("/results");
    if (limit) results = results.slice(0, limit);

    if (results.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:24px;">No exam history recorded yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = results.map(r => {
      const dateStr = r.submitted_at ? new Date(r.submitted_at).toLocaleDateString() : "N/A";
      const statusBadge = r.is_passed ? `<span class="badge badge-success">PASSED</span>` : `<span class="badge badge-danger">FAILED</span>`;

      return `
        <tr>
          <td><strong>${r.exam_title}</strong></td>
          <td>${r.subject_name || "General"}</td>
          <td>${dateStr}</td>
          <td><strong>${r.score} / ${r.total_marks}</strong> (${r.percentage}%)</td>
          <td>${statusBadge}</td>
          <td>
            <a href="/static/student/result.html?attempt_id=${r.attempt_id}" class="btn btn-sm btn-outline">View Report</a>
          </td>
        </tr>
      `;
    }).join("");
  } catch (err) {
    showToast("Error loading exam history", "danger");
  }
}

async function loadResultReport() {
  checkAuthGuard("student");
  const urlParams = new URLSearchParams(window.location.search);
  const attemptId = urlParams.get("attempt_id");

  if (!attemptId) {
    window.location.href = "/static/student/history.html";
    return;
  }

  try {
    const r = await apiFetch(`/results/${attemptId}`);

    document.getElementById("res-title").textContent = r.exam_title;
    document.getElementById("res-subject").textContent = r.subject_name || "General";
    document.getElementById("res-score").textContent = `${r.score} / ${r.total_marks}`;
    document.getElementById("res-percentage").textContent = `${r.percentage}%`;
    
    const badgeEl = document.getElementById("res-status-badge");
    if (r.is_passed) {
      badgeEl.className = "badge badge-success";
      badgeEl.textContent = "PASSED";
    } else {
      badgeEl.className = "badge badge-danger";
      badgeEl.textContent = "FAILED";
    }

    document.getElementById("res-correct").textContent = r.correct_count;
    document.getElementById("res-incorrect").textContent = r.incorrect_count;
    document.getElementById("res-unanswered").textContent = r.unanswered_count;
    document.getElementById("res-total-q").textContent = r.total_questions;

    // Render detailed question breakdown
    const container = document.getElementById("answers-breakdown-container");
    if (container && r.answers) {
      container.innerHTML = r.answers.map((ans, idx) => `
        <div class="card" style="margin-bottom: 16px; border-left: 5px solid ${ans.is_correct ? 'var(--success)' : 'var(--danger)'};">
          <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
            <h4>Q${idx + 1}. ${ans.question_text}</h4>
            <span class="badge ${ans.is_correct ? 'badge-success' : 'badge-danger'}">${ans.marks_obtained} / ${ans.total_marks} Marks</span>
          </div>
          <div style="font-size:14px; margin-top:8px;">
            <p><strong>Your Answer:</strong> <span style="color:${ans.is_correct ? 'var(--success)' : 'var(--danger)'}">${ans.selected_option_text || 'No Answer'}</span></p>
            ${!ans.is_correct ? `<p style="margin-top:4px;"><strong>Correct Answer:</strong> <span style="color:var(--success)">${ans.correct_option_text}</span></p>` : ''}
          </div>
        </div>
      `).join("");
    }

  } catch (err) {
    showToast("Error loading result report", "danger");
  }
}
