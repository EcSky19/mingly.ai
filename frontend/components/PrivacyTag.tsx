type Props = {
  visible: boolean;
};

// Shown next to a field on the Profile page when it's NOT visible on
// the public profile (matching-only). Nothing renders when visible is
// true - being shown publicly is the unmarked default state, the
// exception (private/matching-only) is what's worth calling out.
export default function PrivacyTag({ visible }: Props) {
  if (visible) return null;
  return <span className="privacy-tag">🔒 Matching only</span>;
}
