/**
 * Colored badge for a platform (Blinkit, Zepto, etc.)
 */
export default function PlatformBadge({ platform, size = "sm" }) {
  const padding = size === "sm" ? "px-2 py-0.5 text-xs" : "px-3 py-1 text-sm";

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full font-medium ${padding}`}
      style={{
        backgroundColor: platform.platform_color + "20",
        color: platform.platform_color,
        border: `1px solid ${platform.platform_color}40`,
      }}
    >
      <span>{platform.platform_logo}</span>
      <span>{platform.platform_display}</span>
    </span>
  );
}
