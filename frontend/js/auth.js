/* Auth logic and route protection */

function redirectByRole(role) {
  if (role === "admin") {
    window.location.href = "/static/admin/dashboard.html";
  } else if (role === "teacher") {
    window.location.href = "/static/teacher/dashboard.html";
  } else {
    window.location.href = "/static/student/dashboard.html";
  }
}

async function handleLogin(e) {
  e.preventDefault();
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;
  const submitBtn = e.target.querySelector("button[type='submit']");

  if (!email || !password) {
    showToast("Please enter both email and password", "warning");
    return;
  }

  try {
    if (submitBtn) submitBtn.disabled = true;
    showToast("Signing in...", "info");

    const data = await apiFetch("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password })
    });

    setAuthToken(data.access_token);
    setUserProfile({
      id: data.user_id,
      name: data.name,
      email: data.email,
      role: data.role
    });

    showToast(`Welcome back, ${data.name}!`, "success");
    setTimeout(() => redirectByRole(data.role), 500);

  } catch (err) {
    showToast(err.message || "Failed to log in", "danger");
    if (submitBtn) submitBtn.disabled = false;
  }
}

async function handleRegister(e) {
  e.preventDefault();
  const name = document.getElementById("name").value.trim();
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;
  const roll_number = document.getElementById("roll_number")?.value.trim() || "";
  const department = document.getElementById("department")?.value || "";
  const year = document.getElementById("year")?.value || "";
  const submitBtn = e.target.querySelector("button[type='submit']");

  if (!name || !email || !password) {
    showToast("Please fill out all required fields", "warning");
    return;
  }

  try {
    if (submitBtn) submitBtn.disabled = true;
    showToast("Creating account...", "info");

    const data = await apiFetch("/auth/register", {
      method: "POST",
      body: JSON.stringify({
        name, email, password, roll_number, department, year, section: "A"
      })
    });

    setAuthToken(data.access_token);
    setUserProfile({
      id: data.user_id,
      name: data.name,
      email: data.email,
      role: data.role
    });

    showToast("Registration successful! Redirecting...", "success");
    setTimeout(() => redirectByRole(data.role), 500);

  } catch (err) {
    showToast(err.message || "Registration failed", "danger");
    if (submitBtn) submitBtn.disabled = false;
  }
}

function handleLogout() {
  clearAuth();
  showToast("Logged out successfully", "info");
  setTimeout(() => {
    window.location.href = "/static/login.html";
  }, 400);
}

function checkAuthGuard(requiredRole = null) {
  const token = getAuthToken();
  const user = getUserProfile();

  if (!token || !user) {
    window.location.href = "/static/login.html";
    return;
  }

  if (requiredRole && user.role !== requiredRole && user.role !== "admin") {
    showToast("Unauthorized access to role restricted portal", "danger");
    setTimeout(() => redirectByRole(user.role), 600);
    return;
  }

  // Populate header user info if elements exist
  const userNameElem = document.getElementById("header-user-name");
  const userRoleElem = document.getElementById("header-user-role");
  const userAvatarElem = document.getElementById("header-user-avatar");

  if (userNameElem) userNameElem.textContent = user.name;
  if (userRoleElem) userRoleElem.textContent = user.role.toUpperCase();
  if (userAvatarElem) userAvatarElem.textContent = user.name.charAt(0).toUpperCase();
}
