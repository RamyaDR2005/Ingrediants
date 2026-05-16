import React from "react";
import { Link, useLocation } from "wouter";
import { ScanSearch, Database, History, LayoutDashboard } from "lucide-react";
import { cn } from "@/lib/utils";

export function Layout({ children }: { children: React.ReactNode }) {
  const [location] = useLocation();

  const navItems = [
    { href: "/", label: "Scanner", icon: ScanSearch },
    { href: "/results", label: "Results", icon: ScanSearch, hidden: true },
    { href: "/database", label: "Database", icon: Database },
    { href: "/history", label: "History", icon: History },
    { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  ];

  return (
    <div className="flex h-screen w-full bg-background overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 flex-shrink-0 border-r border-border bg-card flex flex-col hidden md:flex">
        <div className="p-6 border-b border-border flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center text-primary-foreground shadow-sm">
            <ScanSearch size={18} strokeWidth={2.5} />
          </div>
          <span className="font-bold text-lg tracking-tight">SafeScan</span>
        </div>
        <nav className="flex-1 overflow-y-auto p-4 space-y-1.5">
          {navItems.filter(i => !i.hidden).map((item) => {
            const isActive = location === item.href || (item.href !== "/" && location.startsWith(item.href));
            return (
              <Link 
                key={item.href} 
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors",
                  isActive 
                    ? "bg-primary/10 text-primary" 
                    : "text-muted-foreground hover:bg-secondary hover:text-foreground"
                )}
              >
                <item.icon size={18} />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Mobile Header */}
        <header className="md:hidden h-14 border-b border-border bg-card flex items-center px-4 gap-3">
          <div className="w-7 h-7 rounded-md bg-primary flex items-center justify-center text-primary-foreground shadow-sm">
            <ScanSearch size={16} strokeWidth={2.5} />
          </div>
          <span className="font-bold text-lg tracking-tight">SafeScan</span>
        </header>

        {/* Page Content */}
        <div className="flex-1 overflow-y-auto p-4 md:p-8">
          <div className="max-w-5xl mx-auto h-full">
            {children}
          </div>
        </div>

        {/* Mobile Nav */}
        <nav className="md:hidden h-16 border-t border-border bg-card flex items-center justify-around px-2 pb-safe">
          {navItems.filter(i => !i.hidden).map((item) => {
            const isActive = location === item.href || (item.href !== "/" && location.startsWith(item.href));
            return (
              <Link 
                key={item.href} 
                href={item.href}
                className={cn(
                  "flex flex-col items-center justify-center w-16 h-full gap-1 text-[10px] font-medium transition-colors",
                  isActive ? "text-primary" : "text-muted-foreground"
                )}
              >
                <item.icon size={20} className={cn(isActive && "fill-primary/20")} />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </main>
    </div>
  );
}
