export function TierBadge({ tier, label }: { tier: string; label?: string }) {
  const styles: Record<string, string> = {
    GREEN: 'tier-green',
    AMBER: 'tier-amber',
    RED: 'tier-red',
    BLACK: 'tier-black',
  };
  return (
    <span className={`px-3 py-1 rounded-full text-sm font-bold ${styles[tier] || 'bg-gray-700 text-gray-300'}`}>
      {tier}{label ? ` · ${label}` : ''}
    </span>
  );
}
