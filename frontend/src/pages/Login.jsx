
import { useState } from "react";
import PropTypes from "prop-types";
import { login, register } from "../services/auth";

const Login = ({ onLogin }) => {
  const [isRegister, setIsRegister] = useState(false);

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    setError("");
    setSuccess("");
    setLoading(true);

    try {
      if (isRegister) {
        // REGISTER
        await register(name, email, password);

        setSuccess(
          "Registration successful! Please sign in."
        );

        // Switch to login
        setIsRegister(false);

        setName("");
        setPassword("");
      } else {
        // LOGIN
        await login(email, password);

        // Open dashboard
        onLogin();
      }
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          err.response?.data?.message ||
          (isRegister
            ? "Registration failed."
            : "Invalid email or password.")
      );
    } finally {
      setLoading(false);
    }
  };

  const switchMode = () => {
    setIsRegister(!isRegister);

    setError("");
    setSuccess("");
    setName("");
    setEmail("");
    setPassword("");
  };

  return (
    <div className="login-page">

      <div className="login-card">

        <div className="login-logo">
          JS
        </div>

        <h1>Distributed Job Scheduler</h1>

        <p>
          {isRegister
            ? "Create your account"
            : "Sign in to your account"}
        </p>

        <form onSubmit={handleSubmit}>

          {isRegister && (
            <>
              <label>Full Name</label>

              <input
                type="text"
                value={name}
                onChange={(e) =>
                  setName(e.target.value)
                }
                placeholder="Enter your name"
                required
              />
            </>
          )}

          <label>Email</label>

          <input
            type="email"
            value={email}
            onChange={(e) =>
              setEmail(e.target.value)
            }
            placeholder="admin@example.com"
            required
          />

          <label>Password</label>

          <input
            type="password"
            value={password}
            onChange={(e) =>
              setPassword(e.target.value)
            }
            placeholder="Enter password"
            minLength={6}
            required
          />

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          {success && (
            <div className="success-message">
              {success}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
          >
            {loading
              ? "Please wait..."
              : isRegister
              ? "Create Account"
              : "Sign In"}
          </button>

        </form>

        <div className="auth-switch">

          {isRegister ? (
            <p>
              Already have an account?{" "}

              <button
                type="button"
                onClick={switchMode}
              >
                Sign In
              </button>
            </p>
          ) : (
            <p>
              Don&apos;t have an account?

              <button
                type="button"
                onClick={switchMode}
              >
                Create Account
              </button>
            </p>
          )}

        </div>

      </div>

    </div>
  );
};

Login.propTypes = {
  onLogin: PropTypes.func.isRequired,
};

export default Login;

