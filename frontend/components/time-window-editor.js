"use client";

import { formatTime, weekdayLabels } from "../lib/api";

const defaultRow = { weekday: 0, start_minute: 900, end_minute: 960 };

function toInput(minute) {
  const hours = Math.floor(minute / 60);
  const mins = minute % 60;
  return `${String(hours).padStart(2, "0")}:${String(mins).padStart(2, "0")}`;
}

function toMinute(value) {
  const [hours, mins] = value.split(":").map(Number);
  return (hours * 60) + mins;
}

export function TimeWindowEditor({ rows, setRows, withPriority = false, withReason = false, label }) {
  const updateRow = (index, key, value) => {
    const next = rows.map((row, rowIndex) => (rowIndex === index ? { ...row, [key]: value } : row));
    setRows(next);
  };

  const addRow = () => {
    setRows([...rows, { ...defaultRow, ...(withPriority ? { priority: 1 } : {}), ...(withReason ? { reason: "" } : {}) }]);
  };

  const removeRow = (index) => {
    setRows(rows.filter((_, rowIndex) => rowIndex !== index));
  };

  return (
    <section className="panel">
      <div className="panel-header">
        <h3>{label}</h3>
        <button type="button" className="button secondary" onClick={addRow}>
          Add window
        </button>
      </div>
      <div className="editor-grid">
        {rows.map((row, index) => (
          <div key={`${row.weekday}-${index}`} className="editor-row">
            <select value={row.weekday} onChange={(event) => updateRow(index, "weekday", Number(event.target.value))}>
              {weekdayLabels.map((weekday, weekdayIndex) => (
                <option key={weekday} value={weekdayIndex}>
                  {weekday}
                </option>
              ))}
            </select>
            <input
              type="time"
              value={toInput(row.start_minute)}
              onChange={(event) => updateRow(index, "start_minute", toMinute(event.target.value))}
            />
            <input
              type="time"
              value={toInput(row.end_minute)}
              onChange={(event) => updateRow(index, "end_minute", toMinute(event.target.value))}
            />
            {withPriority ? (
              <input
                type="number"
                min="1"
                max="5"
                value={row.priority}
                onChange={(event) => updateRow(index, "priority", Number(event.target.value))}
              />
            ) : null}
            {withReason ? (
              <input
                type="text"
                placeholder="Reason"
                value={row.reason || ""}
                onChange={(event) => updateRow(index, "reason", event.target.value)}
              />
            ) : null}
            <button type="button" className="button danger" onClick={() => removeRow(index)}>
              Remove
            </button>
          </div>
        ))}
        {!rows.length ? <p className="muted">No windows defined yet.</p> : null}
      </div>
    </section>
  );
}
