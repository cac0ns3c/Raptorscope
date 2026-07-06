// SPDX-License-Identifier: GPL-3.0-or-later
import type { ReactNode } from "react";

import { IconAlert, IconShieldCheck } from "./icons";

type Variant = "loading" | "empty" | "error";

/**
 * Shared loading / empty / error state block so every view renders these the same
 * way. The `error` variant is announced (`role="alert"`) and can offer a Retry;
 * the `clear` tone renders the green all-clear treatment.
 */
export function State({
  variant,
  message,
  icon,
  tone,
  onRetry,
}: {
  variant: Variant;
  message: string;
  icon?: ReactNode;
  tone?: "clear";
  onRetry?: () => void;
}) {
  if (variant === "loading") {
    return (
      <div className="state" role="status">
        <span className="spinner" /> {message}
      </div>
    );
  }
  if (variant === "empty") {
    if (tone === "clear") {
      return (
        <div className="empty-clear">
          {icon ?? <IconShieldCheck />}
          {message}
        </div>
      );
    }
    return (
      <div className="state state-empty">
        {icon}
        <span>{message}</span>
      </div>
    );
  }
  return (
    <div className="state state-error" role="alert">
      <IconAlert />
      <span>{message}</span>
      {onRetry && (
        <button className="btn-retry" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
}
