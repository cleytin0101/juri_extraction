import { EventManager } from "@/components/ui/event-manager"

export default function Agenda() {
  return (
    <div className="min-h-screen bg-surface-900 p-6">
      <EventManager defaultView="month" className="max-w-7xl mx-auto" />
    </div>
  )
}
