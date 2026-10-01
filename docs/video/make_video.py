"""Build the Spotter 2 walkthrough video.

    python make_video.py            # render every frame, encode the MP4
    python make_video.py --frames   # render frames only (fast to inspect)

The shot list below is the single source of truth: each entry names a caption
cue and a duration, so the burned-in subtitles, the .srt sidecar and the video
itself can never drift apart.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from render import browser_frame, shoot, vscode_frame

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
BUILD = HERE / "build"
APP = HERE / "assets" / "app"
OUT_MP4 = HERE / "spotter2-walkthrough.mp4"
OUT_SRT = HERE / "spotter2-walkthrough.srt"

FFMPEG = shutil.which("ffmpeg") or "ffmpeg"
FFPROBE = shutil.which("ffprobe") or "ffprobe"

# --------------------------------------------------------------------------- #
# Cues.  Keep each under ~140 characters so the caption stays one line.
# --------------------------------------------------------------------------- #
CUES: dict[str, str] = {
    "intro": "This is Spotter 2: a trip planner that turns three locations and a "
    "cycle-hours figure into a legal route and a full set of driver's daily logs.",
    "form": "Everything starts in the trip form - and the location fields are live. "
    "Typing three characters queries the backend's place search, so you pick a real "
    "geocoded place.",
    "form2": "Three inputs - where the truck is now, the pickup and the drop-off - "
    "plus the hours already burned in the 70-hour cycle.",
    "form3": "An optional panel pins the departure time and fills the log header: "
    "carrier, tractor, trailer, shipper, commodity and load ID.",
    "submit": "One click posts the trip to the API.",
    "result": "A few seconds later the whole run comes back - miles, arrival time "
    "and a legality summary.",
    "map": "The road route itself comes from OSRM, drawn over OpenStreetMap tiles.",
    "map2": "Every required stop is pinned on it - rests, fuel, pickup and drop-off - "
    "at the exact mile it has to happen.",
    "itinerary": "The itinerary is the human-readable version of that same plan: "
    "each stop with its time, place and the reason for it.",
    "summary": "Summary tiles keep the numbers honest, including how much of the "
    "70-hour cycle has been eaten.",
    "logs": "But the real deliverable is the log book - a fully drawn FMCSA daily "
    "log sheet for every calendar day of the trip.",
    "sheet1": "A 24-hour grid, duty-status lines drawn to the quarter hour, brackets, "
    "numbered remark flags, per-line totals and the seven-day recap.",
    "sheet2": "One sheet per day. Day two carries the tail of the run and closes out "
    "the cycle.",
    "code1": "So how does it work? The backend is Django with DRF, and the heart of "
    "it is the hours-of-service engine.",
    "code2": "The limits live in one place - eleven driving hours, fourteen on-duty "
    "hours, a thirty-minute break and the seventy-hour cycle - and every driving "
    "chunk is capped by the tightest of them.",
    "code3": "The simulator walks the route leg by leg, and before each chunk it "
    "asks what the law requires next: a break, a reset, fuel, or a 34-hour restart.",
    "code4": "One subtlety the tests forced out - on-duty blocks are indivisible, so "
    "they need their own cycle look-ahead or a block could slip past seventy hours.",
    "code5": "A second pass turns those segments into 24-hour grids, clipping each "
    "day at midnight.",
    "code6": "Remarks follow the regulation: one numbered flag per duty-status "
    "change, and none for a carry-over block that only squares the grid.",
    "code7": "The planner wires geocoding, routing and the log builder together into "
    "a single response.",
    "code8": "Routing calls OSRM and interpolates position along the returned "
    "polyline, so any mile marker maps to a real coordinate.",
    "code9": "And every one of these rules is pinned by a test - the eleven hours, "
    "the fourteen, the break, the reset and the fuel interval.",
    "test1": "Forty-three tests covering the engine, the log sheets and the API "
    "surface - all offline, no network.",
    "test2": "And the end-to-end contract check - six hundred and thirty-three "
    "assertions against a real six-hundred-mile trip - passes too.",
    "close": "Spotter 2: one POST, a legal route, and finished log sheets you could "
    "hand to an inspector.",
}

# --------------------------------------------------------------------------- #
# Terminal payloads, transcribed from real runs on this machine.
# --------------------------------------------------------------------------- #
PY = r"..\spotter2\Scripts\python.exe"
PROMPT = r"PS C:\projects\assessments\spotter2\backend> "

TEST_PANEL = {
    "tabs": (("PROBLEMS", 0), ("OUTPUT", 0), ("DEBUG CONSOLE", 0), ("TERMINAL", 1)),
    "lines": (
        ("m", PROMPT + PY + " manage.py test eld"),
        ("", ""),
        ("", "Found 43 test(s)."),
        ("d", "System check identified no issues (0 silenced)."),
        ("d", "." * 43),
        ("", "-" * 70),
        ("", "Ran 43 tests in 0.019s"),
        ("", ""),
        ("p", "OK"),
    ),
}

CONTRACT_PANEL = {
    "tabs": (("PROBLEMS", 0), ("OUTPUT", 0), ("DEBUG CONSOLE", 0), ("TERMINAL", 1)),
    "lines": (
        ("m", PROMPT + PY + r" scripts\verify_contract.py"),
        ("", ""),
        ("", "checks run   : 633"),
        ("d", "log sheets   : 2"),
        ("d", "stops        : 6"),
        ("d", "miles        : 672.3"),
        ("d", "fuel/breaks/resets: 0/0/1"),
        ("d", "  day 1 2026-10-01  drive 11:00  onduty 1:30  off 7:30  sb 4:00  "
              "total 24:00  miles 573.0  remarks 6"),
        ("d", "  day 2 2026-10-02  drive  1:53  onduty 2:00  off 15:07  sb 5:00  "
              "total 24:00  miles  99.2  remarks 5"),
        ("", ""),
        ("p", "ALL CHECKS PASSED"),
    ),
}


def app(img: str, cue: str, secs: float, *, zoom: float = 1.0,
        focus: str = "50% 50%", contain: bool = False,
        cursor: tuple[int, int] = (1240, 620)) -> dict:
    """A shot of the browser running the app."""
    return {
        "html": browser_frame(
            caption_text=CUES[cue],
            cursor_xy=cursor,
            image=str(APP / f"{img}.png"),
            contain=contain,
            zoom=zoom,
            focus=focus,
        ),
        "cue": cue,
        "secs": secs,
    }


def code(rel: str, cue: str, secs: float, *, scroll: int = 0,
         highlight: tuple[int, ...] = (), active: int | None = None,
         panel: dict | None = None, open_files: tuple[str, ...] = (),
         cursor: tuple[int, int] = (1500, 540), column: int = 5) -> dict:
    """A shot of a source file open in VS Code."""
    return {
        "html": vscode_frame(
            caption_text=CUES[cue],
            cursor_xy=cursor,
            rel_path=rel,
            open_files=open_files or (rel,),
            scroll=scroll,
            highlight=highlight,
            active=active,
            column=column,
            panel=panel,
        ),
        "cue": cue,
        "secs": secs,
    }


HOS = "backend/eld/services/hos.py"
LOGS = "backend/eld/services/logs.py"
PLANNER = "backend/eld/services/planner.py"
ROUTING = "backend/eld/services/routing.py"
TESTS = "backend/eld/tests/test_hos.py"

# --------------------------------------------------------------------------- #
# The shot list.  Order is the edit order; ``secs`` is screen time.
# --------------------------------------------------------------------------- #
SHOTS: list[dict] = [
    # --- Act 1: the product -------------------------------------------------
    app("01-landing-empty-state", "intro", 9.0),
    app("02-autocomplete-dropdown", "form", 8.0),
    app("03-form-filled", "form2", 7.0),
    app("03b-departure-and-header", "form3", 7.0),
    app("04-loading-spinner", "submit", 4.0),
    app("05-route-overview", "result", 10.0),
    app("06-map-canvas", "map", 6.0, zoom=1.0),
    app("06-map-canvas", "map", 5.0, zoom=1.35, focus="52% 46%"),
    app("06-map-canvas", "map2", 5.0, zoom=1.8, focus="52% 46%"),
    app("07-stops-top", "itinerary", 10.0),
    app("08-stops-more", "itinerary", 8.0),
    app("09-summary-stats", "summary", 8.0),
    app("10-logbook-top", "logs", 10.0),
    app("11-sheet-day1", "sheet1", 11.0, contain=True),
    app("12-sheet-day2", "sheet2", 8.0, contain=True),
    # --- Act 2: the code ----------------------------------------------------
    code(HOS, "code1", 10.0, scroll=42, active=49, open_files=(HOS, LOGS)),
    code(HOS, "code2", 11.0, scroll=272, active=276,
         highlight=(279, 280, 281, 282, 283), open_files=(HOS, LOGS)),
    code(HOS, "code3", 12.0, scroll=368, active=369,
         highlight=(383, 390, 393, 398), open_files=(HOS, LOGS)),
    code(HOS, "code4", 11.0, scroll=295, active=302,
         highlight=(312, 313), open_files=(HOS, LOGS)),
    code(LOGS, "code5", 10.0, scroll=244, active=250, open_files=(HOS, LOGS)),
    code(LOGS, "code6", 9.0, scroll=300, active=301,
         highlight=(306, 308, 311, 312), open_files=(HOS, LOGS)),
    code(PLANNER, "code7", 10.0, scroll=59, active=63,
         open_files=(PLANNER, HOS)),
    code(ROUTING, "code8", 9.0, scroll=126, active=137,
         open_files=(ROUTING, PLANNER)),
    code(TESTS, "code9", 11.0, scroll=20, active=24,
         highlight=(32, 44, 55), open_files=(HOS, TESTS)),
    # --- Act 3: the proof ---------------------------------------------------
    code(TESTS, "test1", 12.0, scroll=20, active=24, panel=TEST_PANEL,
         open_files=(TESTS,), cursor=(1320, 700)),
    code(TESTS, "test2", 10.0, scroll=119, active=123, panel=CONTRACT_PANEL,
         open_files=(TESTS,), cursor=(1320, 700)),
    app("05-route-overview", "close", 9.0),
]

FPS = 30


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


def _srt(shots: list[dict], durations: list[float]) -> str:
    """Merge consecutive shots that share a cue, then emit subtitle blocks."""
    blocks: list[tuple[float, float, str]] = []
    clock = 0.0
    for shot, secs in zip(shots, durations):
        text = CUES[shot["cue"]]
        if blocks and blocks[-1][2] == text:
            start, end, _ = blocks[-1]
            blocks[-1] = (start, end + secs, text)
        else:
            blocks.append((clock, clock + secs, text))
        clock += secs

    def stamp(value: float) -> str:
        ms = int(round(value * 1000))
        h, ms = divmod(ms, 3_600_000)
        m, ms = divmod(ms, 60_000)
        s, ms = divmod(ms, 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    out = []
    for i, (start, end, text) in enumerate(blocks, 1):
        out.append(f"{i}\n{stamp(start)} --> {stamp(end)}\n")
        out.append("\n".join(_wrap(text)) + "\n\n")
    return "".join(out)


def render_frames() -> list[Path]:
    BUILD.mkdir(parents=True, exist_ok=True)
    for stale in BUILD.glob("frame-*.png"):
        stale.unlink()
    paths: list[Path] = []
    for i, shot in enumerate(SHOTS, 1):
        png = BUILD / f"frame-{i:03d}.png"
        shoot(shot["html"], png, workdir=BUILD)
        paths.append(png)
        print(f"  [{i:2d}/{len(SHOTS)}] {png.name}  cue={shot['cue']}", flush=True)
    return paths


def encode(paths: list[Path], durations: list[float]) -> None:
    """Stitch the stills into an MP4 and attach the .srt as a soft track."""
    concat = BUILD / "concat.txt"
    lines: list[str] = []
    for png, secs in zip(paths, durations):
        lines.append(f"file '{png.as_posix()}'")
        lines.append(f"duration {secs:.3f}")
    lines.append(f"file '{paths[-1].as_posix()}'")
    concat.write_text("\n".join(lines) + "\n", encoding="utf-8")

    OUT_SRT.write_text(_srt(SHOTS, durations), encoding="utf-8")
    # Without an explicit -t the concat demuxer lets the duplicated final entry
    # inherit the previous duration, lengthening the film by one whole shot.
    total = sum(durations)
    out = subprocess.run(
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
    if out.returncode:
        sys.exit(f"ffmpeg failed:\n{out.stderr}")


def _probe(*args: str) -> str:
    return subprocess.run(
        [FFPROBE, "-v", "error", *args, str(OUT_MP4)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()


def verify() -> bool:
    """ffprobe the result - a video that is the wrong size or length is a bug."""
    duration = float(_probe("-show_entries", "format=duration", "-of", "csv=p=0"))
    video = _probe("-select_streams", "v:0", "-show_entries",
                   "stream=codec_name,width,height", "-of", "csv=p=0")
    subs = _probe("-select_streams", "s", "-show_entries",
                  "stream=codec_name", "-of", "csv=p=0")
    print(f"  video: {video}")
    print(f"  subs : {subs or '(none)'}")
    print(f"  len  : {duration:.1f}s")

    checks = [
        ("duration matches the shot list",
         abs(duration - sum(s["secs"] for s in SHOTS)) < 1.0,
         f"{duration:.1f}s"),
        ("duration between 180s and 300s", 180 <= duration <= 300,
         f"{duration:.1f}s"),
        ("resolution is 1920x1080", video.endswith("1920,1080"),
         video),
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
    ap.add_argument("--frames", action="store_true",
                    help="render frames only, skip the encode")
    ap.add_argument("--skip-render", action="store_true",
                    help="reuse the frames already in build/")
    args = ap.parse_args()

    durations = [shot["secs"] for shot in SHOTS]
    print(f"{len(SHOTS)} shots, {sum(durations):.1f}s of screen time")
    if args.skip_render:
        paths = [BUILD / f"frame-{i:03d}.png" for i in range(1, len(SHOTS) + 1)]
        missing = [p for p in paths if not p.exists()]
        if missing:
            sys.exit(f"missing frames: {[p.name for p in missing]}")
    else:
        paths = render_frames()
    if args.frames:
        return 0
    encode(paths, durations)
    print(f"\nwrote {OUT_MP4.relative_to(ROOT)}")
    print(f"wrote {OUT_SRT.relative_to(ROOT)}")
    return 0 if verify() else 1


if __name__ == "__main__":
    raise SystemExit(main())
