/**
 * Civic Report Application
 * Main JavaScript application file with enhanced error handling and validation
 */

// Constants
const CONFIG = {
  API_TIMEOUT: 180000,
  TOAST_DURATION: 4000,
  PAGE_SIZE: 20,
  MAX_RETRIES: 3,
  RETRY_DELAY: 1000,
};

const safeJsonParse = (value, fallback = null) => {
  try {
    return JSON.parse(value);
  } catch (error) {
    console.warn("Failed to parse stored JSON", error);
    return fallback;
  }
};

// Global API state
const API = {
  token: localStorage.getItem("access") || "",
  user: safeJsonParse(localStorage.getItem("user") || "null"),
  isLoading: false,
  cache: {},
  refreshPromise: null,
};

const clearSession = () => {
  localStorage.removeItem("access");
  localStorage.removeItem("refresh");
  localStorage.removeItem("user");
  API.token = "";
  API.user = null;
};

const refreshAccessToken = async () => {
  const refresh = localStorage.getItem("refresh");
  if (!refresh) {
    throw new Error("Session expired. Please sign in again.");
  }

  if (!API.refreshPromise) {
    API.refreshPromise = fetch("/api/auth/refresh", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh }),
    })
      .then(async (response) => {
        const data = await response.json().catch(() => ({}));
        if (!response.ok || !data.access) {
          throw new Error(data.detail || "Session expired. Please sign in again.");
        }

        localStorage.setItem("access", data.access);
        API.token = data.access;
        return data.access;
      })
      .finally(() => {
        API.refreshPromise = null;
      });
  }

  return API.refreshPromise;
};

/**
 * Enhanced API request handler with retry logic and error handling
 */
API.req = async (url, options = {}, retryCount = 0, hasRetriedAuth = false) => {
  // Re-read token from localStorage before each request (handles multi-tab updates)
  const currentToken = localStorage.getItem("access") || "";
  if (currentToken) {
    API.token = currentToken;
  }

  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  if (API.token) {
    headers.Authorization = `Bearer ${API.token}`;
  }

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), CONFIG.API_TIMEOUT);

    const response = await fetch(url, {
      ...options,
      headers,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    let data = {};
    const contentType = response.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
      try {
        data = await response.json();
      } catch (e) {
        console.error("Failed to parse JSON response", e);
      }
    }

    if (!response.ok) {
      const errorMsg = data.detail || data.message || data.error || "Request failed";
      // Retry on 401 or 403 auth errors (DRF may return either for expired/invalid tokens)
      const isAuthError = response.status === 401 || 
        (response.status === 403 && errorMsg.toLowerCase().includes("authentication credentials were not provided"));
      
      if (isAuthError && API.token && !hasRetriedAuth) {
        try {
          await refreshAccessToken();
          return API.req(url, options, retryCount, true);
        } catch (refreshError) {
          clearSession();
          throw refreshError;
        }
      }
      throw new Error(errorMsg);
    }

    return data;
  } catch (error) {
    // Retry on timeout or network errors
    if (error.name === "AbortError" && retryCount < CONFIG.MAX_RETRIES) {
      await new Promise(r => setTimeout(r, CONFIG.RETRY_DELAY));
      return API.req(url, options, retryCount + 1);
    }

    if (error.name === "AbortError") {
      throw new Error("Request timeout - please try again");
    }

    if (!navigator.onLine) {
      throw new Error("No internet connection");
    }

    throw error;
  }
};

/**
 * Display toast notifications with auto-dismiss
 */
const toast = (message, type = "ok", duration = CONFIG.TOAST_DURATION) => {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const element = document.createElement("div");
  const baseClass = "glass-card px-4 py-3 rounded-lg font-medium text-sm shadow-lg";
  const typeClass = type === "err" 
    ? "border border-red-500/50 bg-red-500/10 text-red-300"
    : "border border-emerald-500/50 bg-emerald-500/10 text-emerald-300";

  element.className = `${baseClass} ${typeClass} animate-slideIn`;
  element.textContent = message;
  element.setAttribute("role", "alert");
  element.setAttribute("aria-live", "polite");

  container.appendChild(element);

  const timeoutId = setTimeout(() => {
    element.style.animation = "fadeOut 300ms ease-out forwards";
    setTimeout(() => element.remove(), 300);
  }, duration);

  element.addEventListener("click", () => {
    clearTimeout(timeoutId);
    element.remove();
  });

  return element;
};

/**
 * Toggle global loading state
 */
const setLoading = (state) => {
  const loader = document.getElementById("global-loader");
  if (!loader) return;

  API.isLoading = state;
  loader.classList.toggle("hidden", !state);
  loader.classList.toggle("flex", state);

  if (state) {
    loader.style.animation = "fadeIn 200ms ease-out";
  }
};

/**
 * Redirect user by role
 */
const redirectByRole = (role) => {
  const paths = {
    admin: "/admin-dashboard/",
    officer: "/officer/",
    citizen: "/citizen/",
  };

  const targetPath = paths[role] || "/citizen/";
  setTimeout(() => {
    window.location.href = targetPath;
  }, 500);
};

/**
 * User logout with cleanup
 */
const logout = () => {
  clearSession();
  toast("Logged out successfully");
  setTimeout(() => {
    window.location.href = "/";
  }, 800);
};

// Validation functions
const validateEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

const validatePassword = (password) => {
  return password && password.length >= 8;
};

const validateName = (name) => {
  return name && name.trim().length >= 2;
};

const validateTitle = (title) => {
  return title && title.trim().length >= 5;
};

const validateDescription = (description) => {
  return description && description.trim().length >= 20;
};

/**
 * Parse form data into object
 */
const parseFormData = (form) => {
  const formData = new FormData(form);
  const data = {};
  formData.forEach((value, key) => {
    data[key] = typeof value === "string" ? value.trim() : value;
  });
  return data;
};

const formatShortDate = (value) => {
  if (!value) return "Unknown date";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Unknown date";
  return date.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
};

/**
 * Wire authentication pages (login/register)
 */
const wireAuthPages = () => {
  const loginForm = document.getElementById("login-form");
  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      if (API.isLoading) return;

      const formData = parseFormData(loginForm);

      // Validation
      if (!formData.email) {
        toast("Email is required", "err");
        return;
      }
      if (!validateEmail(formData.email)) {
        toast("Invalid email format", "err");
        return;
      }
      if (!formData.password) {
        toast("Password is required", "err");
        return;
      }

      setLoading(true);
      try {
        const response = await API.req("/api/auth/login", {
          method: "POST",
          body: JSON.stringify({
            email: formData.email,
            password: formData.password,
          }),
        });

        if (!response.access) {
          throw new Error("No authentication token received");
        }

        localStorage.setItem("access", response.access);
        localStorage.setItem("refresh", response.refresh || "");
        localStorage.setItem("user", JSON.stringify(response.user));

        API.token = response.access;
        API.user = response.user;

        toast("Login successful");
        redirectByRole(response.user.role);
      } catch (error) {
        toast(error.message || "Login failed", "err", 5000);
        console.error("Login error:", error);
      } finally {
        setLoading(false);
      }
    });
  }

  const registerForm = document.getElementById("register-form");
  if (registerForm) {
    registerForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      if (API.isLoading) return;

      const formData = parseFormData(registerForm);

      // Validation
      if (!validateName(formData.name)) {
        toast("Name must be at least 2 characters", "err");
        return;
      }
      if (!validateEmail(formData.email)) {
        toast("Invalid email format", "err");
        return;
      }
      if (!validatePassword(formData.password)) {
        toast("Password must be at least 8 characters", "err");
        return;
      }
      if (formData.password !== formData.password_confirm) {
        toast("Passwords do not match", "err");
        return;
      }

      setLoading(true);
      try {
        const response = await API.req("/api/auth/register", {
          method: "POST",
          body: JSON.stringify({
            name: formData.name,
            email: formData.email,
            password: formData.password,
          }),
        });

        const message = response.detail || response.message || "Registration successful. You can now sign in.";
        const isError = response.error || false;

        toast(message, isError ? "err" : "ok", 5000);

        if (!isError) {
          registerForm.reset();
        }
      } catch (error) {
        toast(error.message || "Registration failed", "err", 5000);
        console.error("Registration error:", error);
      } finally {
        setLoading(false);
      }
    });
  }
};

/**
 * Wire public home page
 */
const wireHome = async () => {
  if (window.CIVIC_PAGE !== "home") return;

  const issuesContainer = document.getElementById("home-issues");
  const categoryContainer = document.getElementById("home-category-report");
  if (!issuesContainer || !categoryContainer) return;

  const updateStat = (id, value) => {
    const element = document.getElementById(id);
    if (element) {
      element.textContent = value;
    }
  };

  const renderCategories = (categories) => {
    if (!Array.isArray(categories) || categories.length === 0) {
      categoryContainer.innerHTML = "<p class='text-sm text-slate-400'>No category trends available yet.</p>";
      return;
    }

    categoryContainer.innerHTML = categories
      .map((item, index) => `
        <article class="rounded-2xl border border-white/10 bg-slate-900/40 p-4">
          <div class="flex items-center justify-between gap-3">
            <div>
              <p class="text-sm text-slate-400">Category ${index + 1}</p>
              <p class="font-semibold text-white">${Civic.escapeHtml(item.name || "Others")}</p>
            </div>
            <span class="status-pill bg-cyan-500/10 text-cyan-300">${item.count || 0} issues</span>
          </div>
        </article>
      `)
      .join("");
  };

  const renderIssues = (issues) => {
    if (!Array.isArray(issues) || issues.length === 0) {
      issuesContainer.innerHTML = "<p class='text-sm text-slate-400'>No public issues have been reported yet.</p>";
      return;
    }

    issuesContainer.innerHTML = issues
      .map((issue) => `
        <article class="issue-card !cursor-default gap-4" data-issue-id="${issue.id}">
          <div class="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
            <div class="space-y-2">
              <div class="flex items-center gap-2 flex-wrap">
                <span class="id-mono text-emerald-300">${Civic.escapeHtml(issue.issue_code || "N/A")}</span>
                <span class="status-pill ${Civic.getStatusColor(issue.status || "Submitted")}">${Civic.escapeHtml(issue.status || "Submitted")}</span>
                <span class="status-pill bg-slate-700/40 text-slate-300">${Civic.escapeHtml(issue.category || "Others")}</span>
              </div>
              <h3 class="font-semibold text-lg text-white">${Civic.escapeHtml(issue.title || "Untitled issue")}</h3>
              <p class="text-sm text-slate-300 leading-6">${Civic.escapeHtml(issue.description || "No description available.")}</p>
            </div>
            <div class="text-xs text-slate-400 whitespace-nowrap">${formatShortDate(issue.created_at)}</div>
          </div>
          <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pt-2">
            <div class="text-sm text-slate-400">
              ${Civic.escapeHtml(issue.location?.address || "District-wide report")}
            </div>
            <button
              type="button"
              class="btn-muted home-upvote-btn px-4 py-2 text-sm sm:w-auto"
              data-issue-id="${issue.id}"
              data-upvoted="${issue.upvoted ? "true" : "false"}"
            >
              ${issue.upvoted ? "Remove upvote" : "Upvote"} (${issue.upvote_count || 0})
            </button>
          </div>
        </article>
      `)
      .join("");

    issuesContainer.querySelectorAll(".home-upvote-btn").forEach((button) => {
      button.addEventListener("click", async () => {
        if (!API.user) {
          toast("Sign in to upvote issues", "err", 3000);
          window.location.href = "/login/";
          return;
        }

        try {
          setLoading(true);
          await API.req(`/api/issues/${button.dataset.issueId}/upvote/`, { method: "POST" });
          await loadHome();
        } catch (error) {
          toast(error.message || "Failed to update upvote", "err");
        } finally {
          setLoading(false);
        }
      });
    });
  };

  const loadHome = async () => {
    try {
      setLoading(true);
      const response = await API.req("/api/dashboard/public/home/");
      const summary = response.summary || {};

      updateStat("home-stat-total", summary.total_issues || 0);
      updateStat("home-stat-open", summary.open_issues || 0);
      updateStat("home-stat-resolved", summary.resolved_issues || 0);
      updateStat("home-stat-rate", `${summary.resolution_rate || 0}%`);

      renderCategories(summary.top_categories || []);
      renderIssues(response.issues || []);
    } catch (error) {
      issuesContainer.innerHTML = `<p class='text-sm text-red-300'>${Civic.escapeHtml(error.message || "Failed to load issues")}</p>`;
      categoryContainer.innerHTML = "<p class='text-sm text-slate-400'>Unable to load summary right now.</p>";
    } finally {
      setLoading(false);
    }
  };

  await loadHome();
};

/**
 * Wire citizen dashboard
 */
const wireCitizen = async () => {
  if (window.CIVIC_PAGE !== "citizen" || !API.user) return;

  try {
    setLoading(true);

    // Fetch the current user's issues for the citizen dashboard cards and stats
    const response = await API.req("/api/issues/?mine=1&page_size=100");
    
    if (!response.results || !Array.isArray(response.results)) {
      throw new Error("Invalid response format");
    }

    const issues = response.results;
    const openCount = response.results.filter(i => !["Resolved", "Closed"].includes(i.status)).length;
    const resolvedCount = response.results.filter(i => i.status === "Resolved").length;

    // Update statistics
    const updateStat = (id, value) => {
      const element = document.getElementById(id);
      if (element) {
        element.textContent = value;
      }
    };

    updateStat("stat-reports", response.count || 0);
    updateStat("stat-open", openCount);
    updateStat("stat-resolved", resolvedCount);

    // Render my reports
    const reportsContainer = document.getElementById("my-reports");
    if (reportsContainer) {
      if (response.results && response.results.length > 0) {
        reportsContainer.innerHTML = response.results
          .map(issue => `
            <div class='issue-card group cursor-pointer' data-issue-id='${issue.id}'>
              <div class='flex justify-between items-center'>
                <b class='id-mono text-emerald-300'>${Civic.escapeHtml(issue.issue_code || "N/A")}</b>
                <span class='status-pill ${Civic.getStatusColor(issue.status)}'>${Civic.escapeHtml(issue.status || "Unknown")}</span>
              </div>
              <div class='font-medium mt-1 line-clamp-1'>${Civic.escapeHtml(issue.title || "Untitled")}</div>
              <div class='flex items-center gap-2 text-xs text-slate-400 mt-1'>
                <span>${Civic.escapeHtml(issue.category || "Misc")}</span>
                <span>P${issue.priority || 0}</span>
                <span class='text-xs font-mono'>Upvotes: ${issue.upvote_count || 0}</span>
              </div>
            </div>
          `)
          .join("");
      } else {
        reportsContainer.innerHTML = `
          <p class='text-slate-400 py-4 text-center'>
            No reports yet. 
            <a href='/citizen/report/' class='text-emerald-400 hover:underline'>Create one</a>
          </p>
        `;
      }
    }

    // Fetch and render notifications
    try {
      const notificationsResponse = await API.req("/api/notifications/");
      const notifications = notificationsResponse.results || notificationsResponse || [];
      
      const notificationsContainer = document.getElementById("notifications");
      if (notificationsContainer) {
        if (Array.isArray(notifications) && notifications.length > 0) {
          notificationsContainer.innerHTML = notifications
            .slice(0, 8)
            .map((notif, index) => `
              <div class='issue-card text-sm' style='animation-delay:${index * 50}ms'>
                ${Civic.escapeHtml(notif.message || notif.title || "Notification")}
              </div>
            `)
            .join("");
        } else {
          notificationsContainer.innerHTML = "<p class='text-slate-400 py-4 text-center'>No notifications</p>";
        }
      }
    } catch (error) {
      console.error("Failed to load notifications:", error);
    }
  } catch (error) {
    toast(error.message || "Failed to load citizen data", "err");
    console.error("Citizen dashboard error:", error);
  } finally {
    setLoading(false);
  }
};

/**
 * Get status color class
 */
const getStatusColor = (status) => {
  const colors = {
    "Submitted": "bg-blue-500/20 text-blue-300",
    "In Progress": "bg-yellow-500/20 text-yellow-300",
    "Resolved": "bg-emerald-500/20 text-emerald-300",
    "Closed": "bg-gray-500/20 text-gray-300",
    "Assigned": "bg-purple-500/20 text-purple-300",
    "Verified": "bg-cyan-500/20 text-cyan-300",
  };

  return colors[status] || "bg-slate-600/20 text-slate-300";
};

/**
 * Create issue card HTML
 */
const makeCard = (issue) => {
  return `
    <div class='issue-card' draggable='true' data-id='${issue.id}' data-status='${issue.status || "Submitted"}'>
      <div class='flex justify-between items-center'>
        <strong class='id-mono text-sm text-emerald-300'>${Civic.escapeHtml(issue.issue_code || "N/A")}</strong>
        <span class='status-pill ${getStatusColor(issue.status || "Submitted")}'>P${issue.priority || 0}</span>
      </div>
      <div class='text-sm font-medium mt-1 line-clamp-1'>${Civic.escapeHtml(issue.title || "Untitled")}</div>
      <div class='text-xs text-slate-400 mt-1'>${Civic.escapeHtml(issue.category || "Misc")}</div>
    </div>
  `;
};

/**
 * Wire officer Kanban board
 */
const wireOfficer = async () => {
  if (window.CIVIC_PAGE !== "officer" || !API.user) return;

  try {
    setLoading(true);

    const response = await API.req("/api/issues/?page_size=100");
    if (!response.results || !Array.isArray(response.results)) {
      throw new Error("Invalid response");
    }

    const issues = response.results;
    const statusMap = {
      "Submitted": "col-submitted",
      "In Progress": "col-progress",
      "Resolved": "col-resolved",
    };

    // Clear columns
    Object.values(statusMap).forEach(columnId => {
      const column = document.getElementById(columnId);
      if (column) column.innerHTML = "";
    });

    // Populate columns
    issues.forEach(issue => {
      const columnId = statusMap[issue.status];
      if (columnId) {
        const column = document.getElementById(columnId);
        if (column) {
          column.insertAdjacentHTML("beforeend", makeCard(issue));
        }
      }
    });

    // Setup drag and drop
    let draggedId = null;
    let draggedFromStatus = null;

    document.querySelectorAll(".issue-card").forEach(card => {
      card.addEventListener("dragstart", (e) => {
        draggedId = card.dataset.id;
        draggedFromStatus = card.dataset.status;
        e.dataTransfer.effectAllowed = "move";
        card.style.opacity = "0.5";
      });

      card.addEventListener("dragend", () => {
        card.style.opacity = "1";
      });
    });

    document.querySelectorAll(".kanban-col").forEach(column => {
      column.addEventListener("dragover", (e) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = "move";
        column.parentElement.classList.add("drag-over");
      });

      column.addEventListener("dragleave", () => {
        column.parentElement.classList.remove("drag-over");
      });

      column.addEventListener("drop", async (e) => {
        e.preventDefault();
        column.parentElement.classList.remove("drag-over");

        if (!draggedId) return;

        const newStatus = column.dataset.status;
        if (draggedFromStatus === newStatus) return;

        setLoading(true);
        try {
          await API.req(`/api/issues/${draggedId}/status/`, {
            method: "PATCH",
            body: JSON.stringify({ status: newStatus }),
          });

          toast(`Moved to ${newStatus}`);
          await wireOfficer();
        } catch (error) {
          toast(error.message || "Failed to update status", "err");
          console.error("Status update error:", error);
        } finally {
          setLoading(false);
          draggedId = null;
          draggedFromStatus = null;
        }
      });
    });
  } catch (error) {
    toast(error.message || "Failed to load officer board", "err");
    console.error("Officer board error:", error);
  } finally {
    setLoading(false);
  }
};

/**
 * Wire admin dashboard
 */
const wireAdmin = async () => {
  if (window.CIVIC_PAGE !== "admin" || !API.user) return;

  try {
    setLoading(true);

    const analyticsResponse = await API.req("/api/dashboard/admin/analytics/");
    if (!analyticsResponse) {
      throw new Error("No analytics data");
    }

    const updateStat = (id, value) => {
      const element = document.getElementById(id);
      if (element) {
        element.textContent = value;
      }
    };

    updateStat("adm-total", analyticsResponse.total_issues || 0);
    updateStat("adm-rate", `${analyticsResponse.resolution_rate || 0}%`);

    // Load wards
    try {
      const wardsResponse = await API.req("/api/wards/");
      const wards = wardsResponse.results || wardsResponse || [];
      
      updateStat("adm-wards", Array.isArray(wards) ? wards.length : 0);

      const wardList = document.getElementById("ward-list");
      if (wardList) {
        if (Array.isArray(wards) && wards.length > 0) {
          wardList.innerHTML = wards
            .map((ward, index) => `
              <div class='issue-card' style='animation-delay:${index * 30}ms'>
                <div class='font-medium'>${Civic.escapeHtml(ward.name || "Ward")}</div>
                <div class='text-xs text-slate-400'>${Civic.escapeHtml(ward.district || "District")}</div>
              </div>
            `)
            .join("");
        } else {
          wardList.innerHTML = "<p class='text-slate-400 py-4'>No wards configured</p>";
        }
      }
    } catch (error) {
      console.error("Failed to load wards:", error);
    }

    // Setup analytics chart
    try {
      const chartElement = document.getElementById("analyticsChart");
      if (chartElement && typeof Chart !== "undefined") {
        const categoryBreakdown = analyticsResponse.category_breakdown || {};
        const labels = Object.keys(categoryBreakdown);
        const data = Object.values(categoryBreakdown);

        new Chart(chartElement, {
          type: "bar",
          data: {
            labels: labels.length > 0 ? labels : ["No Data"],
            datasets: [
              {
                label: "Issues by Category",
                data: data.length > 0 ? data : [0],
                backgroundColor: "#00C896",
                borderColor: "#00C896",
                borderWidth: 1,
                borderRadius: 4,
                hoverBackgroundColor: "#00D9A3",
              },
            ],
          },
          options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
              legend: {
                labels: { color: "#E6EDF3" },
              },
            },
            scales: {
              y: {
                ticks: { color: "#E6EDF3" },
                grid: { color: "rgba(255,255,255,.05)" },
              },
              x: {
                ticks: { color: "#E6EDF3" },
                grid: { color: "rgba(255,255,255,.05)" },
              },
            },
          },
        });
      }
    } catch (error) {
      console.error("Chart error:", error);
    }
  } catch (error) {
    toast(error.message || "Failed to load admin dashboard", "err");
    console.error("Admin dashboard error:", error);
  } finally {
    setLoading(false);
  }
};

/**
 * Initialize shell (theme, session, navigation)
 */
const initShell = () => {
  // Theme management
  const applyTheme = (theme) => {
    if (theme === "light") {
      document.documentElement.classList.remove("dark");
    } else {
      document.documentElement.classList.add("dark");
    }
  };

  const savedTheme = localStorage.getItem("theme") || "dark";
  applyTheme(savedTheme);

  const themeToggle = document.getElementById("theme-toggle");
  if (themeToggle) {
    themeToggle.addEventListener("click", () => {
      const isDark = document.documentElement.classList.contains("dark");
      const newTheme = isDark ? "light" : "dark";
      applyTheme(newTheme);
      localStorage.setItem("theme", newTheme);
      toast(`Switched to ${newTheme} mode`, "ok", 2000);
    });
  }

  // Logout button
  const logoutBtn = document.getElementById("logout-btn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", logout);
  }

  // Session UI
  const sessionUser = document.getElementById("session-user");
  const loginBtn = document.getElementById("login-btn");
  const registerBtn = document.getElementById("register-btn");

  if (API.user) {
    if (sessionUser) {
      sessionUser.textContent = `${(API.user.role || "user").toUpperCase()} • ${API.user.name || API.user.id}`;
    }
    loginBtn?.classList.add("hidden");
    registerBtn?.classList.add("hidden");
    logoutBtn?.classList.remove("hidden");
  } else {
    loginBtn?.classList.remove("hidden");
    registerBtn?.classList.remove("hidden");
    logoutBtn?.classList.add("hidden");
  }

  // Lightbox modal
  const lightbox = document.getElementById('image-lightbox');
  const closeLightbox = document.getElementById('close-lightbox');
  if (lightbox) {
    if (closeLightbox) {
      closeLightbox.addEventListener('click', () => lightbox.classList.add('hidden'));
    }
    lightbox.addEventListener('click', (e) => {
      if (e.target === lightbox) {
        lightbox.classList.add('hidden');
      }
    });
  }
};

/**
 * Escape HTML special characters
 */
const escapeHtml = (text) => {
  if (!text) return "";
  const map = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  };
  return text.toString().replace(/[&<>"']/g, m => map[m]);
};

/**
 * Enforce authentication on protected pages
 */
const enforceAuthenticatedPages = () => {
  const protectedPages = ["report"];
  if (protectedPages.includes(window.CIVIC_PAGE) && !API.token) {
    toast("You must be logged in to access this page", "err", 3000);
    setTimeout(() => {
      window.location.href = "/login/?next=" + encodeURIComponent(window.location.pathname);
    }, 1500);
  }
};

/**
 * Redirect already authenticated users away from login
 */
const redirectAuthenticatedFromLogin = () => {
  if (["login", "register"].includes(window.CIVIC_PAGE) && API.user?.role) {
    redirectByRole(API.user.role);
  }
};

// Export API for external use
window.Civic = {
  API,
  toast,
  setLoading,
  escapeHtml,
  getStatusColor,
  validateEmail,
  validatePassword,
  showLightbox: (src) => {
    const lightbox = document.getElementById('image-lightbox');
    const img = document.getElementById('lightbox-image');
    if (lightbox && img) {
      img.src = src;
      lightbox.classList.remove('hidden');
    }
  }
};

// Initialize application
document.addEventListener("DOMContentLoaded", () => {
  initShell();
  enforceAuthenticatedPages();
  redirectAuthenticatedFromLogin();
  wireHome();
  wireAuthPages();
  wireCitizen();
  wireOfficer();
  wireAdmin();
});
