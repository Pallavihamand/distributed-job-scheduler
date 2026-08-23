
import api from "./api";

// ============================================================
// REGISTER
// ============================================================

export const register = async (name, email, password) => {
  const response = await api.post("/users", {
    name,
    email,
    password,
  });

  return response.data;
};

// ============================================================
// LOGIN
// ============================================================

export const login = async (email, password) => {
  const response = await api.post("/auth/login", {
    email,
    password,
  });

  const token = response.data.access_token;

  // Save JWT token
  localStorage.setItem("access_token", token);

  // Save logged-in user's email
  localStorage.setItem("user_email", email);

  return response.data;
};

// ============================================================
// LOGOUT
// ============================================================

export const logout = () => {
  localStorage.removeItem("access_token");
  localStorage.removeItem("token");
  localStorage.removeItem("user");
  localStorage.removeItem("user_email");
};

// ============================================================
// AUTH CHECK
// ============================================================

export const isAuthenticated = () => {
  return !!localStorage.getItem("access_token");
};

