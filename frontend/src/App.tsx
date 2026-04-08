import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import { LayoutDashboard, Download, Settings } from "lucide-react";
import { Dashboard } from "./pages/Dashboard";
import { ExtractionPanel } from "./pages/ExtractionPanel";
import { Configuracoes } from "./pages/Configuracoes";
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
        to="/extrair"
        className={({ isActive }) =>
          clsx(
            "flex items-center gap-2 px-3 py-1.5 rounded text-sm transition-colors",
            isActive ? "bg-surface-700 text-white" : "text-gray-400 hover:text-white"
          )
        }
      >
        <Download size={15} />
        Extrair Pauta
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
    </nav>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Nav />
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/extrair" element={<ExtractionPanel />} />
        <Route path="/configuracoes" element={<Configuracoes />} />
      </Routes>
    </BrowserRouter>
  );
}
