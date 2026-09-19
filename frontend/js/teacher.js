/* Teacher Portal Logic */

async function initTeacherDashboard() {
  checkAuthGuard("teacher");
  try {
    const stats = await apiFetch("/stats/teacher");
    if (document.getElementById("tstat-exams")) document.getElementById("tstat-exams").textContent = stats.total_exams;
    if (document.getElementById("tstat-active")) document.getElementById("tstat-active").textContent = stats.active_exams;
    if (document.getElementById("tstat-submissions")) document.getElementById("tstat-submissions").textContent = stats.total_submissions;
    if (document.getElementById("tstat-avg")) document.getElementById("tstat-avg").textContent = `${stats.average_score}%`;
    if (document.getElementById("tstat-passrate")) document.getElementById("tstat-passrate").textContent = `${stats.pass_rate}%`;

    loadTeacherExamsList();
  } catch (err) {
    showToast("Failed to load teacher analytics", "danger");
  }
}

async function loadTeacherExamsList() {
  checkAuthGuard("teacher");
  const tbody = document.getElementById("teacher-exams-body");
  if (!tbody) return;

  try {
    const exams = await apiFetch("/exams");
    if (exams.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:24px;">No examinations created yet. Click "Create New Exam" to begin.</td></tr>`;
      return;
    }

    tbody.innerHTML = exams.map(e => {
      const isPublished = e.status === "published";
      const statusBadge = isPublished ? `<span class="badge badge-success">PUBLISHED</span>` : `<span class="badge badge-warning">DRAFT</span>`;
      
      return `
        <tr>
          <td>#${e.id}</td>
          <td><strong>${e.title}</strong></td>
          <td>${e.subject_name || "General"}</td>
          <td>${e.duration_minutes} mins</td>
          <td>${e.question_count} Qs (${e.total_marks} marks)</td>
          <td>${statusBadge}</td>
          <td style="display:flex; gap:8px;">
            <a href="/static/teacher/questions.html?exam_id=${e.id}" class="btn btn-sm btn-secondary">Manage Qs</a>
            ${isPublished 
              ? `<button class="btn btn-sm btn-outline" onclick="togglePublishExam(${e.id}, false)">Unpublish</button>`
              : `<button class="btn btn-sm btn-success" onclick="togglePublishExam(${e.id}, true)">Publish</button>`
            }
            <a href="/static/teacher/results.html?exam_id=${e.id}" class="btn btn-sm btn-primary">Results</a>
            <button class="btn btn-sm btn-danger" onclick="deleteExamPrompt(${e.id}, '${e.title}')">Delete</button>
          </td>
        </tr>
      `;
    }).join("");
  } catch (err) {
    showToast("Error loading examinations", "danger");
  }
}

async function handleCreateExamForm(e) {
  e.preventDefault();
  const title = document.getElementById("exam-title").value.trim();
  const description = document.getElementById("exam-desc").value.trim();
  const subject_id = parseInt(document.getElementById("exam-subject").value);
  const duration_minutes = parseInt(document.getElementById("exam-duration").value);
  const total_marks = parseFloat(document.getElementById("exam-marks").value);
  const passing_percentage = parseFloat(document.getElementById("exam-pass").value);

  try {
    const newExam = await apiFetch("/exams", {
      method: "POST",
      body: JSON.stringify({
        title, description, subject_id, duration_minutes, total_marks, passing_percentage
      })
    });
    showToast("Exam created successfully! Now add questions.", "success");
    setTimeout(() => {
      window.location.href = `/static/teacher/questions.html?exam_id=${newExam.id}`;
    }, 600);
  } catch (err) {
    showToast(err.message || "Failed to create exam", "danger");
  }
}

async function togglePublishExam(examId, publish) {
  const endpoint = `/exams/${examId}/${publish ? "publish" : "unpublish"}`;
  try {
    await apiFetch(endpoint, { method: "POST" });
    showToast(`Exam ${publish ? "published" : "unpublished"} successfully!`, "success");
    loadTeacherExamsList();
  } catch (err) {
    showToast(err.message || "Action failed", "danger");
  }
}

async function deleteExamPrompt(examId, title) {
  if (confirm(`Delete exam "${title}"? All associated questions and student submissions will be deleted.`)) {
    try {
      await apiFetch(`/exams/${examId}`, { method: "DELETE" });
      showToast("Exam deleted", "success");
      loadTeacherExamsList();
    } catch (err) {
      showToast(err.message || "Failed to delete exam", "danger");
    }
  }
}

// Question Builder Logic
async function initQuestionBuilder() {
  checkAuthGuard("teacher");
  const urlParams = new URLSearchParams(window.location.search);
  const examId = urlParams.get("exam_id");

  if (!examId) {
    showToast("No exam ID provided", "warning");
    window.location.href = "/static/teacher/exams.html";
    return;
  }

  try {
    const exam = await apiFetch(`/exams/${examId}`);
    document.getElementById("builder-exam-title").textContent = exam.title;

    loadExamQuestions(examId);
  } catch (err) {
    showToast("Error loading exam details", "danger");
  }
}

async function loadExamQuestions(examId) {
  const container = document.getElementById("questions-container");
  if (!container) return;

  try {
    const questions = await apiFetch(`/exams/${examId}/questions`);
    
    if (questions.length === 0) {
      container.innerHTML = `<div class="card" style="text-align:center; padding:32px;">No questions added yet. Use the form below to add your first question!</div>`;
      return;
    }

    container.innerHTML = questions.map((q, idx) => `
      <div class="card" style="margin-bottom: 20px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
          <h4>Q${idx + 1}. ${q.question_text}</h4>
          <div>
            <span class="badge badge-info">${q.marks} Marks</span>
            <button class="btn btn-sm btn-danger" onclick="deleteQuestion(${q.id}, ${examId})">Delete</button>
          </div>
        </div>
        <div style="display:grid; grid-template-columns: repeat(2, 1fr); gap:10px;">
          ${q.options.map(opt => `
            <div style="padding:10px 14px; border-radius:8px; border:1px solid ${opt.is_correct ? 'var(--success)' : 'var(--border-color)'}; background:${opt.is_correct ? 'var(--success-bg)' : '#FFFFFF'}; display:flex; align-items:center; gap:8px;">
              <span>${opt.is_correct ? '✔' : '⚪'}</span>
              <span>${opt.option_text}</span>
            </div>
          `).join("")}
        </div>
      </div>
    `).join("");
  } catch (err) {
    showToast("Failed to load questions", "danger");
  }
}

async function handleAddQuestionSubmit(e) {
  e.preventDefault();
  const urlParams = new URLSearchParams(window.location.search);
  const examId = urlParams.get("exam_id");

  const question_text = document.getElementById("q-text").value.trim();
  const marks = parseFloat(document.getElementById("q-marks").value);
  const optA = document.getElementById("opt-a").value.trim();
  const optB = document.getElementById("opt-b").value.trim();
  const optC = document.getElementById("opt-c").value.trim();
  const optD = document.getElementById("opt-d").value.trim();
  const correctChoice = document.querySelector("input[name='correct_option']:checked")?.value;

  if (!correctChoice) {
    showToast("Please select which option is correct", "warning");
    return;
  }

  const options = [
    { option_text: optA, is_correct: correctChoice === "A" },
    { option_text: optB, is_correct: correctChoice === "B" },
    { option_text: optC, is_correct: correctChoice === "C" },
    { option_text: optD, is_correct: correctChoice === "D" }
  ];

  try {
    await apiFetch(`/exams/${examId}/questions`, {
      method: "POST",
      body: JSON.stringify({ question_text, marks, options })
    });
    showToast("Question added!", "success");
    e.target.reset();
    loadExamQuestions(examId);
  } catch (err) {
    showToast(err.message || "Failed to add question", "danger");
  }
}

async function deleteQuestion(questionId, examId) {
  if (confirm("Delete this question?")) {
    try {
      await apiFetch(`/questions/${questionId}`, { method: "DELETE" });
      showToast("Question deleted", "success");
      loadExamQuestions(examId);
    } catch (err) {
      showToast(err.message || "Error deleting question", "danger");
    }
  }
}
