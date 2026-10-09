import { Close } from "@/components/close";
import { Bento } from "@/components/bento";
import { Hero } from "@/components/hero";
import { How } from "@/components/how";
import { LocalNav, SiteFooter } from "@/components/local-nav";
import { Privacy } from "@/components/privacy";
import { Problem } from "@/components/problem";

export function App() {
  return (
    <>
      <LocalNav />
      <main>
        <Hero />
        <Problem />
        <How />
        <Bento />
        <Privacy />
        <Close />
      </main>
      <SiteFooter />
    </>
  );
}
