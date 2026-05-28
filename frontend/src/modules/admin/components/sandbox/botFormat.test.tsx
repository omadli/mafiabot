/**
 * Parser smoke tests.
 *
 * Tests rely on react-dom/server's renderToStaticMarkup so we can
 * assert the resulting HTML directly — much faster than booting a full
 * RTL render harness for what is essentially a pure function.
 */
import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";

import { renderBotText } from "./botFormat";

const html = (node: React.ReactNode) => renderToStaticMarkup(<>{node}</>);

describe("renderBotText — plain text", () => {
  it("renders empty input as nothing", () => {
    expect(renderBotText("", null)).toBeNull();
    expect(renderBotText(null, null)).toBeNull();
  });

  it("preserves newlines as <br>", () => {
    expect(html(renderBotText("a\nb\nc", null))).toContain("a<br/>b<br/>c");
  });
});

describe("renderBotText — Markdown", () => {
  it("renders *bold*", () => {
    expect(html(renderBotText("Hello *world*", "Markdown"))).toContain(
      "<strong>world</strong>",
    );
  });

  it("renders _italic_", () => {
    expect(html(renderBotText("_run_", "Markdown"))).toContain("<em>run</em>");
  });

  it("renders `code`", () => {
    expect(html(renderBotText("`x`", "Markdown"))).toContain("<code>x</code>");
  });

  it("renders ```code blocks```", () => {
    const out = html(renderBotText("```\nfoo\nbar\n```", "Markdown"));
    expect(out).toContain("<pre");
    expect(out).toContain("foo\nbar\n");
  });

  it("renders [text](url) as a safe link", () => {
    const out = html(
      renderBotText("[click](https://example.com)", "Markdown"),
    );
    // URL parsing normalises the host with a trailing slash.
    expect(out).toMatch(/href="https:\/\/example\.com\/?"/);
    expect(out).toContain("click");
    expect(out).toContain('target="_blank"');
    expect(out).toContain('rel="noopener noreferrer"');
  });

  it("rejects javascript: URLs (no anchor produced)", () => {
    const out = html(
      renderBotText("[evil](javascript:alert(1))", "Markdown"),
    );
    // Critical: no <a href> with javascript: ever emitted.
    expect(out).not.toMatch(/href=["']javascript:/);
    // Falls through as literal text — the dangerous string appears
    // verbatim but is text-encoded, not an attribute.
    expect(out).toContain("[evil](javascript:alert(1))");
  });

  it("rejects data: URLs (no anchor produced)", () => {
    const out = html(renderBotText("[data](data:text/html,xxx)", "Markdown"));
    expect(out).not.toMatch(/href=["']data:/);
    expect(out).toContain("[data](data:text/html,xxx)");
  });
});

describe("renderBotText — HTML", () => {
  it("recognises <b> / <strong>", () => {
    expect(html(renderBotText("<b>x</b>", "HTML"))).toContain("<strong>x</strong>");
    expect(html(renderBotText("<strong>y</strong>", "HTML"))).toContain(
      "<strong>y</strong>",
    );
  });

  it("recognises <i> / <em>", () => {
    expect(html(renderBotText("<i>x</i>", "HTML"))).toContain("<em>x</em>");
  });

  it("recognises <code>", () => {
    expect(html(renderBotText("<code>x</code>", "HTML"))).toContain(
      "<code>x</code>",
    );
  });

  it("recognises <s> / strikethrough", () => {
    expect(html(renderBotText("<s>x</s>", "HTML"))).toContain("<s>x</s>");
  });

  it("recognises <a href>", () => {
    const out = html(
      renderBotText('<a href="https://e.com">go</a>', "HTML"),
    );
    expect(out).toMatch(/href="https:\/\/e\.com\/?"/);
    expect(out).toContain("go");
  });

  it("rejects javascript: anchors", () => {
    const out = html(
      renderBotText('<a href="javascript:alert(1)">x</a>', "HTML"),
    );
    expect(out).not.toMatch(/href=["']javascript:/);
    // Renders the inner text as a safe <span>.
    expect(out).toContain("x");
  });

  it("escapes unknown tags as literal text", () => {
    const out = html(
      renderBotText("<script>alert(1)</script>hi", "HTML"),
    );
    expect(out).not.toContain("<script>");
    expect(out).toContain("alert(1)");
    expect(out).toContain("hi");
  });

  it("handles <br>", () => {
    const out = html(renderBotText("a<br>b", "HTML"));
    expect(out).toContain("<br/>");
  });

  it("survives a stray closing tag", () => {
    expect(() => html(renderBotText("hello</b>world", "HTML"))).not.toThrow();
  });
});
