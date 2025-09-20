"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Newspaper,
  BrainCircuit,
  TrendingUp,
  Settings,
} from "lucide-react";

const navItems = [
  { href: "/analysis", label: "Analysis", icon: LayoutDashboard },
  { href: "/advanced", label: "Advanced Analytics", icon: TrendingUp },
  { href: "/news", label: "News", icon: Newspaper },
  { href: "/automation", label: "Automation", icon: Settings },
  { href: "/prediction", label: "Prediction", icon: BrainCircuit },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 h-screen bg-white border-r fixed top-0 left-0">
      <div className="p-6">
        <h2 className="text-xl font-bold">Dashboard Menu</h2>
      </div>
      <nav className="px-4">
        <ul>
          {navItems.map((item) => (
            <li key={item.label}>
              <Link
                href={item.href}
                className={cn(
                  "flex items-center p-3 my-1 rounded-lg text-slate-700 hover:bg-slate-100 transition-colors",
                  pathname === item.href && "bg-slate-200 font-semibold"
                )}
              >
                <item.icon className="w-5 h-5 mr-3" />
                {item.label}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  );
}
