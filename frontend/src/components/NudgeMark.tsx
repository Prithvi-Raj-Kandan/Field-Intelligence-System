interface NudgeMarkProps {
  size?: number;
  /** Slash color — white on orange mark boxes, brand brown on light backgrounds */
  color?: string;
  className?: string;
}

/** The/Nudge Institute diagonal slash mark */
export function NudgeMark({
  size = 20,
  color = "#ffffff",
  className = "",
}: NudgeMarkProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden
    >
      <rect
        x="10.25"
        y="2.5"
        width="4.5"
        height="19"
        rx="0.6"
        fill={color}
        transform="rotate(24 12 12)"
      />
    </svg>
  );
}
