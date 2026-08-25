import { useRef, useState } from "react";
import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

type FileDropProps = {
  accept: string;
  label: string;
  hint: string;
  icon: LucideIcon;
  fileName: string;
  previewUrl?: string | null;
  onFile: (file: File) => void;
};

export function FileDrop({
  accept,
  label,
  hint,
  icon: Icon,
  fileName,
  previewUrl,
  onFile,
}: FileDropProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [over, setOver] = useState(false);

  function take(file: File | undefined) {
    if (file) onFile(file);
  }

  return (
    <button
      type="button"
      onClick={() => inputRef.current?.click()}
      onDragOver={(e) => {
        e.preventDefault();
        setOver(true);
      }}
      onDragLeave={() => setOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setOver(false);
        take(e.dataTransfer.files[0]);
      }}
      className={cn(
        "flex w-full items-center gap-3 rounded-lg border bg-muted/60 p-3 text-left transition-[border-color,background-color] duration-150",
        over ? "border-ring bg-muted" : "border-border hover:border-ring/50",
      )}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="sr-only"
        onChange={(e) => {
          take(e.target.files?.[0]);
          e.target.value = "";
        }}
      />
      {previewUrl ? (
        <img
          src={previewUrl}
          alt=""
          className="size-12 shrink-0 rounded-md object-cover"
        />
      ) : (
        <span className="flex size-12 shrink-0 items-center justify-center rounded-md bg-secondary text-muted-foreground">
          <Icon className="size-5" />
        </span>
      )}
      <span className="min-w-0 flex-1">
        <span className="block text-xs font-medium tracking-wide text-muted-foreground uppercase">
          {label}
        </span>
        <span className="mt-0.5 block truncate text-sm text-foreground">{fileName}</span>
        <span className="mt-0.5 block text-xs text-muted-foreground">{hint}</span>
      </span>
    </button>
  );
}
