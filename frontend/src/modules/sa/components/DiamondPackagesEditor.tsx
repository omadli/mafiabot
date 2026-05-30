/**
 * Diamond package editor — table of Stars-purchase tiers.
 *
 * The super-admin edits each row's `code`, `diamonds`, `bonus_diamonds`,
 * `stars_price`, `display_order`, and `enabled` flag. Rows can be
 * added or removed. "Save" posts the whole replacement list through
 * `superAdminApi.setDiamondPackages` — the backend treats this as the
 * source of truth, so any deleted rows disappear from the shop and
 * any new ones become available on the next pricing-cache refresh
 * (60 s).
 *
 * Mounted in both `/admin/system-settings` (JWT) and
 * `/webapp/sa/system` (initData) via the auth-aware client.
 */

import { useEffect, useMemo, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import {
  superAdminApi,
  type DiamondPackage,
} from "@shared/api/superAdmin";

interface DiamondPackagesEditorProps {
  /** Initial list from `systemSettings.diamond_packages`. */
  initial: DiamondPackage[];
}

const BLANK_PACKAGE: DiamondPackage = {
  code: "",
  diamonds: 0,
  bonus_diamonds: 0,
  stars_price: 0,
  display_order: 100,
  enabled: true,
};

function genCode(existing: DiamondPackage[]): string {
  // Suggest a stable code based on the highest existing pack_N tier so
  // SA doesn't have to invent one for every new row. Stops at the
  // first unused integer name, ignoring whatever already follows
  // `pack_`.
  const taken = new Set(existing.map((p) => p.code));
  for (let i = 1; i < 1000; i += 1) {
    const candidate = `pack_${i * 50}`;
    if (!taken.has(candidate)) return candidate;
  }
  return `pack_${Date.now()}`;
}

export function DiamondPackagesEditor({ initial }: DiamondPackagesEditorProps) {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const [rows, setRows] = useState<DiamondPackage[]>(initial);
  const [error, setError] = useState<string | null>(null);

  // Re-seed from the server payload when it lands (initial fetch) but
  // NOT every render — we want the operator to keep their unsaved
  // edits if the cache invalidates underneath them.
  useEffect(() => {
    setRows(initial);
  }, [initial]);

  const dirty = useMemo(() => {
    if (rows.length !== initial.length) return true;
    return rows.some((row, idx) => {
      const ref = initial[idx];
      return (
        row.code !== ref.code ||
        row.diamonds !== ref.diamonds ||
        row.bonus_diamonds !== ref.bonus_diamonds ||
        row.stars_price !== ref.stars_price ||
        row.display_order !== ref.display_order ||
        row.enabled !== ref.enabled
      );
    });
  }, [rows, initial]);

  const dupCodes = useMemo(() => {
    const seen = new Set<string>();
    const dups = new Set<string>();
    rows.forEach((r) => {
      const k = r.code.trim();
      if (!k) return;
      if (seen.has(k)) dups.add(k);
      seen.add(k);
    });
    return dups;
  }, [rows]);

  const blankCodes = rows.some((r) => !r.code.trim());

  const mutation = useMutation({
    mutationFn: () => superAdminApi.setDiamondPackages(rows),
    onSuccess: () => {
      setError(null);
      qc.invalidateQueries({ queryKey: ["sa-system-settings"] });
      qc.invalidateQueries({ queryKey: ["admin-system-settings"] });
    },
    onError: (e: Error) =>
      setError(e.message || t("sa.diamond_packages.save_failed", "Save failed")),
  });

  const update = (idx: number, patch: Partial<DiamondPackage>) =>
    setRows((cur) =>
      cur.map((row, i) => (i === idx ? { ...row, ...patch } : row)),
    );

  const remove = (idx: number) =>
    setRows((cur) => cur.filter((_, i) => i !== idx));

  const addRow = () =>
    setRows((cur) => [
      ...cur,
      { ...BLANK_PACKAGE, code: genCode(cur), display_order: 100 + cur.length * 10 },
    ]);

  const moveRow = (idx: number, dir: -1 | 1) => {
    const target = idx + dir;
    if (target < 0 || target >= rows.length) return;
    setRows((cur) => {
      const next = cur.slice();
      const [item] = next.splice(idx, 1);
      next.splice(target, 0, item);
      // Re-sequence display_order so the visual order matches the
      // saved order — operators sort by drag-equivalent (the move
      // buttons) and expect the row positions to "stick".
      return next.map((row, i) => ({ ...row, display_order: (i + 1) * 10 }));
    });
  };

  const canSave = dirty && !mutation.isPending && !blankCodes && dupCodes.size === 0;

  return (
    <section className="admin-card" style={{ marginBottom: "1.25rem" }}>
      <h2 className="admin-section-title">
        💎 {t("sa.diamond_packages.title", "Diamond packages")}
      </h2>
      <p style={{ color: "var(--muted)", marginTop: 0, fontSize: "0.85rem" }}>
        {t(
          "sa.diamond_packages.hint",
          "Each tier becomes a 💎 N 🎁+M — ⭐ price button in the bot's shop. Save to apply.",
        )}
      </p>

      <table className="admin-table">
        <thead>
          <tr>
            <th style={{ width: 32 }}>#</th>
            <th>{t("sa.diamond_packages.col_code", "Code")}</th>
            <th style={{ textAlign: "right" }}>
              💎 {t("sa.diamond_packages.col_base", "Base")}
            </th>
            <th style={{ textAlign: "right" }}>
              🎁 {t("sa.diamond_packages.col_bonus", "Bonus")}
            </th>
            <th style={{ textAlign: "right" }}>
              ⭐ {t("sa.diamond_packages.col_stars", "Stars")}
            </th>
            <th style={{ textAlign: "right" }}>
              {t("sa.diamond_packages.col_total", "Total 💎")}
            </th>
            <th style={{ textAlign: "center" }}>
              {t("sa.diamond_packages.col_enabled", "Enabled")}
            </th>
            <th style={{ width: 110 }} />
          </tr>
        </thead>
        <tbody>
          {rows.map((row, idx) => {
            const total = row.diamonds + row.bonus_diamonds;
            const dup = dupCodes.has(row.code.trim());
            return (
              <tr key={`${idx}`}>
                <td style={{ color: "var(--muted)" }}>{idx + 1}</td>
                <td>
                  <input
                    className="admin-input"
                    value={row.code}
                    onChange={(e) => update(idx, { code: e.target.value })}
                    placeholder="pack_500"
                    style={{
                      width: 130,
                      borderColor: dup || !row.code.trim() ? "#c0392b" : undefined,
                    }}
                  />
                </td>
                <td style={{ textAlign: "right" }}>
                  <input
                    type="number"
                    className="admin-input"
                    value={row.diamonds}
                    min={0}
                    onChange={(e) =>
                      update(idx, { diamonds: parseInt(e.target.value || "0") || 0 })
                    }
                    style={{ width: 80, textAlign: "right" }}
                  />
                </td>
                <td style={{ textAlign: "right" }}>
                  <input
                    type="number"
                    className="admin-input"
                    value={row.bonus_diamonds}
                    min={0}
                    onChange={(e) =>
                      update(idx, {
                        bonus_diamonds: parseInt(e.target.value || "0") || 0,
                      })
                    }
                    style={{ width: 80, textAlign: "right" }}
                  />
                </td>
                <td style={{ textAlign: "right" }}>
                  <input
                    type="number"
                    className="admin-input"
                    value={row.stars_price}
                    min={1}
                    onChange={(e) =>
                      update(idx, {
                        stars_price: parseInt(e.target.value || "0") || 0,
                      })
                    }
                    style={{ width: 80, textAlign: "right" }}
                  />
                </td>
                <td style={{ textAlign: "right", color: "var(--muted)" }}>
                  <strong>{total}</strong>
                </td>
                <td style={{ textAlign: "center" }}>
                  <input
                    type="checkbox"
                    checked={row.enabled}
                    onChange={(e) => update(idx, { enabled: e.target.checked })}
                  />
                </td>
                <td style={{ display: "flex", gap: 4, justifyContent: "flex-end" }}>
                  <button
                    type="button"
                    className="admin-btn"
                    onClick={() => moveRow(idx, -1)}
                    disabled={idx === 0}
                    title={t("sa.diamond_packages.move_up", "Move up")}
                    style={{ padding: "2px 8px" }}
                  >
                    ↑
                  </button>
                  <button
                    type="button"
                    className="admin-btn"
                    onClick={() => moveRow(idx, +1)}
                    disabled={idx === rows.length - 1}
                    title={t("sa.diamond_packages.move_down", "Move down")}
                    style={{ padding: "2px 8px" }}
                  >
                    ↓
                  </button>
                  <button
                    type="button"
                    className="admin-btn admin-btn-danger"
                    onClick={() => remove(idx)}
                    title={t("sa.diamond_packages.remove", "Remove")}
                    style={{ padding: "2px 8px" }}
                  >
                    🗑
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      <div
        style={{
          display: "flex",
          gap: "0.5rem",
          marginTop: "0.75rem",
          alignItems: "center",
          flexWrap: "wrap",
        }}
      >
        <button type="button" className="admin-btn" onClick={addRow}>
          ➕ {t("sa.diamond_packages.add_row", "Add tier")}
        </button>
        <button
          type="button"
          className="admin-btn primary"
          onClick={() => mutation.mutate()}
          disabled={!canSave}
        >
          {mutation.isPending
            ? "⏳ " + t("sa.diamond_packages.saving", "Saving…")
            : "💾 " + t("sa.diamond_packages.save_all", "Save all")}
        </button>
        {dirty && (
          <span style={{ color: "var(--muted)", fontSize: "0.85rem" }}>
            {t("sa.diamond_packages.unsaved", "Unsaved changes")}
          </span>
        )}
        {dupCodes.size > 0 && (
          <span style={{ color: "#e74c3c", fontSize: "0.85rem" }}>
            ⚠️ {t("sa.diamond_packages.duplicate_codes", "Duplicate codes")}:{" "}
            <code>{Array.from(dupCodes).join(", ")}</code>
          </span>
        )}
        {blankCodes && (
          <span style={{ color: "#e74c3c", fontSize: "0.85rem" }}>
            ⚠️ {t("sa.diamond_packages.blank_codes", "Empty code field")}
          </span>
        )}
        {error && (
          <span style={{ color: "#e74c3c", fontSize: "0.85rem" }}>⚠️ {error}</span>
        )}
      </div>
    </section>
  );
}
