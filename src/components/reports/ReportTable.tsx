"use client";

export interface Column<T> {
  key: keyof T & string;
  label: string;
  align?: "left" | "right" | "center";
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  format?: (value: any) => string;
}

interface ReportTableProps<T> {
  title: string;
  description?: string;
  columns: Column<T>[];
  rows: T[];
  footnote?: string;
}

export default function ReportTable<T>({
  title,
  description,
  columns,
  rows,
  footnote,
}: ReportTableProps<T>) {
  return (
    <div className="report-section">
      <h3 className="text-base font-semibold mb-1">{title}</h3>
      {description && (
        <p className="text-xs text-zinc-500 mb-3 print-muted">{description}</p>
      )}
      <div className="overflow-x-auto">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr>
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={`px-3 py-2 text-xs font-semibold uppercase tracking-wider border border-zinc-700 bg-zinc-800/80 print-th ${
                    col.align === "right"
                      ? "text-right"
                      : col.align === "center"
                        ? "text-center"
                        : "text-left"
                  }`}
                >
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr
                key={i}
                className={i % 2 === 0 ? "bg-zinc-900/30" : "bg-zinc-900/60"}
              >
                {columns.map((col) => (
                  <td
                    key={col.key}
                    className={`px-3 py-2 border border-zinc-800 print-td ${
                      col.align === "right"
                        ? "text-right tabular-nums"
                        : col.align === "center"
                          ? "text-center"
                          : "text-left"
                    }`}
                  >
                    {col.format
                      ? col.format((row as Record<string, unknown>)[col.key])
                      : String((row as Record<string, unknown>)[col.key] ?? "")}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {footnote && (
        <p className="text-xs text-zinc-600 mt-1.5 italic print-muted">
          {footnote}
        </p>
      )}
    </div>
  );
}
