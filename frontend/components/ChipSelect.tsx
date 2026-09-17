type ChipItem = { id: string; label: string; sublabel?: string };

type Props = {
  items: ChipItem[];
  selectedIds: string[];
  topPickIds?: string[];
  maxTopPicks?: number;
  onToggleSelect: (id: string) => void;
  onToggleTopPick?: (id: string) => void;
};

// Generic multi-select chip UI for catalog items (interests, activities).
// Selecting a chip toggles it in/out; a star toggles "top pick" status
// for already-selected items, up to maxTopPicks.
export default function ChipSelect({
  items,
  selectedIds,
  topPickIds = [],
  maxTopPicks,
  onToggleSelect,
  onToggleTopPick,
}: Props) {
  return (
    <div className="chip-grid">
      {items.map((item) => {
        const isSelected = selectedIds.includes(item.id);
        const isTopPick = topPickIds.includes(item.id);
        const topPicksFull = maxTopPicks !== undefined && topPickIds.length >= maxTopPicks;

        return (
          <button
            key={item.id}
            type="button"
            className={isSelected ? "chip chip-selected" : "chip"}
            onClick={() => onToggleSelect(item.id)}
          >
            <span>{item.label}</span>
            {isSelected && onToggleTopPick && (
              <span
                className={isTopPick ? "chip-star chip-star-active" : "chip-star"}
                onClick={(e) => {
                  e.stopPropagation();
                  if (!isTopPick && topPicksFull) return;
                  onToggleTopPick(item.id);
                }}
                title={isTopPick ? "Remove from top picks" : "Mark as a top pick"}
              >
                ★
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
