import { Nav } from "@/components/nav";
import { Hero } from "@/components/hero";
import { ContextEngine } from "@/components/context-engine";
import { Delegation } from "@/components/delegation";
import { Deployment } from "@/components/deployment";
import { CTAFooter } from "@/components/cta-footer";

export default function DemoPage() {
  return (
    <>
      <Nav />
      <Hero />
      <ContextEngine />
      <Delegation />
      <Deployment />
      <CTAFooter />
    </>
  );
}
