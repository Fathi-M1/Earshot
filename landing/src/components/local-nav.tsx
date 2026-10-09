import logo from "../../../design/logo.svg";
import lockup from "../../../design/lockup-light.svg";
import { brand, githubUrl } from "@/lib/brand";
import { Button } from "@/components/ui/button";

const links = [
  { href: "#overview", label: "Overview" },
  { href: "#problem", label: "Problem" },
  { href: "#how", label: "How" },
  { href: "#privacy", label: "Privacy" },
];

export function LocalNav() {
  return (
    <header className="local-nav">
      <a className="skip" href="#overview">
        Skip to content
      </a>
      <div className="nav-inner">
        <a className="nav-brand" href="#overview">
          <img src={logo} alt="" width={20} height={32} />
          <span>{brand.displayName}</span>
        </a>
        <nav className="nav-links" aria-label="Page">
          {links.map((link) => (
            <a key={link.href} href={link.href}>
              {link.label}
            </a>
          ))}
        </nav>
        <Button asChild size="sm">
          <a href={githubUrl} rel="noreferrer">
            GitHub
          </a>
        </Button>
      </div>
    </header>
  );
}

export function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="wrap wrap-text footer-inner">
        <img src={lockup} alt={brand.displayName} width={168} height={47} />
        <p>
          The watch shows the title. It does not vibrate. Host Grotesk and Fragment Mono are
          used under the SIL Open Font License 1.1.
        </p>
      </div>
    </footer>
  );
}
