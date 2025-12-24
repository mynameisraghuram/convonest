// frontend/components/layout/Sidebar.tsx

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ReactNode, useState } from "react";
import {
  LayoutDashboard,
  Users,
  FolderKanban,
  MessageSquare,
  Settings,
  MessageCircle,
  CreditCard,
  ShieldCheck,
  ChevronDown,
  ChevronRight,
  Menu,
  X,
} from "lucide-react";

type NavItem = {
  label: string;
  href: string;
  icon: ReactNode;
};

type NavSection = {
  label: string;
  items: NavItem[];
  collapsible?: boolean;
};

const mainItems: NavItem[] = [
  {
    label: "Dashboard",
    href: "/dashboard",
    icon: <LayoutDashboard size={18} />,
  },
  {
    label: "Contacts",
    href: "/contacts",
    icon: <Users size={18} />,
  },
  {
    label: "Templates",
    href: "/templates",
    icon: <FolderKanban size={18} />,
  },
  {
    label: "Inbox",
    href: "/inbox",
    icon: <MessageSquare size={18} />,
  },
];

const settingsItems: NavItem[] = [
  {
    label: "WhatsApp Settings",
    href: "/settings/whatsapp",
    icon: <MessageCircle size={18} />, // WhatsApp-style
  },
  {
    label: "Billing",
    href: "/settings/billing",
    icon: <CreditCard size={18} />,
  },
  {
    label: "Roles & Access",
    href: "/settings/roles",
    icon: <ShieldCheck size={18} />,
  },
];

const navSections: NavSection[] = [
  {
    label: "Main",
    items: mainItems,
  },
  {
    label: "Settings",
    items: settingsItems,
    collapsible: true,
  },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false); // desktop mini mode
  const [mobileOpen, setMobileOpen] = useState(false); // mobile drawer
  const [settingsOpen, setSettingsOpen] = useState(true); // settings collapse
  const [activeWorkspace, setActiveWorkspace] = useState("ConvoNest HQ");

  function isActive(href: string) {
    if (pathname === href) return true;
    if (pathname.startsWith(href + "/")) return true;
    return false;
  }

  const sidebarWidth = collapsed ? "w-16" : "w-64";

  // Render a single navigation section
  const renderSection = (section: NavSection) => {
    const isSettings = section.label === "Settings";

    return (
      <div key={section.label} className="space-y-1">
        <button
          type="button"
          className="flex w-full items-center justify-between px-3 pt-4 pb-1 text-[11px] font-semibold uppercase tracking-wide text-slate-500"
          onClick={() => {
            if (isSettings && section.collapsible) {
              setSettingsOpen((prev) => !prev);
            }
          }}
        >
          <span className="flex items-center gap-1">
            {section.label === "Settings" && <Settings size={12} />}
            <span className={collapsed ? "hidden" : "inline"}>
              {section.label}
            </span>
          </span>
          {section.collapsible && !collapsed && (
            <span className="text-slate-500">
              {isSettings && settingsOpen ? (
                <ChevronDown size={14} />
              ) : (
                <ChevronRight size={14} />
              )}
            </span>
          )}
        </button>

        {/* Items */}
        <div
          className={
            section.label === "Settings" && section.collapsible && !settingsOpen
              ? "hidden"
              : "space-y-1"
          }
        >
          {section.items.map((item) => {
            const active = isActive(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition
                ${
                  active
                    ? "bg-sky-50 text-sky-700 border border-sky-100"
                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                }`}
              >
                <span
                  className={`${
                    active ? "text-sky-700" : "text-slate-500"
                  } flex items-center justify-center`}
                >
                  {item.icon}
                </span>
                {!collapsed && <span>{item.label}</span>}
              </Link>
            );
          })}
        </div>
      </div>
    );
  };

  // Desktop sidebar
  const desktopSidebar = (
    <aside
      className={`${sidebarWidth} hidden border-r border-slate-200 bg-white/90 shadow-sm lg:flex lg:flex-col transition-all duration-200`}
    >
      {/* Header with workspace switch & collapse toggle */}
      <div className="flex items-center justify-between gap-2 border-b border-slate-200 px-3 py-4">
        <div className="flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-sky-600 text-white font-semibold">
            CN
          </div>
          {!collapsed && (
            <div>
              <div className="text-sm font-semibold text-slate-900">
                ConvoNest
              </div>
              <select
                value={activeWorkspace}
                onChange={(e) => setActiveWorkspace(e.target.value)}
                className="mt-0.5 w-40 rounded border border-slate-200 bg-white px-1.5 py-0.5 text-[11px] text-slate-600 focus:outline-none"
              >
                <option>ConvoNest HQ</option>
                <option>Client – MegaLeap</option>
                <option>Client – R&R Group</option>
              </select>
            </div>
          )}
        </div>

        {/* Collapse / expand button */}
        <button
          type="button"
          onClick={() => setCollapsed((prev) => !prev)}
          className="rounded-md p-1 text-slate-500 hover:bg-slate-100 hover:text-slate-800"
        >
          {collapsed ? (
            <ChevronRight size={16} />
          ) : (
            <ChevronLeftMini />
          )}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-2 px-1 py-3">
        {navSections.map((section) => renderSection(section))}
      </nav>

      {/* Footer */}
      <div className="border-t border-slate-200 px-4 py-3 text-xs text-slate-500">
        {!collapsed && <>© {new Date().getFullYear()} ConvoNest</>}
      </div>
    </aside>
  );

  // Mobile sidebar (slide-over)
  const mobileSidebar = (
    <>
      {/* Mobile top bar with hamburger */}
      <div className="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-3 lg:hidden">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-sky-600 text-white text-sm font-semibold">
            CN
          </div>
          <div>
            <div className="text-sm font-semibold text-slate-900">
              ConvoNest
            </div>
            <div className="text-[11px] text-slate-500">
              {activeWorkspace}
            </div>
          </div>
        </div>

        <button
          type="button"
          onClick={() => setMobileOpen(true)}
          className="rounded-md p-1 text-slate-600 hover:bg-slate-100 lg:hidden"
        >
          <Menu size={20} />
        </button>
      </div>

      {/* Slide-over menu */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 bg-black/40 lg:hidden">
          <div className="fixed inset-y-0 left-0 w-64 bg-white shadow-lg flex flex-col">
            <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
              <div className="flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-sky-600 text-white text-sm font-semibold">
                  CN
                </div>
                <div>
                  <div className="text-sm font-semibold text-slate-900">
                    ConvoNest
                  </div>
                  <div className="text-[11px] text-slate-500">
                    {activeWorkspace}
                  </div>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setMobileOpen(false)}
                className="rounded-md p-1 text-slate-600 hover:bg-slate-100"
              >
                <X size={18} />
              </button>
            </div>

            <nav className="flex-1 space-y-2 px-2 py-3 overflow-y-auto">
              {navSections.map((section) => renderSection(section))}
            </nav>

            <div className="border-t border-slate-200 px-4 py-3 text-xs text-slate-500">
              © {new Date().getFullYear()} ConvoNest
            </div>
          </div>
        </div>
      )}
    </>
  );

  return (
    <>
      {/* Mobile header + slide-over */}
      {mobileSidebar}

      {/* Desktop sidebar (collapsible) */}
      {desktopSidebar}
    </>
  );
}

/**
 * Tiny helper icon for collapse (left chevron) because lucide doesn't export ChevronLeftMini
 */
function ChevronLeftMini() {
  return <ChevronDown className="-rotate-90" size={16} />;
}
