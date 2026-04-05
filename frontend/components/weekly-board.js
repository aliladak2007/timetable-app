import { formatTime, weekdayLabels } from "../lib/api";

export function WeeklyBoard({ title, items, emptyLabel = "No entries" }) {
  return (
    <section className="panel">
      <div className="panel-header">
        <h3>{title}</h3>
      </div>
      <div className="weekly-board">
        {weekdayLabels.map((label, weekday) => {
          const dayItems = items.filter((item) => item.weekday === weekday);
          return (
            <div key={label} className="day-column">
              <strong>{label}</strong>
              <div className="day-stack">
                {dayItems.length ? (
                  dayItems
                    .sort((a, b) => a.start_minute - b.start_minute)
                    .map((item, index) => (
                      <div key={`${label}-${index}-${item.start_minute}`} className="slot-chip">
                        <span>
                          {formatTime(item.start_minute)}-{formatTime(item.end_minute)}
                        </span>
                        {item.priority ? <small>P{item.priority}</small> : null}
                        {item.reason ? <small>{item.reason}</small> : null}
                        {item.subject ? <small>{item.subject}</small> : null}
                      </div>
                    ))
                ) : (
                  <p className="muted">{emptyLabel}</p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
