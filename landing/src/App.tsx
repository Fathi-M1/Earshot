import { BrowserRouter, Route, Routes } from "react-router-dom";
import { SiteFooter, SiteNav } from "@/components/chrome";
import {
  AccessibilityPage,
  FaqPage,
  HowPage,
  LicensesPage,
  NotFound,
  PrivacyPage,
  TermsPage,
} from "@/pages/docs";
import { Home } from "@/pages/home";

export function App() {
  return (
    <BrowserRouter>
      <SiteNav />
      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/how-it-works" element={<HowPage />} />
          <Route path="/privacy" element={<PrivacyPage />} />
          <Route path="/terms" element={<TermsPage />} />
          <Route path="/faq" element={<FaqPage />} />
          <Route path="/licenses" element={<LicensesPage />} />
          <Route path="/accessibility" element={<AccessibilityPage />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      <SiteFooter />
    </BrowserRouter>
  );
}
