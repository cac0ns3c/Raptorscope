// SPDX-License-Identifier: GPL-3.0-or-later
import DOMPurify from "dompurify";
import { marked } from "marked";
import { useMemo } from "react";

/** Render markdown to sanitized HTML. Used for both first-party docs and model
 *  output — the latter is derived from potentially attacker-controlled collected
 *  artifacts, so the HTML is always run through DOMPurify. */
export function Markdown({ text, className }: { text: string; className?: string }) {
  const html = useMemo(
    () => DOMPurify.sanitize(marked.parse(text) as string),
    [text],
  );
  return (
    <div
      className={`markdown ${className ?? ""}`}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
