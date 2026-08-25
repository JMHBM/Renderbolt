import { cn } from "@/lib/utils";

export function BoltMark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 32 32"
      className={cn("size-8", className)}
      aria-hidden="true"
    >
      <rect width="32" height="32" rx="7" fill="currentColor" className="text-foreground" />
      <path
        fill="currentColor"
        className="text-background"
        d="M19.5 3.5 8.2 15.6h6.4L10.4 28.8l13.6-13.3h-6.8L19.5 3.5z"
      />
    </svg>
  );
}

export function Wordmark({ className }: { className?: string }) {
  return (
    <div className={cn("flex items-center gap-2.5", className)}>
      <BoltMark />
      <span className="font-display text-xl tracking-[0.14em] text-foreground">
        RENDERBOLT
      </span>
    </div>
  );
}
