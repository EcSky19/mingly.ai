type ChipItem = { id: string; label: string; sublabel?: string };

type Props = {
  items: ChipItem[];
  selectedIds: string[]; // "liked" - selected but not loved
  lovedIds: string[]; // "loved" - the stronger signal (maps to is_top_pick server-side)
  maxLoved?: number;
  onCycle: (id: string) => void;
};

// Single click cycles each chip through three states, giving a real
// intensity signal instead of a flat "selected or not":
//   unselected -> liked -> loved -> unselected
// "Loved" is capped at maxLoved and maps to the existing is_top_pick
// flag server-side - no schema change needed, just a richer UI on top
// of data we already had.
export default function ChipSelect({ items, selectedIds, lovedIds, maxLoved, onCycle }: Props) {
  return (
    <div className="chip-grid">
      {items.map((item) => {
        const isLoved = lovedIds.includes(item.id);
        const isLiked = !isLoved && selectedIds.includes(item.id);
        const lovedFull = maxLoved !== undefined && lovedIds.length >= maxLoved;

        let className = "chip";
        if (isLoved) className = "chip chip-loved";
        else if (isLiked) className = "chip chip-liked";

        // If loved is full, clicking a liked (not-yet-loved) chip should
        // still be able to cycle to unselected - just can't advance to
        // loved. onCycle handles that branching based on current state.
        return (
          <button
            key={item.id}
            type="button"
            className={className}
            onClick={() => onCycle(item.id)}
            title={
              isLoved
                ? "Loved - click to clear"
                : isLiked
                ? lovedFull
                  ? `Liked - up to ${maxLoved} loved already picked`
                  : "Liked - click to love"
                : "Click to like"
            }
          >
            <span>{item.label}</span>
            {isLoved && <span className="chip-heart">♥</span>}
            {isLiked && <span className="chip-check">✓</span>}
          </button>
        );
      })}
    </div>
  );
}
