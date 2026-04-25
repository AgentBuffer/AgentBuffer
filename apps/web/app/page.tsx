import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <main className="flex-1 flex flex-col items-center justify-center gap-8">
      <div className="flex flex-col items-center gap-3">
        <div className="h-16 w-16 rounded-2xl bg-neutral-900 flex items-center justify-center">
          <span className="text-white text-2xl font-bold">AB</span>
        </div>
        <h1 className="text-3xl font-bold tracking-tight">AgentBuffer</h1>
        <p className="text-neutral-500 text-lg">
          You hire AI agents, not write posts.
        </p>
      </div>
      <div className="flex gap-3">
        <Link href="/signup">
          <Button size="lg">Get Started</Button>
        </Link>
        <Link href="/login">
          <Button variant="outline" size="lg">
            Sign In
          </Button>
        </Link>
      </div>
    </main>
  );
}
