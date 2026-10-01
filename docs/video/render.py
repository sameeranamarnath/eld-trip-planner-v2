"""HTML frame renderer for the Spotter 2 walkthrough video.

Every frame is a full 1920x1080 "screen": the real Windows wallpaper as the
desktop, one application window composited on top of it, a placed mouse cursor
and the subtitle for that moment.  Frames are photographed with headless Edge,
so the code and terminal shots are pixel-crisp rather than upscaled.

Syntax highlighting is vendored highlight.js (VS2015 theme, the closest shipped
match to VS Code's Dark+), loaded from node_modules - no network at build time.
"""

from __future__ import annotations

import subprocess
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
NODE_MODULES = ROOT / "frontend" / "node_modules"
WALLPAPER = Path(r"C:\Users\serve\Downloads\jesusposterpetfect.png")

HIGHLIGHT_JS = NODE_MODULES / "@highlightjs" / "cdn-assets" / "highlight.min.js"
HIGHLIGHT_CSS = NODE_MODULES / "@highlightjs" / "cdn-assets" / "styles" / "vs2015.min.css"

WIDTH, HEIGHT = 1920, 1080

# VS Code Dark Modern, sampled from the real theme.
C = {
    "chrome": "#181818",
    "editor": "#1f1f1f",
    "border": "#2b2b2b",
    "fg": "#cccccc",
    "muted": "#9d9d9d",
    "dim": "#6e6e6e",
    "accent": "#0078d4",
    "tab_idle": "#181818",
    "panel": "#181818",
}

LINE_HEIGHT = 20
CODE_FONT = 14
CODE_PAD_TOP = 8

CURSOR_SVG = (
    '<svg width="26" height="30" viewBox="0 0 26 30" xmlns="http://www.w3.org/2000/svg">'
    '<path d="M3 2 L3 23 L8.5 17.8 L12 26 L15.5 24.4 L12 16.4 L19.5 16.4 Z" '
    'fill="#ffffff" stroke="#111111" stroke-width="1.6" stroke-linejoin="round"/></svg>'
)


def _uri(path: Path) -> str:
    return path.resolve().as_uri()


BASE_CSS = f"""
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:{WIDTH}px; height:{HEIGHT}px; overflow:hidden; }}
body {{ font-family:'Segoe UI',sans-serif; background:#0b0d12; }}

.desktop {{ position:fixed; inset:0; background:url('{_uri(WALLPAPER)}') center/cover no-repeat; }}
.desktop::after {{ content:''; position:absolute; inset:0;
  background:linear-gradient(180deg, rgba(8,10,16,.34), rgba(8,10,16,.55)); }}

.win {{ position:absolute; display:flex; flex-direction:column; overflow:hidden;
  border-radius:9px; border:1px solid rgba(255,255,255,.13);
  box-shadow:0 26px 70px rgba(0,0,0,.62), 0 3px 12px rgba(0,0,0,.5);
  background:{C['editor']}; color:{C['fg']}; }}

.cursor {{ position:absolute; z-index:60; filter:drop-shadow(0 2px 4px rgba(0,0,0,.6)); }}

.caption {{ position:absolute; z-index:70; left:50%; transform:translateX(-50%);
  bottom:34px; max-width:1580px; padding:14px 30px; border-radius:12px;
  background:rgba(10,12,18,.87); border:1px solid rgba(255,255,255,.14);
  box-shadow:0 10px 30px rgba(0,0,0,.5);
  color:#f4f6fb; font-size:25px; font-weight:600; line-height:1.34; text-align:center; }}
"""

VSCODE_CSS = f"""
.title {{ display:flex; align-items:center; height:34px; background:{C['chrome']};
  border-bottom:1px solid {C['border']}; font-size:12px; color:{C['muted']}; padding:0 10px; gap:10px; }}
.title__center {{ flex:1; display:flex; justify-content:center; }}
.title__box {{ background:#2b2b2b; border:1px solid #3c3c3c; border-radius:6px; padding:3px 26px;
  color:#cccccc; font-size:12px; min-width:560px; text-align:center; }}
.ctl {{ display:flex; }}
.ctl span {{ width:44px; height:32px; display:grid; place-items:center; font-size:11px; color:#c8c8c8; }}

.body {{ flex:1; display:flex; min-height:0; }}
.activity {{ width:48px; background:{C['chrome']}; display:flex; flex-direction:column;
  align-items:center; padding-top:6px; border-right:1px solid {C['border']}; }}
.activity i {{ width:48px; height:44px; display:grid; place-items:center; font-size:21px;
  color:#868686; font-style:normal; }}
.activity i.on {{ color:#ffffff; box-shadow:inset 2px 0 0 #ffffff; }}

.side {{ width:266px; background:{C['chrome']}; border-right:1px solid {C['border']};
  display:flex; flex-direction:column; }}
.side__head {{ height:35px; display:flex; align-items:center; justify-content:space-between;
  padding:0 12px; font-size:11px; letter-spacing:.9px; color:#bbbbbb; }}
.side__body {{ flex:1; padding-bottom:8px; overflow:hidden; }}
.row {{ display:flex; align-items:center; gap:6px; height:22px; color:#cccccc; white-space:nowrap;
  font-size:13px; }}
.row .chev {{ color:#7d7d7d; font-size:10px; width:10px; }}
.row .ico {{ font-size:13px; width:16px; text-align:center; color:#9aa4b2; }}
.row.py .ico {{ color:#4b8bbe; }}
.row.json .ico {{ color:#cbcb41; }}
.row.md .ico {{ color:#519aba; }}
.row.on {{ background:#04395e; }}
.stat {{ height:22px; display:flex; gap:14px; padding:0 12px; font-size:13px; color:#9d9d9d;
  align-items:center; }}

.edit {{ flex:1; display:flex; flex-direction:column; min-width:0; background:{C['editor']}; }}
.tabs {{ display:flex; height:35px; background:{C['chrome']}; border-bottom:1px solid {C['border']}; }}
.tab {{ display:flex; align-items:center; gap:8px; padding:0 14px; font-size:13px; color:#9d9d9d;
  border-right:1px solid {C['border']}; background:{C['tab_idle']}; }}
.tab.on {{ background:{C['editor']}; color:#ffffff; }}
.tab .ico {{ font-size:13px; color:#4b8bbe; }}
.tab .x {{ color:#8a8a8a; font-size:12px; }}
.crumbs {{ height:24px; display:flex; align-items:center; gap:5px; padding:0 14px; font-size:12px;
  color:#a9a9a9; border-bottom:1px solid rgba(255,255,255,.04); }}

.codewrap {{ flex:1; position:relative; min-height:0; overflow:hidden; }}
.scroller {{ position:absolute; left:0; top:0; right:100px; bottom:0; transform-origin:top left; }}
.codepane {{ display:flex; align-items:flex-start; }}
.gutter {{ flex:none; width:76px; text-align:right; padding-right:18px;
  font-family:Consolas,'Cascadia Mono',monospace; font-size:{CODE_FONT}px;
  line-height:{LINE_HEIGHT}px; color:{C['dim']}; }}
pre.code {{ flex:1; min-width:0;
  font-family:Consolas,'Cascadia Mono',monospace; font-size:{CODE_FONT}px;
  line-height:{LINE_HEIGHT}px; white-space:pre; }}
pre.code code {{ background:transparent !important; padding:0 !important; font:inherit;
  line-height:{LINE_HEIGHT}px; display:block; white-space:pre; }}
.band {{ position:absolute; left:0; right:0; height:{LINE_HEIGHT}px; pointer-events:none; }}
.band.cur {{ background:rgba(255,255,255,.045); }}
.band.hit {{ background:rgba(255,214,102,.12); outline:1px solid rgba(255,214,102,.26); }}

.minimap {{ position:absolute; right:0; top:0; bottom:0; width:100px; overflow:hidden;
  border-left:1px solid rgba(255,255,255,.04); }}
.minimap pre {{ font-family:Consolas,monospace; font-size:2px; line-height:2.7px; white-space:pre; }}
.minimap code {{ background:transparent !important; padding:0 !important; font:inherit;
  line-height:2.7px; display:block; }}
.minimap .vp {{ position:absolute; right:0; top:0; width:12px; background:rgba(255,255,255,.14); }}

.status {{ height:24px; display:flex; align-items:center; justify-content:space-between;
  background:{C['chrome']}; color:#ffffff; font-size:12px; padding:0 12px; }}
.status .l, .status .r {{ display:flex; align-items:center; gap:16px; }}
.status .chip {{ background:#16825d; border-radius:3px; padding:1px 7px; font-size:11px; }}

.panel {{ height:296px; background:{C['panel']}; border-top:1px solid {C['border']};
  display:flex; flex-direction:column; }}
.panel__tabs {{ height:34px; display:flex; align-items:center; gap:22px; padding:0 16px;
  font-size:11px; letter-spacing:.8px; color:#9d9d9d; }}
.panel__tabs .on {{ color:#ffffff; border-bottom:1px solid #ffffff; padding-bottom:2px; }}
.panel__body {{ flex:1; padding:2px 16px 12px; overflow:hidden;
  font-family:Consolas,'Cascadia Mono',monospace; font-size:13.5px; line-height:19px;
  white-space:pre; color:#cccccc; }}
.panel__body .p {{ color:#23d18b; }}
.panel__body .m {{ color:#3b8eea; }}
.panel__body .d {{ color:#7d8590; }}
.panel__body .w {{ color:#f5f543; }}
.panel__body .e {{ color:#f14c4c; }}
.panel__body .t {{ color:#d7ba7d; }}
"""

BROWSER_CSS = f"""
.bwin {{ background:#2b2b2b; }}
.bstrip {{ height:42px; display:flex; align-items:flex-end; padding-left:10px; gap:6px;
  background:#2b2b2b; }}
.btab {{ display:flex; align-items:center; gap:9px; height:34px; padding:0 12px;
  border-radius:8px 8px 0 0; background:#3c3c3c; color:#eaeaea; font-size:12.5px; }}
.btab .fav {{ width:15px; height:15px; border-radius:4px; background:#e8590c; flex:none; }}
.btab .x {{ color:#bdbdbd; font-size:12px; }}
.bplus {{ width:28px; height:28px; border-radius:50%; display:grid; place-items:center;
  color:#cfcfcf; font-size:16px; }}
.bwin__ctl {{ margin-left:auto; display:flex; align-self:stretch; }}
.bwin__ctl span {{ width:46px; display:grid; place-items:center; color:#d8d8d8; font-size:11px; }}
.bbar {{ height:48px; display:flex; align-items:center; gap:10px; padding:0 12px; background:#2b2b2b; }}
.bnav {{ width:30px; height:30px; display:grid; place-items:center; color:#d0d0d0; font-size:15px; }}
.burl {{ flex:1; height:32px; border-radius:16px; background:#1f1f1f; display:flex;
  align-items:center; gap:10px; padding:0 16px; color:#dcdcdc; font-size:13px;
  border:1px solid #3a3a3a; }}
.burl .lock {{ color:#9ad19a; font-size:12px; }}
.bpage {{ flex:1; background:#ffffff; overflow:hidden; display:flex; }}
.bpage img {{ width:100%; display:block; }}
.bpage.contain {{ align-items:center; justify-content:center; background:#e9edf3; }}
.bpage.contain img {{ width:100%; height:auto; max-height:100%; object-fit:contain; }}
"""

VSCODE_W = 1720
VSCODE_H = 952
VSCODE_X = (WIDTH - VSCODE_W) // 2
VSCODE_Y = (HEIGHT - VSCODE_H) // 2

BROWSER_W = 1602
BROWSER_H = 992
BROWSER_X = (WIDTH - BROWSER_W) // 2
BROWSER_Y = (HEIGHT - BROWSER_H) // 2

EDITOR_VISIBLE = 41  # lines that fit with no bottom panel
EDITOR_VISIBLE_PANEL = 26

ACTIVITY = (
    '<i>&#9776;</i><i class="on">&#128269;</i><i>&#9906;</i><i>&#9673;</i>'
    '<i>&#9638;</i><i>&#9724;</i><i>&#9881;</i>'
)


def _uri_js() -> str:
    return _uri(HIGHLIGHT_JS)


def page(css: str, body: str, *, highlight: bool = True) -> str:
    tail = ""
    if highlight:
        tail = (
            f'<script src="{_uri(HIGHLIGHT_JS)}"></script>'
            "<script>hljs.highlightAll();</script>"
        )
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<title>frame</title>'
        f'<link rel="stylesheet" href="{_uri(HIGHLIGHT_CSS)}">'
        f"<style>{BASE_CSS}{css}</style></head><body>"
        f'<div class="desktop"></div>{body}{tail}</body></html>'
    )


def caption(text: str) -> str:
    return f'<div class="caption">{escape(text)}</div>'


def cursor(x: int, y: int) -> str:
    return f'<div class="cursor" style="left:{x}px;top:{y}px">{CURSOR_SVG}</div>'


LOCK = (
    '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#8fd694" '
    'stroke-width="2.4" stroke-linecap="round"><rect x="4" y="10" width="16" height="11" '
    'rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/></svg>'
)

FILE_ICONS = {".py": ("py", "\u25a0"), ".md": ("md", "\u2261"), ".json": ("json", "{}")}


def _icon_for(name: str) -> tuple[str, str]:
    for suffix, pair in FILE_ICONS.items():
        if name.endswith(suffix):
            return pair
    return ("", "\u25a1")


def _tabs(open_files: tuple[str, ...], active: str) -> str:
    out = []
    for rel in open_files:
        name = Path(rel).name
        cls = "tab on" if rel == active else "tab"
        out.append(
            f'<div class="{cls}"><span class="ico">&#9635;</span>{escape(name)}'
            '<span class="x">&#10005;</span></div>'
        )
    return f'<div class="tabs">{"".join(out)}</div>'


def _crumbs(rel_path: str) -> str:
    parts = ["spotter2", *Path(rel_path).parts]
    return (
        '<div class="crumbs">'
        + ' <span>\u203a</span> '.join(f"<span>{escape(p)}</span>" for p in parts)
        + "</div>"
    )


def _title_bar(rel_path: str) -> str:
    centre = f"spotter2  \u203a  {rel_path}  \u2014  Visual Studio Code"
    return (
        '<div class="title"><span>&#9776;</span><span>&#8592;</span><span>&#8594;</span>'
        f'<div class="title__center"><div class="title__box">{escape(centre)}</div></div>'
        '<div class="ctl"><span>&#8211;</span><span>&#9633;</span><span>&#10005;</span></div>'
        "</div>"
    )


STATUS_RIGHT = (
    "<span>Spaces: 4</span><span>UTF-8</span><span>LF</span><span>Python</span>"
    '<span class="chip">Cline</span>'
)


def _status(active_line: int, column: int) -> str:
    return (
        '<div class="status"><div class="l"><span>&#9906; main*</span>'
        "<span>&#10005; 0</span><span>&#9888; 0</span></div>"
        f'<div class="r"><span>Ln {active_line}, Col {column}</span>{STATUS_RIGHT}</div></div>'
    )


KIND_COLOR = {
    "py": "#4b8bbe",
    "json": "#cbcb41",
    "md": "#519aba",
    "txt": "#9d9d9d",
    "yaml": "#cb4b16",
    "toml": "#9d9d9d",
}

# (depth, kind, name, active, open?) - kind "folder" uses a disclosure chevron.
TREE = [
    (0, "folder", "SPOTTER2", False, True),
    (1, "folder", "backend", False, True),
    (2, "folder", "config", False, False),
    (2, "folder", "eld", False, True),
    (3, "folder", "services", False, True),
    (4, "py", "geocoding.py", False, None),
    (4, "py", "hos.py", False, None),
    (4, "py", "http.py", False, None),
    (4, "py", "logs.py", False, None),
    (4, "py", "planner.py", False, None),
    (4, "py", "routing.py", False, None),
    (3, "folder", "tests", False, True),
    (4, "py", "factories.py", False, None),
    (4, "py", "test_api.py", False, None),
    (4, "py", "test_hos.py", False, None),
    (4, "py", "test_logs.py", False, None),
    (3, "py", "__init__.py", False, None),
    (3, "py", "apps.py", False, None),
    (3, "py", "exceptions.py", False, None),
    (3, "py", "serializers.py", False, None),
    (3, "py", "urls.py", False, None),
    (3, "py", "views.py", False, None),
    (2, "py", "manage.py", False, None),
    (2, "txt", "requirements.txt", False, None),
    (2, "json", "vercel.json", False, None),
    (1, "folder", "frontend", False, False),
    (1, "md", "README.md", False, None),
    (1, "yaml", "render.yaml", False, None),
]


def _sidebar(active_row: str | None) -> str:
    rows = []
    for depth, kind, name, _on, opened in TREE:
        pad = 10 + depth * 13
        if kind == "folder":
            chev = "\u25be" if opened else "\u25b8"
            icon = f'<span class="chev">{chev}</span>'
            cls = "row folder"
        else:
            icon = f'<span class="ico" style="color:{KIND_COLOR.get(kind, "#9d9d9d")}">\u25a0</span>'
            cls = "row"
        if name == active_row:
            cls += " on"
        rows.append(
            f'<div class="{cls}" style="padding-left:{pad}px">{icon}'
            f"<span>{escape(name)}</span></div>"
        )
    return (
        '<div class="side"><div class="side__head"><span>Explorer</span><span>&#8943;</span></div>'
        f'<div class="side__body">{"".join(rows)}</div>'
        '<div class="stat"><span>Outline</span><span>Timeline</span></div></div>'
    )


def _panel(panel: dict) -> str:
    """The bottom panel (terminal) of the VS Code window."""
    tabs = "".join(
        f'<span class="{"on" if on else ""}">{escape(name)}</span>'
        for name, on in panel.get("tabs", ())
    )
    lines = "".join(
        f'<span class="{cls}">{escape(text)}</span>\n' for cls, text in panel["lines"]
    )
    return (
        f'<div class="panel"><div class="panel__tabs">{tabs}</div>'
        f'<div class="panel__body">{lines}</div></div>'
    )


def vscode_frame(
    *,
    caption_text: str,
    cursor_xy: tuple[int, int],
    rel_path: str,
    open_files: tuple[str, ...] = (),
    scroll: int = 0,
    highlight: tuple[int, ...] = (),
    active: int | None = None,
    column: int = 5,
    panel: dict | None = None,
) -> str:
    """A full 1920x1080 frame of the VS Code window showing ``rel_path``."""
    lines = (ROOT / rel_path).read_text(encoding="utf-8").splitlines()
    total = len(lines)
    visible = EDITOR_VISIBLE_PANEL if panel else EDITOR_VISIBLE
    offset = max(0, min(scroll, max(0, total - 8)))

    gutter = "\n".join(str(n) for n in range(offset + 1, total + 1))
    body = escape("\n".join(lines))

    bands = []
    for index in highlight:
        bands.append(
            f'<div class="band hit" style="top:{(index - 1) * LINE_HEIGHT}px"></div>'
        )
    if active:
        bands.append(
            f'<div class="band cur" style="top:{(active - 1) * LINE_HEIGHT}px"></div>'
        )

    view_top = (offset / max(total, 1)) * 100
    view_height = max(6.0, (visible / max(total, 1)) * 100)
    editor = (
        f"<div class=\"edit\">{_tabs(open_files or (rel_path,), rel_path)}{_crumbs(rel_path)}"
        f'<div class="codewrap"><div class="scroller" '
        f'style="transform:translateY(-{offset * LINE_HEIGHT}px)">'
        f'<div class="codepane"><pre class="gutter">{gutter}</pre>'
        f'<pre class="code"><code class="language-python">{body}</code></pre></div>'
        f'{"".join(bands)}</div>'
        f'<div class="minimap"><pre><code class="language-python">{body}</code></pre>'
        f'<div class="vp" style="top:{view_top}%;height:{view_height}%"></div></div>'
        "</div></div>"
    )

    window = (
        f'<div class="win" style="left:{VSCODE_X}px;top:{VSCODE_Y}px;'
        f'width:{VSCODE_W}px;height:{VSCODE_H}px">'
        f'{_title_bar(rel_path)}'
        f'<div class="body"><div class="activity">{ACTIVITY}</div>'
        f'{_sidebar(Path(rel_path).name)}{editor}</div>'
        f'{_panel(panel) if panel else ""}'
        f'{_status(active or offset + 1, column)}'
        "</div>"
    )
    return page(
        VSCODE_CSS,
        window + cursor(*cursor_xy) + caption(caption_text),
    )


EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")


def shoot(html: str, out_png: Path, *, workdir: Path) -> Path:
    """Photograph one 1920x1080 frame with headless Edge."""
    workdir.mkdir(parents=True, exist_ok=True)
    page_path = workdir / f"{out_png.stem}.html"
    page_path.write_text(html, encoding="utf-8")
    out_png.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            str(EDGE),
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            "--allow-file-access-from-files",
            "--force-device-scale-factor=1",
            f"--window-size={WIDTH},{HEIGHT}",
            "--virtual-time-budget=8000",
            f"--screenshot={out_png}",
            page_path.as_uri(),
        ],
        capture_output=True,
        check=False,
    )
    if not out_png.exists():
        raise RuntimeError(
            f"Edge produced no frame for {out_png.name}: "
            f"{result.stderr.decode(errors='replace')[-400:]}"
        )
    return out_png


if __name__ == "__main__":  # pragma: no cover - manual smoke test
    build = Path(__file__).resolve().parent / "build"
    demo = vscode_frame(
        caption_text="Smoke test: the HOS rule engine, as rendered for the video.",
        cursor_xy=(1460, 470),
        rel_path="backend/eld/services/hos.py",
        open_files=("backend/eld/services/hos.py", "backend/eld/services/logs.py"),
        scroll=286,
        highlight=(295, 296, 297, 298, 299),
        active=302,
    )
    print(shoot(demo, build / "smoke-vscode.png", workdir=build))


def browser_frame(
    *,
    caption_text: str,
    cursor_xy: tuple[int, int],
    image: str,
    title: str = "Spotter ELD - Trip planner & automatic driver's daily log sheets",
    url: str = "127.0.0.1:5173",
    contain: bool = False,
    zoom: float = 1.0,
    focus: str = "50% 50%",
) -> str:
    """A full 1920x1080 frame of the app inside a dark Edge window."""
    style = ""
    if zoom != 1.0:
        style = f' style="transform:scale({zoom});transform-origin:{focus}"'
    inner = (
        '<div class="bstrip"><div class="btab"><span class="fav"></span>'
        f'{escape(title)}<span class="x">&#10005;</span></div>'
        '<div class="bplus">+</div>'
        '<div class="bwin__ctl"><span>&#8211;</span><span>&#9633;</span>'
        '<span>&#10005;</span></div></div>'
        '<div class="bbar"><div class="bnav">&#8592;</div><div class="bnav">&#8594;</div>'
        '<div class="bnav">&#8635;</div>'
        f'<div class="burl">{LOCK}<span>{escape(url)}</span></div>'
        '<div class="bnav">&#9734;</div><div class="bnav">&#8942;</div></div>'
        f'<div class="bpage{" contain" if contain else ""}">'
        f'<img src="{_uri(ROOT / image)}" alt=""{style}></div>'
    )
    window = (
        f'<div class="win bwin" style="left:{BROWSER_X}px;top:{BROWSER_Y}px;'
        f'width:{BROWSER_W}px;height:{BROWSER_H}px">{inner}</div>'
    )
    return page(
        VSCODE_CSS + BROWSER_CSS,
        window + cursor(*cursor_xy) + caption(caption_text),
        highlight=False,
    )




