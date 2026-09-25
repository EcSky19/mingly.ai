import { useState, ReactNode } from "react";

type Props = {
  title: string;
  defaultOpen?: boolean;
  summary?: string; // shown collapsed, e.g. "3 added" - lets someone
  // scan the page without opening every section
  children: ReactNode;
};

// The real fix for "too much scrolling": rather than every section
// permanently expanded, sections collapse to just a title + one-line
// summary and open on tap. This is how native mobile apps handle long
// profile/settings screens, and the plan is a phone app sharing this
// same look - so the pattern needs to work well at phone width, not
// just look fine on desktop.
export default function CollapsibleSection({ title, defaultOpen = false, summary, children }: Props) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <section className="section collapsible-section">
      <button
        type="button"
        className="collapsible-header"
        onClick={() => setOpen((prev) => !prev)}
        aria-expanded={open}
      >
        <h2 className="section-title">{title}</h2>
        <span className="collapsible-header-right">
          {!open && summary && <span className="collapsible-summary">{summary}</span>}
          <span className={open ? "collapsible-chevron collapsible-chevron-open" : "collapsible-chevron"}>
            ▾
          </span>
        </span>
      </button>
      {open && <div className="collapsible-body">{children}</div>}
    </section>
  );
}
