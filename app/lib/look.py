"""HTML pieces of the U1 screens: CSS, line icons, static previews, bars, badges (config/public.yaml fixes U1-1).

There are no on-screen words in this file: every text a function draws is passed in by the page, which takes it from t(...).
Why tags and CSS are built from small tables: the app-code lint (bundle check 6) rejects string constants that hold two
English words separated by a space, so a literal such as an SVG tag with attributes or "1px solid" cannot be written here.
CSS therefore uses longhand properties without spaces (border-width / border-style / border-color) and child selectors.
All HTML is one line without blank lines, so Streamlit's markdown treats it as a raw HTML block (no markdown inside).
"""

from __future__ import annotations

from html import escape

# ---------------------------------------------------------------- colours of the Cowork reference (fixes U1-1 spec.common)
ACCENT = "#1D4E89"
ACCENT_SOFT = "#EAF0F7"
PASS = "#1F7A4D"
PASS_SOFT = "#E3F1EA"
BASELINE = "#9AA3AF"
INFO = "#5B6472"
LINE = "#CBD2DC"
LINE_SOFT = "#DDE2E8"

# selector -> declarations (no spaces inside a declaration)
CSS = {
    "[data-testid=stMainBlockContainer] h1": ["font-size:1.6rem", "font-weight:700", "line-height:1.3"],
    "[data-testid=stMainBlockContainer] h3": ["font-size:1.1rem", "font-weight:700"],
    "[class*=st-key-kpd_card]": ["background:#FFFFFF", "border-width:1px", "border-style:solid", "border-color:#E3E6EB",
                                 "border-radius:12px", "padding:18px"],
    ".kpd-grid": ["display:grid", "grid-template-columns:repeat(auto-fit,minmax(min(100%,220px),1fr))", "gap:16px", "margin:4px 0 16px"],
    ".kpd-grid2": ["display:grid", "grid-template-columns:repeat(auto-fit,minmax(min(100%,340px),1fr))", "gap:16px", "margin:4px 0 8px"],
    ".kpd-card": ["background:#FFFFFF", "border-width:1px", "border-style:solid", "border-color:#E3E6EB",
                  "border-radius:12px", "padding:18px", "display:flex", "flex-direction:column", "gap:10px", "min-width:0"],
    ".kpd-sub": ["border-width:1px", "border-style:solid", "border-color:#E3E6EB", "border-radius:10px", "padding:16px",
                 "display:flex", "flex-direction:column", "gap:8px", "min-width:0"],
    ".kpd-head": ["display:flex", "align-items:center", "gap:10px", "font-size:13px", "color:#4A5361"],
    ".kpd-head-strong": ["display:flex", "align-items:center", "gap:10px", "font-size:16px", "font-weight:700",
                         "color:#14181F"],
    ".kpd-ico": ["width:40px", "height:40px", "border-radius:10px", "background:" + ACCENT_SOFT, "display:flex",
                 "align-items:center", "justify-content:center", "flex:none"],
    ".kpd-ico-sm": ["width:32px", "height:32px", "border-radius:8px", "background:" + ACCENT_SOFT, "display:flex",
                    "align-items:center", "justify-content:center", "flex:none"],
    ".kpd-big": ["font-size:24px", "font-weight:700", "line-height:1.25", "color:#14181F", "overflow-wrap:anywhere"],
    ".kpd-huge": ["font-size:30px", "font-weight:700", "line-height:1.2", "color:#14181F"],
    ".kpd-note": ["font-size:12.5px", "line-height:1.55", "color:#5B6472", "margin:0"],
    ".kpd-text": ["font-size:14px", "line-height:1.6", "color:#3D4654", "margin:0"],
    ".kpd-preview": ["background:#F6F8FB", "border-radius:8px", "height:88px", "display:flex", "align-items:center",
                     "justify-content:center", "margin:10px 0"],
    ".kpd-track": ["height:8px", "min-height:8px", "flex:none", "background:#EEF0F3", "border-radius:4px", "overflow:hidden"],
    ".kpd-fill-pass": ["height:100%", "background:" + PASS, "border-radius:4px"],
    ".kpd-fill-base": ["height:100%", "background:" + BASELINE, "border-radius:4px"],
    ".kpd-fill-accent": ["height:100%", "background:" + ACCENT, "border-radius:4px"],
    ".kpd-cmp": ["display:grid", "grid-template-columns:minmax(64px,auto) 1fr 52px", "align-items:center", "gap:8px",
                 "font-size:12.5px", "color:#3D4654"],
    ".kpd-cmp>span:last-child": ["text-align:right", "white-space:nowrap"],
    ".kpd-cmps": ["display:flex", "flex-direction:column", "gap:6px"],
    ".kpd-badges": ["display:flex", "gap:6px", "flex-wrap:wrap", "align-items:center"],
    ".kpd-b-pdf,.kpd-b-xlsx,.kpd-b-lang,.kpd-chip": ["font-size:12px", "font-weight:700", "padding:3px 8px",
                                                     "border-radius:6px", "white-space:nowrap"],
    ".kpd-b-pdf": ["background:#FDECEC", "color:#8A1F1F"],
    ".kpd-b-xlsx": ["background:" + PASS_SOFT, "color:#1F5E3D"],
    ".kpd-b-lang": ["background:" + ACCENT_SOFT, "color:" + ACCENT],
    ".kpd-chip": ["background:#EEF0F3", "color:#3D4654", "font-weight:500", "border-radius:999px", "padding:4px 10px"],
    ".kpd-result": ["display:flex", "flex-wrap:wrap", "align-items:baseline", "gap:6px 14px", "margin-bottom:14px"],
    ".kpd-range": ["position:relative", "height:58px", "margin:0 10px"],
    ".kpd-r-axis": ["position:absolute", "left:0", "right:0", "top:26px", "height:4px", "background:#E3E6EB",
                    "border-radius:2px"],
    ".kpd-r-band": ["position:absolute", "top:20px", "height:16px", "background:#C9D9EC", "border-radius:4px"],
    ".kpd-r-point": ["position:absolute", "top:14px", "width:4px", "height:28px", "margin-left:-2px",
                     "background:" + ACCENT, "border-radius:2px"],
    ".kpd-r-tick": ["position:absolute", "top:44px", "font-size:12px", "color:#5B6472", "transform:translateX(-50%)",
                    "white-space:nowrap"],
    ".kpd-r-tick-end": ["position:absolute", "top:44px", "right:0", "font-size:12px", "color:#5B6472",
                        "white-space:nowrap", "transform:translateX(50%)"],
    ".kpd-foot": ["display:flex", "flex-wrap:wrap", "justify-content:space-between", "gap:8px 16px", "font-size:12.5px",
                  "color:#5B6472", "padding-top:6px"],
    ".kpd-foot>span>a": ["color:" + ACCENT],
    ".kpd-link": ["font-size:13px", "color:" + ACCENT],
    "[class*=st-key-kpd_card] [data-testid=stPageLink] p": ["color:" + ACCENT, "font-weight:600", "font-size:14px"],
    ".kpd-gtitle": ["display:flex", "align-items:center", "gap:8px", "font-weight:700", "font-size:15px",
                    "margin:0 0 4px"],
}

# line icons, 24 x 24 view box: (tag, attributes)
ICONS = {
    "calc": [("rect", {"x": 5, "y": 3, "width": 14, "height": 18, "rx": 2}),
             ("path", {"d": "M8 7h8M8 12h2M12 12h2M8 16h2M12 16h2"})],
    "rows": [("path", {"d": "M4 5h16M4 10h16M4 15h16M4 20h10"})],
    "range": [("path", {"d": "M4 12h16"}), ("path", {"d": "M8 8v8M16 8v8"}), ("circle", {"cx": 12, "cy": 12, "r": 2})],
    "check": [("path", {"d": "M5 12l4 4 10-10"})],
    "db": [("ellipse", {"cx": 12, "cy": 6, "rx": 8, "ry": 3}),
           ("path", {"d": "M4 6v12c0 1.7 3.6 3 8 3s8-1.3 8-3V6M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"})],
    "ok": [("circle", {"cx": 12, "cy": 12, "r": 9}), ("path", {"d": "M8 12l3 3 5-6"})],
    "bars": [("path", {"d": "M4 19h16M7 16V10M12 16V6M17 16v-4"})],
    "file": [("path", {"d": "M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"}), ("path", {"d": "M14 3v5h5"})],
    "pass": [("circle", {"cx": 12, "cy": 12, "r": 10}), ("path", {"d": "M7 12l3.5 3.5L17 9"})],
    "info": [("circle", {"cx": 12, "cy": 12, "r": 10}), ("path", {"d": "M12 11v6M12 7.5v.5"})],
}

# static previews of the four home tiles, 200 x 72, no numbers and no words (fixes U1-1 spec.home)
PREVIEWS = {
    "calc": [("path", {"d": "M14 8v56h176", "fill": "none", "stroke": LINE, "stroke-width": 1.5}),
             ("path", {"d": "M20 14C60 40 110 56 186 60", "fill": "none", "stroke": ACCENT, "stroke-width": 2.5}),
             ("circle", {"cx": 96, "cy": 47, "r": 5, "fill": ACCENT}),
             ("path", {"d": "M96 47V64", "stroke": ACCENT, "stroke-dasharray": "3 3"})],
    "comps": [("rect", {"x": 10, "y": y, "width": 60, "height": 8, "rx": 2, "fill": LINE}) for y in (8, 24, 40, 56)]
    + [("rect", {"x": 80, "y": y, "width": 40, "height": 8, "rx": 2, "fill": LINE_SOFT}) for y in (8, 24, 40, 56)]
    + [("rect", {"x": x, "y": y, "width": w, "height": 8, "rx": 2, "fill": ACCENT, "opacity": o})
       for x, y, w, o in ((138, 8, 52, 1), (152, 24, 38, 0.75), (130, 40, 60, 0.9), (160, 56, 30, 0.6))],
    "fair": [("path", {"d": "M10 36h180", "stroke": LINE, "stroke-width": 4, "stroke-linecap": "round"}),
             ("rect", {"x": 70, "y": 26, "width": 62, "height": 20, "rx": 4, "fill": "#C9D9EC"}),
             ("rect", {"x": 113, "y": 18, "width": 4, "height": 36, "rx": 2, "fill": ACCENT})],
    "valid": [s for y in (14, 36, 58) for s in (
        ("circle", {"cx": 18, "cy": y, "r": 8, "fill": PASS_SOFT}),
        ("path", {"d": f"M14 {y}l3 3 5-6", "fill": "none", "stroke": PASS, "stroke-width": 2}))]
    + [("rect", {"x": 34, "y": y - 4, "width": w, "height": 8, "rx": 2, "fill": LINE}) for y, w in ((14, 120), (36, 96), (58, 140))],
}


def attrs(a: dict | None) -> str:
    """HTML attributes from a dict (values escaped)."""
    return "".join(" " + k + '="' + escape(str(v), quote=True) + '"' for k, v in (a or {}).items())


def el(tag: str, a: dict | None = None, *children: str) -> str:
    """One element; children are HTML strings (escape plain text with txt())."""
    return "<" + tag + attrs(a) + ">" + "".join(children) + "</" + tag + ">"


def txt(s) -> str:
    """Plain text for HTML: only &, <, > are escaped, so a translated sentence stays readable in the page source."""
    return escape(str(s), quote=False)


def css() -> str:
    """The whole style sheet as one <style> element."""
    return el("style", None, "".join(sel + "{" + ";".join(decls) + "}" for sel, decls in CSS.items()))


def svg(shapes, w: int, h: int, view: str, stroke: str | None = None, width: float = 1.8, label: str | None = None) -> str:
    """Inline SVG from (tag, attributes) shapes. stroke = line-icon colour (fill none); label = accessible name."""
    a = {"width": w, "height": h, "viewBox": view}
    if stroke:
        a.update({"fill": "none", "stroke": stroke, "stroke-width": width, "stroke-linecap": "round",
                  "stroke-linejoin": "round"})
    a.update({"role": "img", "aria-label": label} if label else {"aria-hidden": "true"})
    return el("svg", a, *(el(t, s) for t, s in shapes))


def icon(name: str, color: str = ACCENT, size: int = 22, box: str | None = "kpd-ico", label: str | None = None,
         width: float = 1.8) -> str:
    """A line icon, by default inside the light accent square (40px)."""
    s = svg(ICONS[name], size, size, "0 0 24 24", stroke=color, width=width, label=label)
    return el("span", {"class": box}, s) if box else s


def preview(name: str) -> str:
    """Static tile preview drawing (no numbers, no words)."""
    return el("div", {"class": "kpd-preview"}, svg(PREVIEWS[name], 200, 72, "0 0 200 72"))


def head(icon_html: str, text: str, strong: bool = False) -> str:
    """Card header row: icon + title."""
    return el("div", {"class": "kpd-head-strong" if strong else "kpd-head"}, icon_html, el("span", None, txt(text)))


def big(text: str, cls: str = "kpd-big") -> str:
    return el("div", {"class": cls}, txt(text))


def note(text: str, cls: str = "kpd-note") -> str:
    return el("p", {"class": cls}, txt(text))


def bar(frac: float, kind: str = "pass") -> str:
    """Horizontal bar, frac in [0, 1] (clipped). kind: pass / base / accent."""
    f = max(0.0, min(1.0, float(frac)))
    return el("div", {"class": "kpd-track"}, el("div", {"class": "kpd-fill-" + kind, "style": f"width:{f * 100:.1f}%"}))


def compare(rows) -> str:
    """Rows of (label, value text, frac, kind): label | bar | value."""
    return el("div", {"class": "kpd-cmps"}, *(
        el("div", {"class": "kpd-cmp"}, el("span", None, txt(lab)), bar(frac, kind), el("span", None, txt(val)))
        for lab, val, frac, kind in rows))


def badge(text: str, kind: str) -> str:
    """Small label: kind pdf / xlsx / lang."""
    return el("span", {"class": "kpd-b-" + kind}, txt(text))


def chip(text: str) -> str:
    return el("span", {"class": "kpd-chip"}, txt(text))


def badges(*items: str) -> str:
    return el("div", {"class": "kpd-badges"}, *items)


def card(*parts: str, cls: str = "kpd-card") -> str:
    return el("div", {"class": cls}, *parts)


def grid(*cards: str, cls: str = "kpd-grid") -> str:
    """Responsive card grid (kpd-grid: columns of at least 220px, kpd-grid2: 340px; one column on a phone)."""
    return el("div", {"class": cls}, *cards)


def link(text: str, url: str, cls: str = "kpd-link") -> str:
    """External link (new tab)."""
    return el("a", {"class": cls, "href": url, "target": "_blank", "rel": "noopener"}, txt(text))


def range_bar(low: float, high: float, point: float, lo_axis: float, hi_axis: float, end_label: str) -> str:
    """Range band (low..high) with the point estimate as a vertical line on a fixed axis lo_axis..hi_axis.
    Ticks: the axis start, middle and end (end_label carries the unit)."""
    span = (hi_axis - lo_axis) or 1.0

    def pos(v: float) -> float:
        return max(0.0, min(100.0, (float(v) - lo_axis) / span * 100.0))

    mid = (lo_axis + hi_axis) / 2.0
    return el("div", {"class": "kpd-range"},
              el("div", {"class": "kpd-r-axis"}),
              el("div", {"class": "kpd-r-band", "style": f"left:{pos(low):.2f}%;width:{max(pos(high) - pos(low), 0.5):.2f}%"}),
              el("div", {"class": "kpd-r-point", "style": f"left:{pos(point):.2f}%"}),
              el("span", {"class": "kpd-r-tick", "style": "left:0%;transform:none"}, txt(f"{lo_axis:g}")),
              el("span", {"class": "kpd-r-tick", "style": "left:50%"}, txt(f"{mid:g}")),
              el("span", {"class": "kpd-r-tick-end", "style": "transform:none"}, txt(end_label)))
