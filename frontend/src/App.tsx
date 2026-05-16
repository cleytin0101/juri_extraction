import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import { LayoutDashboard, Upload, Settings, CalendarDays } from "lucide-react";
import { Dashboard } from "./pages/Dashboard";
import { UploadPanel } from "./pages/UploadPanel";
import { Configuracoes } from "./pages/Configuracoes";
import Agenda from "./pages/Agenda";
import clsx from "clsx";

function Nav() {
  return (
    <nav className="flex gap-1 px-6 py-2 bg-surface-800 border-b border-surface-600">
      <NavLink
        to="/"
        end
        className={({ isActive }) =>
          clsx(
            "flex items-center gap-2 px-3 py-1.5 rounded text-sm transition-colors",
            isActive ? "bg-surface-700 text-white" : "text-gray-400 hover:text-white"
          )
        }
      >
        <LayoutDashboard size={15} />
        Dashboard
      </NavLink>
      <NavLink
        to="/upload"
        className={({ isActive }) =>
          clsx(
            "flex items-center gap-2 px-3 py-1.5 rounded text-sm transition-colors",
            isActive ? "bg-surface-700 text-white" : "text-gray-400 hover:text-white"
          )
        }
      >
        <Upload size={15} />
        Upload de Documentos
      </NavLink>
      <NavLink
        to="/configuracoes"
        className={({ isActive }) =>
          clsx(
            "flex items-center gap-2 px-3 py-1.5 rounded text-sm transition-colors",
            isActive ? "bg-surface-700 text-white" : "text-gray-400 hover:text-white"
          )
        }
      >
        <Settings size={15} />
        Configurações
      </NavLink>
      <NavLink
        to="/agenda"
        className={({ isActive }) =>
          clsx(
            "flex items-center gap-2 px-3 py-1.5 rounded text-sm transition-colors",
            isActive ? "bg-surface-700 text-white" : "text-gray-400 hover:text-white"
          )
        }
      >
        <CalendarDays size={15} />
        Agenda
      </NavLink>
    </nav>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Nav />
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/upload" element={<UploadPanel />} />
        <Route path="/configuracoes" element={<Configuracoes />} />
        <Route path="/agenda" element={<Agenda />} />
      </Routes>
    </BrowserRouter>
  );
}
