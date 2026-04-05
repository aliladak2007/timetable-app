export function PageHeader({ title, subtitle, actions }) {
  return (
    <header className="page-header">
      <div>
        <p className="eyebrow">Admin workflow</p>
        <h2>{title}</h2>
        {subtitle ? <p className="subtle-text">{subtitle}</p> : null}
      </div>
      {actions ? <div className="header-actions">{actions}</div> : null}
    </header>
  );
}
