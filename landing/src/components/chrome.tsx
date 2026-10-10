import { NavLink } from "react-router-dom";
import { useEffect, useState } from "react";
import logo from "../../../design/logo.svg";
import { brand, githubUrl } from "@/lib/brand";

const links = [
  { to: "/how-it-works", label: "How it works" },
  { to: "/privacy", label: "Privacy" },
  { to: "/faq", label: "FAQ" },
];

export function SiteNav() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const root = document.documentElement;
    root.style.overflow = open ? "hidden" : "";
    return () => {
      root.style.overflow = "";
    };
  }, [open]);

  return (
    <>
      <header className="nav">
        <div className="nav-inner">
          <NavLink className="brand" to="/" onClick={() => setOpen(false)}>
            <img src={logo} alt="" width={20} height={32} />
            <span>{brand.displayName}</span>
          </NavLink>
          <nav className="nav-links" aria-label="Pages">
            {links.map((link) => (
              <NavLink key={link.to} to={link.to}>
                {link.label}
              </NavLink>
            ))}
            <a href={githubUrl} rel="noreferrer">
              GitHub ↗
            </a>
          </nav>
          <NavLink className="pill nav-pill" to="/#get" onClick={() => setOpen(false)}>
            Get {brand.displayName}
          </NavLink>
          <button
            type="button"
            className="menu-button"
            aria-expanded={open}
            aria-label={open ? "Close menu" : "Open menu"}
            onClick={() => setOpen((value) => !value)}
          >
            {open ? <span className="menu-x">×</span> : (<><i /><i /></>)}
          </button>
        </div>
      </header>
      {open ? (
        <div className="sheet" role="dialog" aria-label="Menu">
          {links.map((link) => (
            <NavLink key={link.to} to={link.to} onClick={() => setOpen(false)}>
              {link.label}
            </NavLink>
          ))}
          <a href={githubUrl} rel="noreferrer" onClick={() => setOpen(false)}>
            GitHub ↗
          </a>
        </div>
      ) : null}
    </>
  );
}

export function SiteFooter() {
  return (
    <footer className="footer">
      <div className="footer-grid">
        <div>
          <NavLink className="brand" to="/">
            <img src={logo} alt="" width={24} height={38} />
            <span>{brand.displayName}</span>
          </NavLink>
          <p>Every word, within earshot.</p>
          <p className="mono">Made in Manila for AppBuilders PH 2026</p>
        </div>
        <div>
          <p className="mono col-label">Product</p>
          <NavLink to="/how-it-works">How it works</NavLink>
          <NavLink to="/#features">Features</NavLink>
        </div>
        <div>
          <p className="mono col-label">Resources</p>
          <NavLink to="/faq">FAQ</NavLink>
          <a href={githubUrl} rel="noreferrer">
            GitHub ↗
          </a>
          <NavLink to="/licenses">Licenses</NavLink>
        </div>
        <div>
          <p className="mono col-label">Legal</p>
          <NavLink to="/privacy">Privacy</NavLink>
          <NavLink to="/terms">Terms</NavLink>
          <NavLink to="/accessibility">Accessibility</NavLink>
        </div>
      </div>
      <div className="footer-bar">
        <p>© 2026 {brand.displayName} · Team Skip Intro</p>
        <p className="mono">Runs offline. 0 bytes sent.</p>
      </div>
    </footer>
  );
}
