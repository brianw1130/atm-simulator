import { type FormEvent, useState } from "react";
import { Modal } from "./Modal";
import { FormField } from "./FormField";

interface PinResetModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (newPin: string) => Promise<void>;
  cardNumber: string;
}

function validatePinComplexity(pin: string): string | null {
  if (!/^\d+$/.test(pin)) return "PIN must contain only digits";
  if (pin.length < 4 || pin.length > 6) return "PIN must be 4-6 digits";
  if (new Set(pin).size === 1) return "PIN cannot be all the same digit";

  const digits = [...pin].map(Number);
  const isAsc = digits.every(
    (d, i) => i === 0 || d === (digits[i - 1] ?? 0) + 1,
  );
  const isDesc = digits.every(
    (d, i) => i === 0 || d === (digits[i - 1] ?? 0) - 1,
  );
  if (isAsc || isDesc) return "PIN cannot be sequential digits";

  return null;
}

export function PinResetModal({
  isOpen,
  onClose,
  onSubmit,
  cardNumber,
}: PinResetModalProps) {
  const [newPin, setNewPin] = useState("");
  const [confirmPin, setConfirmPin] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const pinError = newPin.length >= 4 ? validatePinComplexity(newPin) : null;
  const matchError =
    confirmPin && newPin !== confirmPin ? "PINs do not match" : null;

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    const complexityError = validatePinComplexity(newPin);
    if (complexityError) {
      setError(complexityError);
      return;
    }
    if (newPin !== confirmPin) {
      setError("PINs do not match");
      return;
    }

    setIsLoading(true);
    try {
      await onSubmit(newPin);
      setNewPin("");
      setConfirmPin("");
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

  const isValid = newPin.length >= 4 && !pinError && !matchError && confirmPin;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Reset PIN">
      <p className="text-muted">Card: {cardNumber}</p>
      <form onSubmit={(e) => void handleSubmit(e)}>
        {error && (
          <div className="form-error-banner" role="alert">
            {error}
          </div>
        )}
        <FormField
          id="newPin"
          label="New PIN"
          type="password"
          value={newPin}
          onChange={(e) => setNewPin(e.target.value)}
          maxLength={6}
          error={pinError ?? undefined}
          disabled={isLoading}
        />
        <FormField
          id="confirmPin"
          label="Confirm PIN"
          type="password"
          value={confirmPin}
          onChange={(e) => setConfirmPin(e.target.value)}
          maxLength={6}
          error={matchError ?? undefined}
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
            className="btn btn--danger"
            disabled={!isValid || isLoading}
          >
            {isLoading ? "Resetting..." : "Reset PIN"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
