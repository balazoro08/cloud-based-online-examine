/* Admin Portal Logic */

async function initAdminDashboard() {
  checkAuthGuard("admin");
  try {
    const stats = await apiFetch("/stats/admin");
    if (document.getElementById("stat-students")) document.getElementById("stat-students").textContent = stats.total_students;
    if (document.getElementById("stat-teachers")) document.getElementById("stat-teachers").textContent = stats.total_teachers;
    if (document.getElementById("stat-exams")) document.getElementById("stat-exams").textContent = stats.total_exams;
    if (document.getElementById("stat-subjects")) document.getElementById("stat-subjects").textContent = stats.total_subjects;
    if (document.getElementById("stat-attempts")) document.getElementById("stat-attempts").textContent = stats.completed_attempts;
    if (document.getElementById("stat-avg")) document.getElementById("stat-avg").textContent = `${stats.average_score}%`;
  } catch (err) {
    showToast("Failed to load admin statistics", "danger");
  }
}

async function loadUsersList(roleFilter = "") {
  checkAuthGuard("admin");
  const tableBody = document.getElementById("users-table-body");
  if (!tableBody) return;

  try {
    const endpoint = roleFilter ? `/users?role=${roleFilter}` : "/users";
    const users = await apiFetch(endpoint);
    
    if (users.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="6" class="text-center" style="text-align:center; padding: 24px;">No users found.</td></tr>`;
      return;
    }

    tableBody.innerHTML = users.map(user => {
      let dept = "-";
      if (user.role === "student" && user.student_profile) dept = user.student_profile.department || "-";
      if (user.role === "teacher" && user.teacher_profile) dept = user.teacher_profile.department || "-";

      const badgeClass = user.role === "admin" ? "badge-danger" : user.role === "teacher" ? "badge-info" : "badge-success";

      return `
        <tr>
          <td>#${user.id}</td>
          <td><strong>${user.name}</strong></td>
          <td>${user.email}</td>
          <td><span class="badge ${badgeClass}">${user.role.toUpperCase()}</span></td>
          <td>${dept}</td>
          <td>
            <button class="btn btn-sm btn-outline" onclick="deleteUserPrompt(${user.id}, '${user.name}')">Delete</button>
          </td>
        </tr>
      `;
    }).join("");
  } catch (err) {
    showToast("Error loading user directory", "danger");
  }
}

async function handleCreateUserModal(e) {
  e.preventDefault();
  const name = document.getElementById("modal-name").value.trim();
  const email = document.getElementById("modal-email").value.trim();
  const password = document.getElementById("modal-password").value;
  const role = document.getElementById("modal-role").value;
  const department = document.getElementById("modal-department")?.value || "";

  try {
    await apiFetch("/users", {
      method: "POST",
      body: JSON.stringify({ name, email, password, role, department })
    });
    showToast(`User ${name} created successfully!`, "success");
    closeModal("user-modal");
    loadUsersList();
  } catch (err) {
    showToast(err.message || "Failed to create user", "danger");
  }
}

async function deleteUserPrompt(userId, name) {
  if (confirm(`Are you sure you want to delete user "${name}"? This action cannot be undone.`)) {
    try {
      await apiFetch(`/users/${userId}`, { method: "DELETE" });
      showToast("User deleted successfully", "success");
      loadUsersList();
    } catch (err) {
      showToast(err.message || "Could not delete user", "danger");
    }
  }
}

async function loadSubjectsList() {
  checkAuthGuard("admin");
  const tbody = document.getElementById("subjects-table-body");
  if (!tbody) return;

  try {
    const subjects = await apiFetch("/subjects");
    if (subjects.length === 0) {
      tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; padding: 24px;">No subjects registered.</td></tr>`;
      return;
    }

    tbody.innerHTML = subjects.map(s => `
      <tr>
        <td>#${s.id}</td>
        <td><strong>${s.name}</strong></td>
        <td>${s.description || "No description"}</td>
        <td>
          <button class="btn btn-sm btn-danger" onclick="deleteSubjectPrompt(${s.id}, '${s.name}')">Delete</button>
        </td>
      </tr>
    `).join("");
  } catch (err) {
    showToast("Failed to load subjects", "danger");
  }
}

async function handleCreateSubject(e) {
  e.preventDefault();
  const name = document.getElementById("subj-name").value.trim();
  const description = document.getElementById("subj-desc").value.trim();

  try {
    await apiFetch("/subjects", {
      method: "POST",
      body: JSON.stringify({ name, description })
    });
    showToast("Subject added successfully!", "success");
    closeModal("subject-modal");
    loadSubjectsList();
  } catch (err) {
    showToast(err.message || "Failed to add subject", "danger");
  }
}

async function deleteSubjectPrompt(subjectId, name) {
  if (confirm(`Delete subject "${name}"?`)) {
    try {
      await apiFetch(`/subjects/${subjectId}`, { method: "DELETE" });
      showToast("Subject deleted", "success");
      loadSubjectsList();
    } catch (err) {
      showToast(err.message || "Could not delete subject", "danger");
    }
  }
}

// Modal helper utilities
function openModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.add("active");
}

function closeModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove("active");
}
