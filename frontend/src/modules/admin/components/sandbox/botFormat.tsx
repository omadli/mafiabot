/**
 * Whitelist parser for the subset of Markdown / HTML the bot actually
 * emits in `.ftl` rendered messages.
 *
 * **Security**: this code's outputs are inserted as plain React
 * children. We NEVER use `dangerouslySetInnerHTML`. The parser
 * recognises a tight, hand-picked set of tags + Markdown delimiters
 * and converts them into a React element tree; everything else falls
 * through as text. That gives us bold/italic/code/links + the few
 * HTML tags aiogram's `parse_mode="HTML"` accepts, without opening a
 * raw-HTML injection vector.
 *
 * Supported:
 *   Markdown   — *bold*, _italic_, `code`, [text](url), \n
 *   HTML       — <b>, <strong>, <i>, <em>, <code>, <pre>, <s>, <u>,
 *                <a href="…">, <br>
 *
 * Anything else (other tags, attributes, custom emojis, entities) is
 * shown as literal text.
 */

import React, { type ReactNode } from "react";

export type ParseMode = "Markdown" | "MarkdownV2" | "HTML" | null | undefined;

let _keySeq = 0;
const nextKey = () => `f${_keySeq++}`;

// --- helpers ---------------------------------------------------------------

function safeUrl(raw: string): string | null {
  try {
    const u = new URL(raw);
    if (u.protocol !== "http:" && u.protocol !== "https:") return null;
    return u.toString();
  } catch {
    return null;
  }
}

// --- HTML path -------------------------------------------------------------

const ALLOWED_HTML_TAGS: Record<
  string,
  "b" | "i" | "code" | "pre" | "s" | "u" | "a" | "br" | "mention" | "tg-emoji"
> = {
  b: "b",
  strong: "b",
  i: "i",
  em: "i",
  code: "code",
  pre: "pre",
  s: "s",
  strike: "s",
  del: "s",
  u: "u",
  a: "a",
  br: "br",
  // Bot output uses these Telegram-only HTML extensions:
  //   <a href="tg://user?id=X">name</a> — user mention (no web URL)
  //   <tg-emoji emoji-id="X">😀</tg-emoji> — custom emoji w/ unicode fallback
  // Map them to internal pseudo-tags so renderHtml can style them.
  "tg-emoji": "tg-emoji",
};

interface HtmlNode {
  type: "text" | "element";
  text?: string;
  tag?: string;
  href?: string;
  // For mention nodes: the Telegram user_id parsed out of `tg://user?id=…`.
  // Surfaced so the bubble can show it on hover for debugging.
  userId?: string;
  children?: HtmlNode[];
}

function tokenizeHtml(input: string): HtmlNode[] {
  const out: HtmlNode[] = [];
  const stack: HtmlNode[] = [{ type: "element", tag: "root", children: [] }];
  const root = stack[0];

  // <br/>, <br>
  const tagRe = /<(\/?)(\w+)([^>]*?)(\/?)>/g;
  let last = 0;
  let m: RegExpExecArray | null;
  const pushText = (txt: string) => {
    if (!txt) return;
    stack[stack.length - 1].children!.push({ type: "text", text: txt });
  };

  while ((m = tagRe.exec(input)) !== null) {
    pushText(input.slice(last, m.index));
    last = m.index + m[0].length;
    const closing = m[1] === "/";
    const tagName = m[2].toLowerCase();
    const attrs = m[3] || "";
    const selfClose = m[4] === "/" || tagName === "br";
    const mapped = ALLOWED_HTML_TAGS[tagName];
    if (!mapped) {
      // Unknown tag — render as literal text (escape `<` so it shows).
      pushText(m[0]);
      continue;
    }
    if (mapped === "br") {
      stack[stack.length - 1].children!.push({ type: "element", tag: "br" });
      continue;
    }
    if (closing) {
      // Pop until we find a matching open; ignore stray closes.
      for (let i = stack.length - 1; i > 0; i--) {
        if (stack[i].tag === mapped) {
          stack.length = i; // discard inclusive
          break;
        }
      }
      continue;
    }
    const el: HtmlNode = { type: "element", tag: mapped, children: [] };
    if (mapped === "a") {
      const href = /href=["']([^"']+)["']/i.exec(attrs)?.[1] ?? "";
      // Telegram user mention — `tg://user?id=<digits>`. Surface as a
      // styled mention rather than a dead link (we have no clickable
      // Telegram URL from the dashboard).
      const mention = /^tg:\/\/user\?id=(\d+)/.exec(href);
      if (mention) {
        el.tag = "mention";
        el.userId = mention[1];
      } else {
        const safe = href ? safeUrl(href) : null;
        el.href = safe || undefined;
      }
    } else if (mapped === "tg-emoji") {
      // Custom emoji — we render the inline UTF-8 fallback (the children).
      // Attributes (emoji-id) are ignored; we never reach the Telegram
      // custom-emoji CDN from the dashboard.
    }
    stack[stack.length - 1].children!.push(el);
    if (!selfClose) stack.push(el);
  }
  pushText(input.slice(last));
  void out;
  return root.children!;
}

function renderHtml(nodes: HtmlNode[]): ReactNode[] {
  return nodes.map((n) => {
    if (n.type === "text") return n.text;
    const key = nextKey();
    const kids = renderHtml(n.children || []);
    switch (n.tag) {
      case "b":
        return <strong key={key}>{kids}</strong>;
      case "i":
        return <em key={key}>{kids}</em>;
      case "code":
        return <code key={key}>{kids}</code>;
      case "pre":
        return (
          <pre key={key} style={{ whiteSpace: "pre-wrap", margin: "0.25em 0" }}>
            {kids}
          </pre>
        );
      case "s":
        return <s key={key}>{kids}</s>;
      case "u":
        return <u key={key}>{kids}</u>;
      case "a":
        if (!n.href) return <span key={key}>{kids}</span>;
        return (
          <a key={key} href={n.href} target="_blank" rel="noopener noreferrer">
            {kids}
          </a>
        );
      case "mention":
        // Telegram-style @-mention rendering. Bold accent color, no
        // navigation — the dashboard can't open Telegram profiles.
        return (
          <span
            key={key}
            className="sb-mention"
            title={n.userId ? `tg://user?id=${n.userId}` : undefined}
          >
            {kids}
          </span>
        );
      case "tg-emoji":
        // The children are the Unicode fallback emoji — render verbatim.
        return <span key={key}>{kids}</span>;
      case "br":
        return <br key={key} />;
      default:
        return <span key={key}>{kids}</span>;
    }
  });
}

// --- Markdown path ---------------------------------------------------------
//
// Telegram Markdown is a tiny subset: *bold*, _italic_, `code`,
// [text](url), and ``` for code blocks. We do NOT support nesting
// across types (matching Telegram's own parser) — the bot rarely emits
// that anyway.

function renderMarkdown(input: string): ReactNode[] {
  // Code blocks first — they suppress inner formatting.
  const out: ReactNode[] = [];
  let i = 0;
  while (i < input.length) {
    // ```code block```
    if (input.startsWith("```", i)) {
      const end = input.indexOf("```", i + 3);
      if (end === -1) break;
      const body = input.slice(i + 3, end).replace(/^\n/, "");
      out.push(
        <pre key={nextKey()} style={{ whiteSpace: "pre-wrap", margin: "0.25em 0" }}>
          <code>{body}</code>
        </pre>,
      );
      i = end + 3;
      continue;
    }
    // `inline code`
    if (input[i] === "`") {
      const end = input.indexOf("`", i + 1);
      if (end !== -1) {
        out.push(<code key={nextKey()}>{input.slice(i + 1, end)}</code>);
        i = end + 1;
        continue;
      }
    }
    // *bold*
    if (input[i] === "*") {
      const end = input.indexOf("*", i + 1);
      if (end !== -1) {
        out.push(<strong key={nextKey()}>{renderMarkdown(input.slice(i + 1, end))}</strong>);
        i = end + 1;
        continue;
      }
    }
    // _italic_
    if (input[i] === "_") {
      const end = input.indexOf("_", i + 1);
      if (end !== -1) {
        out.push(<em key={nextKey()}>{renderMarkdown(input.slice(i + 1, end))}</em>);
        i = end + 1;
        continue;
      }
    }
    // [text](url)
    if (input[i] === "[") {
      const close = input.indexOf("]", i + 1);
      if (close !== -1 && input[close + 1] === "(") {
        const paren = input.indexOf(")", close + 2);
        if (paren !== -1) {
          const text = input.slice(i + 1, close);
          const url = safeUrl(input.slice(close + 2, paren));
          if (url) {
            out.push(
              <a key={nextKey()} href={url} target="_blank" rel="noopener noreferrer">
                {renderMarkdown(text)}
              </a>,
            );
            i = paren + 1;
            continue;
          }
        }
      }
    }
    // Newline → <br>
    if (input[i] === "\n") {
      out.push(<br key={nextKey()} />);
      i += 1;
      continue;
    }
    // Regular text — accumulate until next special character.
    let j = i;
    while (j < input.length && !"`*_[\n".includes(input[j])) j += 1;
    if (j > i) {
      out.push(input.slice(i, j));
      i = j;
    } else {
      // Stuck on a special char that didn't match → emit as literal.
      out.push(input[i]);
      i += 1;
    }
  }
  return out;
}

// --- Entry point -----------------------------------------------------------

export function renderBotText(
  text: string | null | undefined,
  parseMode: ParseMode,
): ReactNode {
  if (text === null || text === undefined || text === "") return null;
  if (parseMode === "HTML") {
    return <>{renderHtml(tokenizeHtml(text))}</>;
  }
  if (parseMode === "Markdown" || parseMode === "MarkdownV2") {
    return <>{renderMarkdown(text)}</>;
  }
  // Plain text — preserve newlines as <br>.
  return (
    <>
      {text.split("\n").map((line, i, arr) => (
        <React.Fragment key={i}>
          {line}
          {i < arr.length - 1 && <br />}
        </React.Fragment>
      ))}
    </>
  );
}
