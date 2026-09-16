import { useEffect, useRef, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type Suggestion = { value: string; subtitle?: string | null };

type Props = {
  label: string;
  placeholder?: string;
  value: string;
  onChange: (value: string) => void;
  endpoint: string; // e.g. "/api/companies/autocomplete"
  emptyHint?: string; // shown when no suggestions match, e.g. "Not listed? Just type it in."
};

// Debounced type-ahead field. Always usable as plain free text underneath -
// suggestions are a UX aid, never a gate. See docs/professional-profile-design.md.
export default function AutocompleteField({
  label,
  placeholder,
  value,
  onChange,
  endpoint,
  emptyHint = "Not listed? What you've typed will be saved as-is.",
}: Props) {
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  function handleChange(next: string) {
    onChange(next);
    if (debounceRef.current) clearTimeout(debounceRef.current);

    if (next.trim().length < 2) {
      setSuggestions([]);
      setOpen(false);
      return;
    }

    debounceRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await fetch(`${API_URL}${endpoint}?q=${encodeURIComponent(next)}`, {
          credentials: "include",
        });
        if (res.ok) {
          const data: Suggestion[] = await res.json();
          setSuggestions(data);
          setOpen(true);
        }
      } catch {
        // Fail open - suggestions just don't appear, field stays usable as free text.
        setSuggestions([]);
      } finally {
        setLoading(false);
      }
    }, 250);
  }

  return (
    <div className="field" ref={containerRef}>
      <label className="field-label">{label}</label>
      <input
        className="field-input"
        type="text"
        placeholder={placeholder}
        value={value}
        onChange={(e) => handleChange(e.target.value)}
        onFocus={() => suggestions.length > 0 && setOpen(true)}
        autoComplete="off"
      />
      {open && (
        <div className="suggestions">
          {loading && <div className="suggestion-hint">Searching…</div>}
          {!loading && suggestions.length === 0 && (
            <div className="suggestion-hint">{emptyHint}</div>
          )}
          {!loading &&
            suggestions.map((s) => (
              <button
                key={s.value}
                type="button"
                className="suggestion"
                onClick={() => {
                  onChange(s.value);
                  setOpen(false);
                }}
              >
                <span>{s.value}</span>
                {s.subtitle && <span className="suggestion-subtitle">{s.subtitle}</span>}
              </button>
            ))}
        </div>
      )}
    </div>
  );
}
