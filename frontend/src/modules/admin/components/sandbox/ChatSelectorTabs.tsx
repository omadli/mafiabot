/**
 * Tab strip above the group-chat panel.
 *
 * In the MVP backend the bot only emits to one "group" scope; the
 * Mafia/Dead tabs sit inactive until those scopes ship — kept here
 * so the layout doesn't shift later.
 */

import { useTranslation } from "react-i18next";

import type { TranscriptScope } from "@shared/api/sandbox";

export type ChatTab = TranscriptScope;

interface ChatSelectorTabsProps {
  active: ChatTab;
  onChange: (tab: ChatTab) => void;
  counts: Record<ChatTab, number>;
}

const TABS: Array<{ value: ChatTab; emoji: string; i18nKey: string }> = [
  { value: "group", emoji: "🟢", i18nKey: "admin.sandbox.tabs.group" },
  { value: "mafia_chat", emoji: "🤵", i18nKey: "admin.sandbox.tabs.mafia" },
  { value: "dead_chat", emoji: "💀", i18nKey: "admin.sandbox.tabs.dead" },
  { value: "dm", emoji: "📩", i18nKey: "admin.sandbox.tabs.all_dms" },
];

export function ChatSelectorTabs({ active, onChange, counts }: ChatSelectorTabsProps) {
  const { t } = useTranslation();
  return (
    <div className="sb-tabs">
      {TABS.map((tab) => {
        const count = counts[tab.value] || 0;
        const isActive = active === tab.value;
        return (
          <button
            key={tab.value}
            type="button"
            onClick={() => onChange(tab.value)}
            disabled={count === 0 && !isActive}
            className={`sb-tab ${isActive ? "active" : ""}`}
          >
            {tab.emoji} {t(tab.i18nKey)}
            {count > 0 && <span className="sb-tab-count">{count}</span>}
          </button>
        );
      })}
    </div>
  );
}
