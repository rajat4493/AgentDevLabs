"use client";

import { PROVIDER_STYLES, ProviderKey } from "@/lib/providerStyles";

type Props = {
  provider: string;
  model?: string;
  showModel?: boolean;
};

export function ProviderBadge({ provider, model, showModel = false }: Props) {
  const key = provider.toLowerCase() as ProviderKey;
  const style =
    PROVIDER_STYLES[key] ?? {
      label: provider,
      badgeClass:
        "inline-flex items-center rounded-full border border-zinc-500/40 bg-zinc-500/10 px-2 py-0.5 text-[11px] font-medium text-zinc-200",
    };

  return (
    <span className={style.badgeClass}>
      <span className="mr-1 h-1.5 w-1.5 rounded-full bg-current" />
      {style.label}
      {showModel && model && (
        <span className="ml-1 text-[10px] text-zinc-300/80">· {model}</span>
      )}
    </span>
  );
}

