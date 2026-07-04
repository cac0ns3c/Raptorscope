// SPDX-License-Identifier: GPL-3.0-or-later
import "@testing-library/jest-dom/vitest";

// Some jsdom + Node combinations don't expose window.localStorage. Provide a
// minimal in-memory implementation so storage-backed features are testable.
if (typeof window !== "undefined" && !window.localStorage) {
  const mem = new Map<string, string>();
  const storage: Storage = {
    get length() {
      return mem.size;
    },
    clear: () => mem.clear(),
    getItem: (k) => (mem.has(k) ? mem.get(k)! : null),
    key: (i) => Array.from(mem.keys())[i] ?? null,
    removeItem: (k) => void mem.delete(k),
    setItem: (k, v) => void mem.set(k, String(v)),
  };
  Object.defineProperty(window, "localStorage", {
    value: storage,
    configurable: true,
  });
}
