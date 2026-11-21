"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const links = [
  { href: "/", label: "Проверка и подача" },
  { href: "/applications", label: "Мои заявки" },
  { href: "/archive", label: "Архив" },
];

export function SiteNav() {
  const path = usePathname();
  return (
    <nav className="flex gap-1 border-b bg-card px-4">
      {links.map((l) => (
        <Link
          key={l.href}
          href={l.href}
          className={cn(
            "border-b-2 border-transparent px-4 py-3 text-sm text-muted-foreground hover:text-foreground",
            path === l.href && "border-primary font-semibold text-primary"
          )}
        >
          {l.label}
        </Link>
      ))}
    </nav>
  );
}
