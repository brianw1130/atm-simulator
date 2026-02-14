import type { InputHTMLAttributes } from "react";

interface FormFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
}

export function FormField({ label, error, id, ...inputProps }: FormFieldProps) {
  return (
    <div className="form-group">
      <label className="form-label" htmlFor={id}>
        {label}
      </label>
      <input className={`form-input ${error ? "form-input--error" : ""}`} id={id} {...inputProps} />
      {error && <span className="form-error">{error}</span>}
    </div>
  );
}
