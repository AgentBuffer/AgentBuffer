import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { KeybindShell } from "@/components/keybinds/keybind-shell";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <KeybindShell>
      <div className="flex h-screen">
        <Sidebar />
        <div className="flex-1 flex flex-col overflow-hidden">
          <Header />
          <main className="flex-1 overflow-y-auto bg-slate-50 p-6">
            {children}
          </main>
        </div>
      </div>
    </KeybindShell>
  );
}
