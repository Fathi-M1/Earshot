import { useEffect } from "react";
import { brand } from "@/lib/brand";

export function PageMeta({ title, description }: { title: string; description: string }) {
  useEffect(() => {
    document.title = title === brand.displayName ? title : `${title} · ${brand.displayName}`;
    document.querySelector('meta[name="description"]')?.setAttribute("content", description);
  }, [title, description]);
  return null;
}
