import type { InputHTMLAttributes, ReactNode, SelectHTMLAttributes, TextareaHTMLAttributes } from "react";
import "./Input.css";

interface FieldProps {
  label: string;
  hint?: string;
  error?: string;
}

export function TextField({
  label,
  hint,
  error,
  id,
  className = "",
  ...props
}: FieldProps & InputHTMLAttributes<HTMLInputElement>) {
  const fieldId = id ?? label.toLowerCase().replace(/\s+/g, "-");
  return (
    <label className={`field ${className}`} htmlFor={fieldId}>
      <span className="field__label">{label}</span>
      <input id={fieldId} className={`field__input ${error ? "field__input--error" : ""}`} {...props} />
      {hint && !error ? <span className="field__hint">{hint}</span> : null}
      {error ? <span className="field__error">{error}</span> : null}
    </label>
  );
}

export function TextAreaField({
  label,
  hint,
  error,
  id,
  className = "",
  ...props
}: FieldProps & TextareaHTMLAttributes<HTMLTextAreaElement>) {
  const fieldId = id ?? label.toLowerCase().replace(/\s+/g, "-");
  return (
    <label className={`field ${className}`} htmlFor={fieldId}>
      <span className="field__label">{label}</span>
      <textarea
        id={fieldId}
        className={`field__input field__textarea ${error ? "field__input--error" : ""}`}
        {...props}
      />
      {hint && !error ? <span className="field__hint">{hint}</span> : null}
      {error ? <span className="field__error">{error}</span> : null}
    </label>
  );
}

export function SelectField({
  label,
  hint,
  error,
  id,
  children,
  className = "",
  ...props
}: FieldProps & SelectHTMLAttributes<HTMLSelectElement> & { children: ReactNode }) {
  const fieldId = id ?? label.toLowerCase().replace(/\s+/g, "-");
  return (
    <label className={`field ${className}`} htmlFor={fieldId}>
      <span className="field__label">{label}</span>
      <select id={fieldId} className={`field__input field__select ${error ? "field__input--error" : ""}`} {...props}>
        {children}
      </select>
      {hint && !error ? <span className="field__hint">{hint}</span> : null}
      {error ? <span className="field__error">{error}</span> : null}
    </label>
  );
}
