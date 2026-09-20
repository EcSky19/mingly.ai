type ChipOption = { value: string; label: string };

type Props = {
  options: ChipOption[];
  selectedValues: string[];
  onToggle: (value: string) => void;
};

// Simple binary multi-select (selected/not), unlike ChipSelect's
// three-state like/love cycle - used for fixed, small vocabularies
// (career qualities, social environment, social goals) where there's
// no meaningful "intensity" distinction to capture.
export default function MultiSelectChips({ options, selectedValues, onToggle }: Props) {
  return (
    <div className="chip-grid">
      {options.map((opt) => {
        const isSelected = selectedValues.includes(opt.value);
        return (
          <button
            key={opt.value}
            type="button"
            className={isSelected ? "chip chip-liked" : "chip"}
            onClick={() => onToggle(opt.value)}
          >
            <span>{opt.label}</span>
            {isSelected && <span className="chip-check">✓</span>}
          </button>
        );
      })}
    </div>
  );
}
