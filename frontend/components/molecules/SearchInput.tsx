import { Search, X } from "lucide-react";
import { IconButton } from "@/components/atoms";

interface SearchInputProps {
  value: string;
  onChange: (value: string) => void;
  onClear: () => void;
  placeholder?: string;
  clearLabel?: string;
}

export function SearchInput({
  value,
  onChange,
  onClear,
  placeholder = "Search LLM news…",
  clearLabel = "Clear search",
}: SearchInputProps) {
  return (
    <div className="flex items-center gap-2 rounded-xl border border-zinc-800 bg-zinc-900/60 px-3 py-2 backdrop-blur-sm transition-colors focus-within:border-zinc-600">
      <Search size={16} className="shrink-0 text-zinc-500" />
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full bg-transparent text-sm text-zinc-200 outline-none placeholder:text-zinc-600"
      />
      {value && (
        <IconButton label={clearLabel} onClick={onClear}>
          <X size={14} />
        </IconButton>
      )}
    </div>
  );
}
