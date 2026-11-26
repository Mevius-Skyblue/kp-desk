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
# ② chart category colours = chartCategoricalColors of docs/ci/streamlit_config.toml (same order). The chart passes them as
# its explicit colour range so the HTML legend below it (fixes U1-2 B6) shows exactly the chart's colours.
CHART_COLORS = ("#1F4E79", "#E07B39", "#2E8B57", "#8E5EA2", "#C9A227", "#4A9BD1", "#B5475B", "#6B7280")
PRINCIPAL = "#9DB7D5"  # ① cash-flow chart: principal bars (coupons in ACCENT), fixes U2-1 A
SRC_CELL = {"sec": "background-color:#EEF0F3;color:#3D4654;font-weight:700",  # ② source cells in the ③ badge colours
            "dart": "background-color:" + ACCENT_SOFT + ";color:" + ACCENT + ";font-weight:700",
            "news": "background-color:" + ACCENT_SOFT + ";color:" + ACCENT + ";font-weight:700"}

# selector -> declarations (no spaces inside a declaration)
CSS = {
    "[data-testid=stMainBlockContainer] h1": ["font-size:1.6rem", "font-weight:700", "line-height:1.3"],
    "[data-testid=stMainBlockContainer] h3": ["font-size:1.1rem", "font-weight:700"],
    "[class*=st-key-kpd_card]": ["background:#FFFFFF", "border-width:1px", "border-style:solid", "border-color:#E3E6EB",
                                 "border-radius:12px", "padding:18px"],
    ".kpd-grid": ["display:grid", "grid-template-columns:repeat(auto-fit,minmax(min(100%,220px),1fr))", "gap:16px", "margin:4px 0 16px"],
    # two columns at most (fixes U1-2 B1): each column is at least 40% of the row, so a third never fits (the old
    # minmax(340px) gave 3 + 1 cards on a wide screen); below about 700px it is one column (min(100%,340px) wins)
    ".kpd-grid2": ["display:grid", "grid-template-columns:repeat(auto-fit,minmax(max(min(100%,340px),40%),1fr))", "gap:16px",
                   "margin:4px 0 8px"],
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
    ".kpd-cmps": ["display:grid", "grid-template-columns:fit-content(50%) 1fr 56px", "align-items:center", "gap:6px 8px",
                  "font-size:12.5px", "color:#3D4654"],
    ".kpd-cmp-v": ["text-align:right", "white-space:nowrap"],
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
    # ③ comparable-deal dots on the range bar and the table under it (fixes U1-2 A)
    ".kpd-range-dots": ["position:relative", "height:86px", "margin:0 10px"],
    ".kpd-range-dots>.kpd-r-axis": ["top:40px"],
    ".kpd-range-dots>.kpd-r-band": ["top:34px"],
    ".kpd-range-dots>.kpd-r-point": ["top:22px", "height:40px"],
    ".kpd-range-dots>.kpd-r-tick,.kpd-range-dots>.kpd-r-tick-end": ["top:70px"],
    ".kpd-dot": ["position:absolute", "width:10px", "height:10px", "box-sizing:border-box", "margin-left:-5px", "margin-top:-5px",
                 "border-radius:50%", "background:#FFFFFF", "border-width:2px", "border-style:solid",
                 "border-color:" + ACCENT, "cursor:default", "z-index:2"],
    ".kpd-dot:hover": ["background:" + ACCENT],
    ".kpd-tbl-wrap": ["overflow-x:auto", "max-height:460px", "overflow-y:auto"],
    ".kpd-tbl": ["width:100%", "border-collapse:collapse", "font-size:13.5px"],  # no min width: compresses on a phone
    ".kpd-tbl>thead>tr>th": ["text-align:left", "font-weight:500", "color:#4A5361", "padding:8px 6px",
                             "border-bottom-width:1px", "border-bottom-style:solid", "border-bottom-color:#E3E6EB",
                             "position:sticky", "top:0", "background:#FFFFFF"],
    ".kpd-tbl>tbody>tr>td": ["word-break:keep-all", "overflow-wrap:break-word", "padding:8px 6px", "border-bottom-width:1px", "border-bottom-style:solid",
                             "border-bottom-color:#EEF0F3"],
    # phone (audit A11-2): headers may wrap, numbers stay on one line, Korean names break between words only
    ".kpd-tbl>thead>tr>th.kpd-num": ["text-align:right"],
    ".kpd-tbl>tbody>tr>td.kpd-num": ["text-align:right", "white-space:nowrap"],
    ".kpd-tbl>tbody>tr>td:nth-child(2)": ["white-space:nowrap"],  # issue date (YYYY-MM-DD) on one line
    ".kpd-b-src": ["font-size:12px", "font-weight:700", "padding:3px 8px", "border-radius:6px", "white-space:nowrap",
                   "background:" + ACCENT_SOFT, "color:" + ACCENT, "text-decoration:none!important"],  # Streamlit underlines links
    ".kpd-b-src-sec": ["background:#EEF0F3", "color:#3D4654"],
    # home tiles (fixes U1-2 B4): the four columns stretch to the tallest tile and 'Open' sits at the bottom, flush left
    "[data-testid=stHorizontalBlock]:has([class*=st-key-kpd_card_tile])": ["align-items:stretch"],
    # column > vertical block > layout wrapper > tile container: each level grows to the column height (Streamlit 1.5x DOM)
    "[data-testid=stColumn]:has([class*=st-key-kpd_card_tile])": ["display:flex", "flex-direction:column"],
    "[data-testid=stColumn]:has([class*=st-key-kpd_card_tile])>[data-testid=stVerticalBlock]": ["flex:1"],
    "[data-testid=stLayoutWrapper]:has(>[class*=st-key-kpd_card_tile])": ["flex:1"],
    "[data-testid=stLayoutWrapper]>[class*=st-key-kpd_card_tile]": ["flex:1"],
    "[class*=st-key-kpd_card_tile]>[data-testid=stElementContainer]:last-child": ["margin-top:auto"],
    "[class*=st-key-kpd_card_tile] [data-testid=stPageLink] a": ["padding-left:0", "margin-left:0"],
    # ② chart legend as HTML (fixes U1-2 B6): two columns like the old chart legend, a long label wraps inside its column on
    # a phone instead of running off the screen
    ".kpd-legend": ["display:grid", "grid-template-columns:repeat(2,minmax(0,max-content))", "column-gap:28px", "row-gap:4px",
                    "font-size:12.5px", "color:#3D4654", "margin:0 0 6px"],
    ".kpd-legend-t": ["grid-column:1/-1", "font-weight:600", "color:#14181F"],
    ".kpd-legend>span": ["display:flex", "align-items:center", "gap:6px", "min-width:0"],
    ".kpd-legend>span>i": ["width:10px", "height:10px", "border-radius:50%", "flex:none"],
    # ① number cards (fixes U2-1 A): six columns on a wide screen, two on a phone (each card at least 150px)
    ".kpd-grid6": ["display:grid", "grid-template-columns:repeat(auto-fit,minmax(min(100%,150px),1fr))", "gap:12px",
                   "margin:4px 0 16px"],
    ".kpd-stat": ["background:#FFFFFF", "border-width:1px", "border-style:solid", "border-color:#E3E6EB",
                  "border-radius:12px", "padding:14px", "display:flex", "flex-direction:column", "gap:8px", "min-width:0"],
    ".kpd-stat-v": ["font-size:22px", "font-weight:700", "line-height:1.2", "color:#14181F", "overflow-wrap:anywhere",
                    "font-variant-numeric:tabular-nums"],
    ".kpd-stat-u": ["font-size:12.5px", "font-weight:500", "color:#5B6472", "margin-top:-4px"],  # unit on its own line
    # ② filter box head: count on the left, reset on the right (fixes U2-1 B)
    ".kpd-count": ["font-size:15px", "font-weight:700", "color:#14181F"],
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
    # ① number cards (fixes U2-1 A)
    "tag": [("path", {"d": "M3 12V4h8l10 10-8 8z"}), ("circle", {"cx": 7.5, "cy": 7.5, "r": 1.5})],
    "pct": [("path", {"d": "M19 5L5 19"}), ("circle", {"cx": 7, "cy": 7, "r": 2.5}), ("circle", {"cx": 17, "cy": 17, "r": 2.5})],
    "clock": [("circle", {"cx": 12, "cy": 12, "r": 9}), ("path", {"d": "M12 7v5l3 2"})],
    "delta": [("path", {"d": "M12 4l8 16H4z"})],
    "gap": [("path", {"d": "M4 19h16M4 5h16"}), ("path", {"d": "M12 8v8M9.5 10.5L12 8l2.5 2.5M9.5 13.5L12 16l2.5-2.5"})],
    "curve": [("path", {"d": "M4 20C9 17 14 12 20 9"}), ("path", {"d": "M4 13C9 10 14 6 20 3", "stroke-dasharray": "2 3"})],
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
    """Rows of (label, value text, frac, kind): label | bar | value, all rows in ONE grid so every bar starts and ends at
    the same x (audit A10-1: one grid per row made the English label column differ and the bar lengths off-ratio)."""
    cells = []
    for lab, val, frac, kind in rows:
        cells += [el("span", None, txt(lab)), bar(frac, kind), el("span", {"class": "kpd-cmp-v"}, txt(val))]
    return el("div", {"class": "kpd-cmps"}, *cells)


def badge(text: str, kind: str) -> str:
    """Small label: kind pdf / xlsx / lang."""
    return el("span", {"class": "kpd-b-" + kind}, txt(text))


def stat(icon_name: str, label: str, value: str, unit: str) -> str:
    """One number card of page ①: icon + label, then the value with its unit (fixes U2-1 A)."""
    return el("div", {"class": "kpd-stat"},
              head(icon(icon_name, size=18, width=2, box="kpd-ico-sm"), label),
              el("div", {"class": "kpd-stat-v"}, txt(value)), el("div", {"class": "kpd-stat-u"}, txt(unit)))


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


DOT_GAP_PCT = 4.0  # dots closer than this (% of the axis width; about one 10px dot on a 300px phone axis, audit A11-R1)
#                   are put on different lanes; on a wide screen this only moves dots that are already close
LANE_STEP_PX = 9  # vertical offset between dot lanes
LANES = (0, -1, 1, -2, 2)  # lane order: on the axis, above, below, two above, two below


def dot_lanes(xs: list[float], gap: float = DOT_GAP_PCT) -> list[int]:
    """Lane of each dot (same order as xs, positions in % of the axis) so that dots closer than `gap` do not overlap:
    in value order, a dot takes the first lane of LANES whose last dot is at least `gap` to the left; when every lane is
    taken it goes back to the middle lane (fixes U1-2 A, 'slightly above / below')."""
    order = sorted(range(len(xs)), key=lambda i: (xs[i], i))
    last: dict[int, float] = {}
    out = [0] * len(xs)
    for i in order:
        lane = next((ln for ln in LANES if ln not in last or xs[i] - last[ln] >= gap), 0)
        last[lane] = xs[i]
        out[i] = lane
    return out


def range_bar(low: float, high: float, point: float, lo_axis: float, hi_axis: float, end_label: str,
              dots: list[tuple[float, str]] | None = None) -> str:
    """Range band (low..high) with the point estimate as a vertical line on a fixed axis lo_axis..hi_axis.
    Ticks: the axis start, middle and end (end_label carries the unit). dots = [(value, hover text)]: comparable deals as
    hollow dots on the axis (fixes U1-2 A); the hover text is the title (tooltip) and the accessible name of the dot."""
    span = (hi_axis - lo_axis) or 1.0

    def pos(v: float) -> float:
        return max(0.0, min(100.0, (float(v) - lo_axis) / span * 100.0))

    mid = (lo_axis + hi_axis) / 2.0
    dot_html = []
    if dots:
        xs = [pos(v) for v, _ in dots]
        for (v, tip), x, lane in zip(dots, xs, dot_lanes(xs)):
            dot_html.append(el("span", {"class": "kpd-dot", "title": tip, "role": "img", "aria-label": tip,
                                        "style": f"left:{x:.2f}%;top:{40 + 2 + lane * LANE_STEP_PX}px"}))
    return el("div", {"class": "kpd-range-dots" if dots else "kpd-range"},
              el("div", {"class": "kpd-r-axis"}),
              el("div", {"class": "kpd-r-band", "style": f"left:{pos(low):.2f}%;width:{max(pos(high) - pos(low), 0.5):.2f}%"}),
              el("div", {"class": "kpd-r-point", "style": f"left:{pos(point):.2f}%"}),
              el("span", {"class": "kpd-r-tick", "style": "left:0%;transform:none"}, txt(f"{lo_axis:g}")),
              el("span", {"class": "kpd-r-tick", "style": "left:50%"}, txt(f"{mid:g}")),
              el("span", {"class": "kpd-r-tick-end", "style": "transform:none"}, txt(end_label)),
              *dot_html)


def source_badge(kind: str | None, text: str, url: str | None) -> str:
    """Source of a deal as a small badge link (kind sec / dart / news); no url -> the text alone (e.g. '–')."""
    if not kind or not url:
        return txt(text)
    cls = " ".join(["kpd-b-src", "kpd-b-src-sec"]) if kind == "sec" else "kpd-b-src"  # (lint: no spaced literals)
    return el("a", {"class": cls, "href": url, "target": "_blank", "rel": "noopener"}, txt(text))


def table(head: list[tuple[str, bool]], rows: list[list[str]]) -> str:
    """Plain HTML table: head = [(label, numeric)], rows = cells as HTML (numeric columns right-aligned)."""
    num = [n for _, n in head]
    th = "".join(el("th", {"class": "kpd-num"} if n else None, txt(h)) for h, n in head)
    body = "".join(el("tr", None, *(el("td", {"class": "kpd-num"} if num[i] else None, c) for i, c in enumerate(r)))
                   for r in rows)
    return el("div", {"class": "kpd-tbl-wrap"},
              el("table", {"class": "kpd-tbl"}, el("thead", None, el("tr", None, th)), el("tbody", None, body)))


def legend(title: str, items: list[tuple[str, str]]) -> str:
    """Chart legend: title + (label, colour) entries in two columns (fixes U1-2 B6)."""
    cells = [el("span", {"class": "kpd-legend-t"}, txt(title))]
    cells += [el("span", None, el("i", {"style": "background:" + c}), el("span", None, txt(lab))) for lab, c in items]
    return el("div", {"class": "kpd-legend", "role": "list"}, *cells)
