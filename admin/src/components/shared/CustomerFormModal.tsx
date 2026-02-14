import { type FormEvent, useEffect, useState } from "react";
import { Modal } from "./Modal";
import { FormField } from "./FormField";
import type { AdminCustomer, CustomerCreateData } from "../../api/types";

interface CustomerFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: CustomerCreateData) => Promise<void>;
  customer?: AdminCustomer | null;
}

export function CustomerFormModal({
  isOpen,
  onClose,
  onSubmit,
  customer,
}: CustomerFormModalProps) {
  const isEdit = !!customer;
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [dateOfBirth, setDateOfBirth] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (isOpen && customer) {
      setFirstName(customer.first_name);
      setLastName(customer.last_name);
      setEmail(customer.email);
      setPhone(customer.phone ?? "");
      setDateOfBirth(customer.date_of_birth);
      setError(null);
    } else if (isOpen) {
      setFirstName("");
      setLastName("");
      setEmail("");
      setPhone("");
      setDateOfBirth("");
      setError(null);
    }
  }, [isOpen, customer]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    try {
      const data: CustomerCreateData = {
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        email: email.trim(),
        date_of_birth: dateOfBirth,
      };
      if (phone.trim()) {
        data.phone = phone.trim();
      }
      await onSubmit(data);
      onClose();
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("An error occurred");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const isValid =
    firstName.trim() && lastName.trim() && email.trim() && dateOfBirth;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEdit ? "Edit Customer" : "Create Customer"}
    >
      <form onSubmit={(e) => void handleSubmit(e)}>
        {error && (
          <div className="form-error-banner" role="alert">
            {error}
          </div>
        )}
        <FormField
          id="firstName"
          label="First Name"
          value={firstName}
          onChange={(e) => setFirstName(e.target.value)}
          required
          disabled={isLoading}
        />
        <FormField
          id="lastName"
          label="Last Name"
          value={lastName}
          onChange={(e) => setLastName(e.target.value)}
          required
          disabled={isLoading}
        />
        <FormField
          id="email"
          label="Email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          disabled={isLoading}
        />
        <FormField
          id="phone"
          label="Phone (optional)"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          disabled={isLoading}
        />
        <FormField
          id="dateOfBirth"
          label="Date of Birth"
          type="date"
          value={dateOfBirth}
          onChange={(e) => setDateOfBirth(e.target.value)}
          required
          disabled={isLoading}
        />
        <div className="modal-footer">
          <button
            type="button"
            className="btn btn--outline"
            onClick={onClose}
            disabled={isLoading}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="btn btn--primary"
            disabled={!isValid || isLoading}
          >
            {isLoading ? "Saving..." : isEdit ? "Update" : "Create"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
