type Props = {
  visibleOnProfile: boolean;
  usableForMatching: boolean;
  onChangeVisible: (v: boolean) => void;
  onChangeMatching: (v: boolean) => void;
};

// Every professional-profile field carries these two independent flags -
// see docs/professional-profile-design.md. Defaults (visible: false,
// matching: true) match the backend model's defaults.
export default function PrivacyToggles({
  visibleOnProfile,
  usableForMatching,
  onChangeVisible,
  onChangeMatching,
}: Props) {
  return (
    <div className="privacy-row">
      <label className="privacy-toggle">
        <input
          type="checkbox"
          checked={visibleOnProfile}
          onChange={(e) => onChangeVisible(e.target.checked)}
        />
        Show on profile
      </label>
      <label className="privacy-toggle">
        <input
          type="checkbox"
          checked={usableForMatching}
          onChange={(e) => onChangeMatching(e.target.checked)}
        />
        Use for matching
      </label>
    </div>
  );
}
