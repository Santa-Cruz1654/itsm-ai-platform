import { useState } from 'react'
import { AppShell } from './components/AppShell'
import { EmployeePortal } from './pages/EmployeePortal'
import { KnowledgeBase } from './pages/KnowledgeBase'
import { OperationsDashboard } from './pages/OperationsDashboard'

export default function App() {
  const [view, setView] = useState<'employee' | 'knowledge' | 'operations'>('employee')

  return (
    <AppShell view={view} onChangeView={setView}>
      {view === 'employee' && <EmployeePortal />}
      {view === 'knowledge' && <KnowledgeBase />}
      {view === 'operations' && <OperationsDashboard />}
    </AppShell>
  )
}
