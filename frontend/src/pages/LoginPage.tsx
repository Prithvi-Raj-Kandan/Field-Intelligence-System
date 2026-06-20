import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { login } from "../api/auth";
import { ApiError } from "../api/client";
import { Button } from "../components/Button";
import { TextField } from "../components/Input";
import { useAuth } from "../context/AuthContext";
import "./AuthPage.css";

export function LoginPage() {
  const navigate = useNavigate();
  const { setUser } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await login(email, password);
      setUser(res.user);
      navigate(res.user.role === "manager" ? "/manager" : "/app/log");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-page__card animate-in">
        <p className="auth-page__brand">The/Nudge Institute</p>
        <h1>Sign in</h1>
        <p className="auth-page__hint">Field workers and managers sign in here</p>
        <form className="auth-page__form" onSubmit={handleSubmit}>
          <TextField
            label="Email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <TextField
            label="Password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          {error ? <p className="auth-page__error">{error}</p> : null}
          <Button type="submit" fullWidth size="lg" loading={loading}>
            Sign in
          </Button>
        </form>
        <p className="auth-page__switch">
          New here? <Link to="/signup">Create an account</Link>
        </p>
        <Link to="/" className="auth-page__back">
          ← Back to home
        </Link>
      </div>
    </div>
  );
}
