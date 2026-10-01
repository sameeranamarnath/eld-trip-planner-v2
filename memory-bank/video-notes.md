# Video Deliverable Notes

Deliverable: `docs/video/spotter2-walkthrough.mp4` — 1920x1080, 30fps, ~4 min, silent
H.264 + AAC, with burned-in subtitles for the user's voiceover.

## Decisions and rejected alternatives

| Decision | Alternative rejected | Why |
| --- | --- | --- |
| Backdrop = real wallpaper file fill-cropped | Screenshot the live desktop | Two other agents' VS Code chat windows are on screen; capturing them would leak third-party work |
| Code frames rendered as a VS Code (Dark Modern) replica in HTML | Drive the real VS Code window | Window position, theme and other agents' activity make it non-deterministic |
| Motion = extra frames at successive scroll offsets | ffmpeg `zoompan` over stills | `zoompan` rounds to integers and jitters visibly at 1080p |
| One headless-Edge launch per shot | Batch page + .NET cropping | Simpler, deterministic, and the batch path needs a giant PNG Edge may cap |
| Static cursor drawn into each shot | Interpolated cursor path | Piecewise overlay expressions are brittle; a placed cursor still reads as authentic |

## Shared-desktop safety

- Never stop a process we did not start. Only PIDs 27416 (Django) and 73048 (Vite) are ours.
- No minimising, focus-stealing or window manipulation on the shared desktop.

## Toolchain (verified)

- ffmpeg/ffprobe 9.0 full build (winget Gyan.FFmpeg).
- Edge: `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`.
- Fonts present: Consolas, Cascadia Mono, Segoe UI.
- Live dev servers: Django 127.0.0.1:8090, Vite 127.0.0.1:5173.
