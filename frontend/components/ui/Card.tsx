import { cn } from "@/lib/format";

export function Card({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-white/5 bg-surface-900/80 p-5 sm:p-6",
        className
      )}
    >
      {children}
    </div>
  );
}

export function CardTitle({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <h2 className={cn("text-sm font-medium text-slate-400 mb-3", className)}>
      {children}
    </h2>
  );
}
