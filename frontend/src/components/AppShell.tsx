interface AppShellProps {
  view: 'employee' | 'knowledge' | 'operations'
  onChangeView: (view: 'employee' | 'knowledge' | 'operations') => void
  children: React.ReactNode
}

export function AppShell({ view, onChangeView, children }: AppShellProps) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">IT</div>
          <div>
            <strong>IT Assist</strong>
            <span>Enterprise ITSM</span>
          </div>
        </div>

        <div className="nav-label">WORKSPACE</div>

        <button className={`nav-item ${view === 'employee' ? 'active' : ''}`} onClick={() => onChangeView('employee')}>
          <span>⌂</span> Employee Portal
        </button>
        <button className={`nav-item ${view === 'knowledge' ? 'active' : ''}`} onClick={() => onChangeView('knowledge')}>
          <span>◇</span> Knowledge Base
        </button>
        <button className={`nav-item ${view === 'operations' ? 'active' : ''}`} onClick={() => onChangeView('operations')}>
          <span>▦</span> ITSM Operations
        </button>

        <div className="sidebar-footer">
          <div className="status-dot"><i /> API via FastAPI</div>
          <small>AI-assisted IT service management</small>
        </div>
      </aside>
      <main className="main-content">{children}</main>
    </div>
  )
}
