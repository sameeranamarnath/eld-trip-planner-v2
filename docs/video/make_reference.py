"""Build the Loom-style reference video for the walkthrough recording.

This is NOT the submission video - it is the rehearsal target. Every beat carries
the exact line to say, the shot to be on, and how long to stay there, so the real
Loom can be recorded in one take against it. It uses the same stills pipeline as
the main walkthrough (HTML -> headless Edge -> ffmpeg) with a Loom-style overlay:
webcam bubble, chapter tag, elapsed clock and a progress bar.

    python make_reference.py            # render every frame, encode the MP4
    python make_reference.py --frames   # render frames only (fast to inspect)
    python make_reference.py --skip-render

The beat table is the single source of truth and matches
`docs/recording/voiceover-script.md` timecode for timecode.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from html import escape
from pathlib import Path

from render import browser_frame, shoot, vscode_frame

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
BUILD = HERE / "build"
APP = HERE / "assets" / "app"
OUT_MP4 = HERE / "spotter2-loom-reference.mp4"
OUT_SRT = HERE / "spotter2-loom-reference.srt"

FFMPEG = shutil.which("ffmpeg") or "ffmpeg"
FFPROBE = shutil.which("ffprobe") or "ffprobe"
FPS = 30


@dataclass
class Beat:
    """One rehearsal beat: what is on screen, and the words to say over it."""

    at: str  # display timecode, kept in step with the voiceover script
    secs: float
    chapter: str
    line: str
    kind: str = "app"
    shot: str = ""
    zoom: float = 1.0
    focus: str = "50% 50%"
    scroll: int = 0
    highlight: tuple[int, ...] = ()
    active: int | None = None
    cursor: tuple[int, int] = (1180, 640)
    extra: dict = field(default_factory=dict)


BEATS: list[Beat] = [
    Beat(
        at="00:00", secs=9, chapter="Intro", shot="01-landing-empty-state",
        cursor=(1180, 700),
        line="Hi, I'm Amar. This is Spotter ELD - a Django and React app that takes four trip "
             "inputs and returns a legal route plus a filled-out FMCSA daily log for every day "
             "of the trip.",
    ),
    Beat(
        at="00:09", secs=13, chapter="The four inputs", shot="03-form-filled",
        zoom=1.12, focus="30% 45%", cursor=(430, 470),
        line="The four inputs are exactly what the brief asks for: current location, pickup, "
             "drop-off, and hours already used in the seventy-hour, eight-day cycle.",
    ),
    Beat(
        at="00:22", secs=11, chapter="Real places", shot="02-autocomplete-dropdown",
        zoom=1.22, focus="28% 62%", cursor=(430, 560),
        line="Locations autocomplete from OpenStreetMap, so you are choosing a real dispatchable "
             "city. I rank city and town results above counties and states, because the middle "
             "of Tennessee is not a place a truck can be sent to.",
    ),
    Beat(
        at="00:33", secs=10, chapter="Form header", shot="03b-departure-and-header",
        zoom=1.1, focus="30% 70%", cursor=(430, 700),
        line="Optional departure time, and the driver and carrier fields - driver number, "
             "tractor and trailer, shipper, commodity - so the drawn sheet matches the form it "
             "replaces.",
    ),
    Beat(
        at="00:43", secs=7, chapter="Stateless planning", shot="04-loading-spinner",
        cursor=(900, 560),
        line="Planning here is pure computation with no database, which is why the backend "
             "deploys anywhere as a stateless function.",
    ),
    Beat(
        at="00:50", secs=15, chapter="The plan at a glance", shot="05-route-overview",
        cursor=(900, 300),
        line="Six hundred and seventy-two miles, two log sheets, one ten-hour reset. The summary "
             "tiles are the whole plan at a glance: driving hours, cycle hours used, fuel stops, "
             "breaks and rests.",
    ),
    Beat(
        at="01:05", secs=12, chapter="Route on the map", shot="06-map-canvas",
        cursor=(700, 620),
        line="The route comes from OSRM over OpenStreetMap tiles - both free and keyless. Every "
             "stop, rest and fuel stop is placed on the route itself, not offset next to it.",
    ),
    Beat(
        at="01:17", secs=12, chapter="Stops and rests", shot="07-stops-top",
        zoom=1.15, focus="78% 40%", cursor=(1420, 420),
        line="Each stop is a real duty-status change with an arrival time, a duration and a mile "
             "marker, and it is the same data the log grid is drawn from. One source of truth.",
    ),
    Beat(
        at="01:29", secs=17, chapter="Route instructions", shot="14-directions-top",
        cursor=(900, 700),
        line="Route instructions are their own output in the brief, so they are their own tab: "
             "fifty-seven turn-by-turn steps with maneuvers, distances, durations and running "
             "mileage. OSRM returns machine-readable maneuver codes, so the backend writes the "
             "sentences.",
    ),
    Beat(
        at="01:46", secs=15, chapter="The drawn log sheet", shot="11-sheet-day1",
        cursor=(900, 620),
        line="Now the part that matters. Four duty-status lines on a fifteen-minute grid, brackets "
             "where the truck sat still, a numbered remark flag at every status change with the "
             "city and state, per-line totals, and the seventy-hour recap.",
    ),
    Beat(
        at="02:01", secs=12, chapter="One sheet per day", shot="12-sheet-day2",
        cursor=(900, 620),
        line="Longer trips just add sheets. Day two totals twenty-four hours again, and carries "
             "the recap forward so the cycle maths never gets lost between pages.",
    ),
    Beat(
        at="02:13", secs=9, chapter="Print or PDF", shot="10-logbook-top",
        cursor=(1560, 840),
        line="Every sheet prints or saves as a PDF at one clean landscape page per day - real "
             "vector text, not a screenshot of a table.",
    ),
    Beat(
        at="02:22", secs=9, chapter="The rulebook", shot="16-hos-rules",
        cursor=(900, 500),
        line="The rules dialog lists every limit the planner enforces with the paragraph each one "
             "comes from: the eleven-hour limit, the fourteen-hour window, the thirty-minute "
             "break, the seventy-hour cycle.",
    ),
    Beat(
        at="02:31", secs=7, chapter="Dark theme", shot="17-dark-directions",
        cursor=(900, 700),
        line="And a dark theme. The log sheet deliberately stays white in both, because it is "
             "paper.",
    ),
    Beat(
        at="02:38", secs=14, chapter="Code: the HOS engine", kind="code",
        shot="backend/eld/services/hos.py", scroll=286,
        highlight=(295, 296, 297, 298, 299), active=302, cursor=(980, 470),
        line="Now the code. The HOS engine is deliberately pure: give it a route and a start time "
             "and it returns duty segments. Every tunable rule lives in one dataclass at the top "
             "of the file, so the regulation can be read against it line by line.",
    ),
    Beat(
        at="02:52", secs=13, chapter="Code: the log builder", kind="code",
        shot="backend/eld/services/logs.py", scroll=300,
        highlight=(330, 331, 332, 333, 334, 335, 336, 337), active=338, cursor=(980, 470),
        line="A separate builder slices that stream into one sheet per calendar day. Keeping it "
             "separate means the grid arithmetic - totals, remark flags, the seventy-hour recap - "
             "is unit-testable without ever opening a browser.",
    ),
    Beat(
        at="03:05", secs=11, chapter="Code: routing", kind="code",
        shot="backend/eld/services/routing.py", scroll=280,
        highlight=(74, 75, 76, 77, 78, 79, 80, 81), active=84, cursor=(980, 470),
        line="The router turns OSRM's machine-readable maneuver codes into plain-language "
             "instructions, and rescales the polyline so the mile markers agree with the "
             "provider's own distance.",
    ),
    Beat(
        at="03:16", secs=12, chapter="Code: the sheet is SVG", kind="code",
        shot="frontend/src/components/LogSheet.jsx", scroll=76,
        highlight=(77, 78, 79, 80, 81, 82, 83), active=83, cursor=(980, 470),
        line="The sheet itself is SVG generated in React, which is why it prints crisply, and why "
             "the grid, the brackets and the numbered remark flags are all real vector output "
             "rather than an image.",
    ),
    Beat(
        at="03:28", secs=12, chapter="Code: the tests", kind="code",
        shot="backend/eld/tests/test_hos.py", scroll=0,
        highlight=(1, 2, 3, 4, 5, 6),
        active=7, cursor=(980, 470),
        line="Fifty-two offline tests cover the HOS arithmetic and the geocoding ranking. On top "
             "of that a contract script replays a 672-mile trip and asserts 633 fields against "
             "the running stack.",
    ),
    Beat(
        at="03:40", secs=9, chapter="No API keys", kind="code",
        shot="frontend/vite.config.js", scroll=0, active=13, highlight=(11, 12, 13),
        cursor=(980, 400),
        line="There are no API keys anywhere - OSRM, Nominatim and Photon all run keyless, so a "
             "fresh clone works on the first try.",
    ),
    Beat(
        at="03:49", secs=10, chapter="Ready to hand over", shot="18-dark-logbook",
        cursor=(900, 700),
        line="So the app plans a legal trip, draws the logs, and hands them to a driver as a PDF "
             "that looks like the form it replaces.",
    ),
    Beat(
        at="03:59", secs=11, chapter="Wrap up", shot="01-landing-empty-state",
        cursor=(1180, 700),
        line="The repository and the live link are in the description below. Thanks for watching.",
    ),
]

# --------------------------------------------------------------------------- #
# Loom furniture.  The bubble is deliberately labelled: this is a rehearsal
# target, not a webcam recording, and pretending otherwise would be confusing.
# --------------------------------------------------------------------------- #

LOOM_CSS = """
.loom-bar { position:absolute; z-index:80; left:0; right:0; top:0; height:5px;
  background:rgba(255,255,255,.16); }
.loom-bar i { display:block; height:100%; background:linear-gradient(90deg,#5b8cff,#8f6bff); }
.loom-tag { position:absolute; z-index:80; left:0; top:5px; padding:8px 16px 8px 46px;
  background:rgba(10,12,18,.84); border-bottom-right-radius:10px;
  color:#e8eef8; font-size:12px; font-weight:700; letter-spacing:.08em; text-transform:uppercase; }
.loom-clock { position:absolute; z-index:80; right:16px; top:15px; padding:6px 13px;
  border-radius:999px; background:rgba(10,12,18,.84); color:#e8eef8; font-size:12px;
  font-weight:700; font-variant-numeric:tabular-nums; }
.loom-bubble { position:absolute; z-index:80; left:36px; bottom:118px; width:170px; height:170px;
  border-radius:50%; background:linear-gradient(150deg,#22304d,#0d1526);
  border:3px solid rgba(255,255,255,.55); box-shadow:0 16px 36px rgba(0,0,0,.55);
  display:flex; flex-direction:column; align-items:center; justify-content:center; gap:7px;
  color:#dbe4f5; font-size:11px; font-weight:800; letter-spacing:.06em; text-align:center; }
.loom-bubble .dot { width:10px; height:10px; border-radius:50%; background:#ff5a5f;
  box-shadow:0 0 12px #ff5a5f; }
.loom-bubble small { font-weight:600; color:#93a2bb; font-size:9.5px; letter-spacing:.02em; }
"""


def _clock(seconds: float) -> str:
    total = int(round(seconds))
    return f"{total // 60}:{total % 60:02d}"


def _overlay(*, elapsed: float, total: float, chapter: str) -> str:
    percent = min(100.0, (elapsed / total) * 100.0) if total else 0.0
    return (
        f"<style>{LOOM_CSS}</style>"
        f'<div class="loom-bar"><i style="width:{percent:.2f}%"></i></div>'
        f'<div class="loom-tag">{escape(chapter)}</div>'
        f'<div class="loom-clock">{_clock(elapsed)} / {_clock(total)}</div>'
        '<div class="loom-bubble"><span class="dot"></span>YOUR WEBCAM'
        "<small>bottom-left, medium</small></div>"
    )


def _app_image(name: str) -> str:
    """Path to a captured app screenshot, relative to the repo root."""
    return (APP / f"{name}.png").relative_to(ROOT).as_posix()


def frame_for(beat: Beat, *, elapsed: float, total: float) -> str:
    """One 1920x1080 frame: the screen content plus the Loom furniture."""
    if beat.kind == "code":
        html = vscode_frame(
            caption_text=beat.line,
            cursor_xy=beat.cursor,
            rel_path=beat.shot,
            open_files=(beat.shot,),
            scroll=beat.scroll,
            highlight=beat.highlight,
            active=beat.active,
        )
    else:
        html = browser_frame(
            caption_text=beat.line,
            cursor_xy=beat.cursor,
            image=_app_image(beat.shot),
            zoom=beat.zoom,
            focus=beat.focus,
        )
    overlay = _overlay(elapsed=elapsed, total=total, chapter=beat.chapter)
    return html.replace("</body>", overlay + "</body>")


def timeline() -> list[tuple[Beat, float]]:
    """Pair every beat with the elapsed time it starts at."""
    elapsed = 0.0
    paired: list[tuple[Beat, float]] = []
    for beat in BEATS:
        paired.append((beat, elapsed))
        elapsed += beat.secs
    return paired


# The assessment allows 3-5 minutes; the beat list targets 4:10 to leave headroom.
MAX_SECONDS = 300


def _wrap(text: str, width: int = 78) -> list[str]:
    """Greedy wrap for the .srt sidecar."""
    words, lines, current = text.split(), [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) > width and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def _srt() -> str:
    """One subtitle block per beat - this doubles as the read-along script."""
    def stamp(value: float) -> str:
        ms = int(round(value * 1000))
        h, ms = divmod(ms, 3_600_000)
        m, ms = divmod(ms, 60_000)
        s, ms = divmod(ms, 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    out: list[str] = []
    for index, (beat, start) in enumerate(timeline(), 1):
        out.append(f"{index}\n{stamp(start)} --> {stamp(start + beat.secs)}\n")
        out.append("\n".join(_wrap(beat.line)) + "\n\n")
    return "".join(out)


def render_frames() -> list[Path]:
    BUILD.mkdir(parents=True, exist_ok=True)
    for stale in BUILD.glob("ref-*.png"):
        stale.unlink()
    total = sum(beat.secs for beat in BEATS)
    paths: list[Path] = []
    for index, (beat, elapsed) in enumerate(timeline(), 1):
        png = BUILD / f"ref-{index:03d}.png"
        shoot(frame_for(beat, elapsed=elapsed, total=total), png, workdir=BUILD)
        paths.append(png)
        print(f"  [{index:2d}/{len(BEATS)}] {beat.at}  {png.name}  {beat.chapter}", flush=True)
    return paths


def encode(paths: list[Path]) -> None:
    """Stitch the stills into an MP4 and attach the narration as a soft track."""
    concat = BUILD / "ref-concat.txt"
    lines: list[str] = []
    for png, beat in zip(paths, BEATS):
        lines.append(f"file '{png.as_posix()}'")
        lines.append(f"duration {beat.secs:.3f}")
    lines.append(f"file '{paths[-1].as_posix()}'")
    concat.write_text("\n".join(lines) + "\n", encoding="utf-8")

    OUT_SRT.write_text(_srt(), encoding="utf-8")
    total = sum(beat.secs for beat in BEATS)
    # The explicit -t matters: without it the duplicated final concat entry
    # inherits the previous duration and the film gains a whole extra beat.
    result = subprocess.run(
        [FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
         "-f", "concat", "-safe", "0", "-i", str(concat),
         "-i", str(OUT_SRT),
         "-map", "0:v:0", "-map", "1:0",
         "-vf", f"fps={FPS},format=yuv420p",
         "-c:v", "libx264", "-crf", "18", "-preset", "medium",
         "-c:s", "mov_text", "-metadata:s:s:0", "language=eng",
         "-t", f"{total:.3f}",
         "-movflags", "+faststart", str(OUT_MP4)],
        capture_output=True, text=True,
    )
    if result.returncode:
        sys.exit(f"ffmpeg failed:\n{result.stderr}")


def _probe(*args: str) -> str:
    return subprocess.run(
        [FFPROBE, "-v", "error", *args, str(OUT_MP4)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()


def verify() -> bool:
    """ffprobe the result - a reference of the wrong length wastes a rehearsal."""
    duration = float(_probe("-show_entries", "format=duration", "-of", "csv=p=0"))
    video = _probe("-select_streams", "v:0", "-show_entries",
                   "stream=codec_name,width,height", "-of", "csv=p=0")
    subs = _probe("-select_streams", "s", "-show_entries",
                  "stream=codec_name", "-of", "csv=p=0")
    total = sum(beat.secs for beat in BEATS)
    print(f"  video: {video}")
    print(f"  subs : {subs or '(none)'}")
    print(f"  len  : {duration:.1f}s ({_clock(duration)}) over {len(BEATS)} beats")

    checks = [
        ("duration matches the beat list", abs(duration - total) < 1.0, f"{duration:.1f}s"),
        ("duration inside the 3-5 minute brief",
         180 <= duration <= MAX_SECONDS, f"{duration:.1f}s"),
        ("resolution is 1920x1080", video.endswith("1920,1080"), video),
        ("has a subtitle track", "mov_text" in subs, subs or "(none)"),
        ("file is not empty", OUT_MP4.stat().st_size > 500_000,
         f"{OUT_MP4.stat().st_size / 1e6:.1f} MB"),
    ]
    ok = True
    for name, passed, detail in checks:
        print(f"  {'PASS' if passed else 'FAIL'}  {name}  ({detail})")
        ok = ok and passed
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--frames", action="store_true", help="render frames only")
    ap.add_argument("--skip-render", action="store_true", help="reuse rendered frames")
    args = ap.parse_args()

    total = sum(beat.secs for beat in BEATS)
    print(f"{len(BEATS)} beats, {total:.1f}s of screen time ({_clock(total)})")
    if args.skip_render:
        paths = [BUILD / f"ref-{i:03d}.png" for i in range(1, len(BEATS) + 1)]
        missing = [p.name for p in paths if not p.exists()]
        if missing:
            sys.exit(f"missing frames: {missing}")
    else:
        paths = render_frames()
    if args.frames:
        return 0
    encode(paths)
    print(f"\nwrote {OUT_MP4.relative_to(ROOT)}")
    print(f"wrote {OUT_SRT.relative_to(ROOT)}")
    return 0 if verify() else 1


if __name__ == "__main__":
    raise SystemExit(main())
