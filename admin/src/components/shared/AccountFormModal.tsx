import { type FormEvent, useState } from "react";
import { Modal } from "./Modal";
import type { AccountCreateData } from "../../api/types";

interface AccountFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: AccountCreateData) => Promise<void>;
}

export function AccountFormModal({
  isOpen,
  onClose,
  onSubmit,
}: AccountFormModalProps) {
  const [accountType, setAccountType] = useState<"CHECKING" | "SAVINGS">(
    "CHECKING",
  );
  const [initialBalance, setInitialBalance] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    try {
      const balanceDollars = parseFloat(initialBalance || "0");
      const balanceCents = Math.round(balanceDollars * 100);
      await onSubmit({
        account_type: accountType,
        initial_balance_cents: balanceCents,
      });
      setAccountType("CHECKING");
      setInitialBalance("");
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

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Create Account">
      <form onSubmit={(e) => void handleSubmit(e)}>
        {error && (
          <div className="form-error-banner" role="alert">
            {error}
          </div>
        )}
        <div className="form-group">
          <label className="form-label" htmlFor="accountType">
            Account Type
          </label>
          <select
            id="accountType"
            className="form-input"
            value={accountType}
            onChange={(e) =>
              setAccountType(e.target.value as "CHECKING" | "SAVINGS")
            }
            disabled={isLoading}
          >
            <option value="CHECKING">Checking</option>
            <option value="SAVINGS">Savings</option>
          </select>
        </div>
        <div className="form-group">
          <label className="form-label" htmlFor="initialBalance">
            Initial Balance ($)
          </label>
          <input
            id="initialBalance"
            className="form-input"
            type="number"
            min="0"
            step="0.01"
            value={initialBalance}
            onChange={(e) => setInitialBalance(e.target.value)}
            placeholder="0.00"
            disabled={isLoading}
          />
        </div>
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
            disabled={isLoading}
          >
            {isLoading ? "Creating..." : "Create Account"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
