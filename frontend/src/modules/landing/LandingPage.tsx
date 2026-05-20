import { useMemo } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { api } from "@shared/api/client";
import type { Locale } from "@shared/i18n";

import "./LandingPage.css";

const BOT_URL = "https://t.me/MafGameUzBot";
const ADD_TO_GROUP_URL = `${BOT_URL}?startgroup=true`;
const NEWS_URL = "https://t.me/Mafiauzbot_news";
const EMOJI_PACK_URL = "https://t.me/addemoji/mafia_uz_by_MafGameuzbot";

interface PublicRole {
  role: string;
  team: "civilians" | "mafia" | "singletons";
  name_uz: string;
  name_ru: string;
  name_en: string;
  static_emoji: string;
  custom_emoji_id: string;
}

const TEAM_META: Record<
  PublicRole["team"],
  { emoji: string; key: string; tone: string }
> = {
  civilians: { emoji: "👨‍👨‍👧‍👦", key: "landing.team_civilians", tone: "team-civilians" },
  mafia:     { emoji: "🤵🏼",   key: "landing.team_mafia",     tone: "team-mafia" },
  singletons:{ emoji: "🎯",    key: "landing.team_singletons", tone: "team-singletons" },
};

const TEAM_ORDER: PublicRole["team"][] = ["civilians", "mafia", "singletons"];

export function LandingPage() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language as Locale) || "uz";

  const { data } = useQuery({
    queryKey: ["public-role-configs"],
    queryFn: async () => (await api.get<{ items: PublicRole[] }>("/public/role-configs")).data,
    staleTime: 5 * 60_000,
  });

  const rolesByTeam = useMemo(() => {
    const out: Record<PublicRole["team"], PublicRole[]> = {
      civilians: [], mafia: [], singletons: [],
    };
    (data?.items ?? []).forEach((r) => out[r.team]?.push(r));
    return out;
  }, [data]);

  const nameOf = (r: PublicRole): string =>
    (lang === "ru" ? r.name_ru : lang === "en" ? r.name_en : r.name_uz);

  return (
    <div className="landing">
      <LandingNav />
      <Hero t={t} />
      <Features t={t} />
      <RolesSection t={t} rolesByTeam={rolesByTeam} nameOf={nameOf} />
      <RulesSection t={t} />
      <PremiumSection t={t} />
      <CTASection t={t} />
      <LandingFooter t={t} />
    </div>
  );
}

// === Sub-components ====================================================

function LandingNav() {
  const { t, i18n } = useTranslation();
  const onLang = (e: React.ChangeEvent<HTMLSelectElement>) =>
    i18n.changeLanguage(e.target.value);

  return (
    <header className="landing-nav">
      <div className="landing-nav-inner">
        <a href="#top" className="landing-brand">
          <img src="/bot-avatar.png" alt="" className="landing-brand-icon" />
          <span>MAFIA</span>
        </a>
        <nav className="landing-nav-links">
          <a href="#roles">{t("landing.nav_roles")}</a>
          <a href="#rules">{t("landing.nav_rules")}</a>
          <a href="#premium">{t("landing.nav_premium")}</a>
          <select
            value={i18n.language}
            onChange={onLang}
            className="landing-lang"
            aria-label="Language"
          >
            <option value="uz">🇺🇿 UZ</option>
            <option value="ru">🇷🇺 RU</option>
            <option value="en">🇬🇧 EN</option>
          </select>
          <Link to="/admin" className="landing-nav-admin">
            {t("landing.nav_admin")}
          </Link>
        </nav>
      </div>
    </header>
  );
}

function Hero({ t }: { t: (k: string) => string }) {
  return (
    <section id="top" className="landing-hero">
      <div className="landing-hero-bg" aria-hidden="true">
        <div className="hero-glow hero-glow--a" />
        <div className="hero-glow hero-glow--b" />
        <div className="hero-grid" />
      </div>
      <div className="landing-hero-inner">
        <div className="hero-copy">
          <span className="hero-eyebrow">@MafGameUzBot</span>
          <h1 className="hero-title">
            MAFIA<span className="hero-title-dot">.</span>
          </h1>
          <p className="hero-tagline">{t("landing.hero_tagline")}</p>
          <div className="hero-stats">
            <Stat n="21+" label={t("landing.stat_roles")} />
            <Stat n="4–30" label={t("landing.stat_players")} />
            <Stat n="3" label={t("landing.stat_langs")} />
            <Stat n="100%" label={t("landing.stat_free")} />
          </div>
          <div className="hero-cta">
            <a className="btn btn-primary" href={ADD_TO_GROUP_URL} target="_blank" rel="noopener">
              ➕ {t("landing.cta_add_to_group")}
            </a>
            <a className="btn btn-ghost" href="#rules">
              {t("landing.cta_rules")} →
            </a>
          </div>
        </div>
        <div className="hero-art" aria-hidden="true">
          <div className="hero-card hero-card--back hero-card--rot-l">
            <span>♠</span>
          </div>
          <div className="hero-card hero-card--mid hero-card--rot-r">
            <span>M</span>
          </div>
          <img src="/bot-avatar.png" alt="" className="hero-avatar" />
        </div>
      </div>
    </section>
  );
}

function Stat({ n, label }: { n: string; label: string }) {
  return (
    <div className="hero-stat">
      <div className="hero-stat-n">{n}</div>
      <div className="hero-stat-l">{label}</div>
    </div>
  );
}

function Features({ t }: { t: (k: string) => string }) {
  const items: { icon: string; titleKey: string; descKey: string }[] = [
    { icon: "🎭", titleKey: "landing.f1_title", descKey: "landing.f1_desc" },
    { icon: "🌙", titleKey: "landing.f2_title", descKey: "landing.f2_desc" },
    { icon: "💎", titleKey: "landing.f3_title", descKey: "landing.f3_desc" },
    { icon: "🏆", titleKey: "landing.f4_title", descKey: "landing.f4_desc" },
    { icon: "🎒", titleKey: "landing.f5_title", descKey: "landing.f5_desc" },
    { icon: "🌍", titleKey: "landing.f6_title", descKey: "landing.f6_desc" },
  ];
  return (
    <section className="landing-section">
      <SectionHeader eyebrow="01" title={t("landing.features_title")} />
      <div className="features-grid">
        {items.map((it) => (
          <article key={it.titleKey} className="feature">
            <div className="feature-icon">{it.icon}</div>
            <h3>{t(it.titleKey)}</h3>
            <p>{t(it.descKey)}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

function RolesSection({
  t,
  rolesByTeam,
  nameOf,
}: {
  t: (k: string) => string;
  rolesByTeam: Record<PublicRole["team"], PublicRole[]>;
  nameOf: (r: PublicRole) => string;
}) {
  return (
    <section id="roles" className="landing-section">
      <SectionHeader eyebrow="02" title={t("landing.roles_title")} subtitle={t("landing.roles_subtitle")} />
      <div className="teams-grid">
        {TEAM_ORDER.map((team) => {
          const meta = TEAM_META[team];
          const list = rolesByTeam[team];
          return (
            <div key={team} className={`team-col ${meta.tone}`}>
              <div className="team-header">
                <span className="team-emoji">{meta.emoji}</span>
                <h3>{t(meta.key)}</h3>
                <span className="team-count">{list.length}</span>
              </div>
              <ul className="role-list">
                {list.map((r) => (
                  <li key={r.role} className="role-pill">
                    <span className="role-emoji">{r.static_emoji}</span>
                    <span className="role-name">{nameOf(r)}</span>
                    {r.custom_emoji_id && (
                      <span className="role-star" title="Animated emoji">★</span>
                    )}
                  </li>
                ))}
                {list.length === 0 && (
                  <li className="role-pill role-pill--ghost">…</li>
                )}
              </ul>
            </div>
          );
        })}
      </div>
    </section>
  );
}

function RulesSection({ t }: { t: (k: string) => string }) {
  return (
    <section id="rules" className="landing-section">
      <SectionHeader eyebrow="03" title={t("landing.rules_title")} subtitle={t("landing.rules_subtitle")} />
      <div className="rules-cycle">
        <div className="rule-phase rule-phase--night">
          <div className="rule-phase-icon">🌙</div>
          <h3>{t("landing.phase_night")}</h3>
          <p>{t("landing.phase_night_desc")}</p>
          <ul>
            <li>{t("landing.phase_night_i1")}</li>
            <li>{t("landing.phase_night_i2")}</li>
            <li>{t("landing.phase_night_i3")}</li>
          </ul>
        </div>
        <div className="rule-arrow">→</div>
        <div className="rule-phase rule-phase--day">
          <div className="rule-phase-icon">☀️</div>
          <h3>{t("landing.phase_day")}</h3>
          <p>{t("landing.phase_day_desc")}</p>
          <ul>
            <li>{t("landing.phase_day_i1")}</li>
            <li>{t("landing.phase_day_i2")}</li>
            <li>{t("landing.phase_day_i3")}</li>
          </ul>
        </div>
        <div className="rule-arrow">→</div>
        <div className="rule-phase rule-phase--win">
          <div className="rule-phase-icon">🏆</div>
          <h3>{t("landing.phase_win")}</h3>
          <p>{t("landing.phase_win_desc")}</p>
          <ul>
            <li>{t("landing.phase_win_i1")}</li>
            <li>{t("landing.phase_win_i2")}</li>
            <li>{t("landing.phase_win_i3")}</li>
          </ul>
        </div>
      </div>
    </section>
  );
}

function PremiumSection({ t }: { t: (k: string) => string }) {
  const items: { icon: string; titleKey: string; descKey: string }[] = [
    { icon: "💎", titleKey: "landing.p1_title", descKey: "landing.p1_desc" },
    { icon: "🃏", titleKey: "landing.p2_title", descKey: "landing.p2_desc" },
    { icon: "🎁", titleKey: "landing.p3_title", descKey: "landing.p3_desc" },
    { icon: "📊", titleKey: "landing.p4_title", descKey: "landing.p4_desc" },
  ];
  return (
    <section id="premium" className="landing-section landing-section--alt">
      <SectionHeader eyebrow="04" title={t("landing.premium_title")} subtitle={t("landing.premium_subtitle")} />
      <div className="premium-grid">
        {items.map((it) => (
          <article key={it.titleKey} className="premium-card">
            <div className="premium-icon">{it.icon}</div>
            <div>
              <h3>{t(it.titleKey)}</h3>
              <p>{t(it.descKey)}</p>
            </div>
          </article>
        ))}
      </div>
      <div className="premium-cta">
        <a
          className="btn btn-ghost btn-sm"
          href={EMOJI_PACK_URL}
          target="_blank"
          rel="noopener"
        >
          🃏 {t("landing.premium_emoji_pack")}
        </a>
      </div>
    </section>
  );
}

function CTASection({ t }: { t: (k: string) => string }) {
  return (
    <section className="landing-cta">
      <div className="landing-cta-inner">
        <h2>{t("landing.cta_title")}</h2>
        <p>{t("landing.cta_subtitle")}</p>
        <div className="landing-cta-buttons">
          <a className="btn btn-primary btn-lg" href={ADD_TO_GROUP_URL} target="_blank" rel="noopener">
            ➕ {t("landing.cta_add_to_group")}
          </a>
          <a className="btn btn-ghost" href={NEWS_URL} target="_blank" rel="noopener">
            📢 {t("landing.cta_news")}
          </a>
        </div>
      </div>
    </section>
  );
}

function LandingFooter({ t }: { t: (k: string) => string }) {
  return (
    <footer className="landing-footer">
      <div className="landing-footer-inner">
        <div className="landing-footer-brand">
          <img src="/bot-avatar.png" alt="" />
          <div>
            <div className="landing-footer-name">Mafia</div>
            <div className="landing-footer-handle">@MafGameUzBot</div>
          </div>
        </div>
        <div className="landing-footer-cols">
          <div>
            <h4>{t("landing.footer_play")}</h4>
            <a href={ADD_TO_GROUP_URL} target="_blank" rel="noopener">{t("landing.cta_add_to_group")}</a>
            <a href={BOT_URL} target="_blank" rel="noopener">@MafGameUzBot</a>
            <a href={NEWS_URL} target="_blank" rel="noopener">@Mafiauzbot_news</a>
          </div>
          <div>
            <h4>{t("landing.footer_resources")}</h4>
            <a href={EMOJI_PACK_URL} target="_blank" rel="noopener">{t("landing.premium_emoji_pack")}</a>
            <a href="#roles">{t("landing.nav_roles")}</a>
            <a href="#rules">{t("landing.nav_rules")}</a>
          </div>
          <div>
            <h4>{t("landing.footer_admin")}</h4>
            <Link to="/admin">{t("landing.nav_admin")}</Link>
          </div>
        </div>
      </div>
      <div className="landing-footer-bottom">
        <span>© {new Date().getFullYear()} Mafia · mafia.omadli.uz</span>
      </div>
    </footer>
  );
}

function SectionHeader({
  eyebrow,
  title,
  subtitle,
}: {
  eyebrow: string;
  title: string;
  subtitle?: string;
}) {
  return (
    <header className="section-header">
      <div className="section-eyebrow">{eyebrow}</div>
      <h2 className="section-title">{title}</h2>
      {subtitle && <p className="section-subtitle">{subtitle}</p>}
    </header>
  );
}
