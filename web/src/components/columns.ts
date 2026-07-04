// SPDX-License-Identifier: GPL-3.0-or-later
// Per-dataset column definitions for the artifact table.

export interface Column {
  header: string;
  path: string;
}

export const COLUMNS: Record<string, Column[]> = {
  "macos.persistence": [
    { header: "Type", path: "raptorscope.persistence.type" },
    { header: "Label", path: "raptorscope.persistence.label" },
    { header: "Path", path: "file.path" },
    { header: "Executable", path: "process.executable" },
  ],
  "macos.process": [
    { header: "Name", path: "process.name" },
    { header: "PID", path: "process.pid" },
    { header: "Executable", path: "process.executable" },
    { header: "User", path: "user.name" },
    { header: "Signed", path: "process.code_signature.trusted" },
  ],
  "macos.quarantine": [
    { header: "File", path: "file.name" },
    { header: "Origin", path: "url.original" },
    { header: "Agent", path: "process.name" },
  ],
  "macos.tcc": [
    { header: "Service", path: "raptorscope.tcc.service" },
    { header: "Client", path: "raptorscope.tcc.client" },
    { header: "Allowed", path: "raptorscope.tcc.allowed" },
  ],
  "macos.inventory": [
    { header: "App", path: "raptorscope.app.name" },
    { header: "Version", path: "raptorscope.app.version" },
    { header: "Path", path: "file.path" },
    { header: "Signed", path: "raptorscope.app.signed" },
  ],
};

export const DEFAULT_COLUMNS: Column[] = [
  { header: "Timestamp", path: "@timestamp" },
  { header: "Path", path: "file.path" },
];

export function columnsFor(dataset: string): Column[] {
  return COLUMNS[dataset] ?? DEFAULT_COLUMNS;
}
