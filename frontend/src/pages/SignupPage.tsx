import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { register } from "../api/auth";
import { ApiError } from "../api/client";
import { Button } from "../components/Button";
import { TextField } from "../components/Input";
import { useAuth } from "../context/AuthContext";
import "./AuthPage.css";

export function SignupPage() {
  const navigate = useNavigate();
  const { setUser } = useAuth();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await register(email, password, name, "field_worker");
      setUser(res.user);
      navigate("/app/log");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-page__card animate-in">
        <p className="auth-page__brand">The/Nudge Institute</p>
        <h1>Create account</h1>
        <p className="auth-page__hint">Field worker accounts only — managers are provisioned by admin</p>
        <form className="auth-page__form" onSubmit={handleSubmit}>
          <TextField
            label="Full name"
            type="text"
            autoComplete="name"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
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
            autoComplete="new-password"
            required
            minLength={10}
            hint="At least 10 characters — avoid common or breached passwords"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          {error ? <p className="auth-page__error">{error}</p> : null}
          <Button type="submit" fullWidth size="lg" loading={loading}>
            Create account
          </Button>
        </form>
        <p className="auth-page__switch">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
