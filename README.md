# gmi_queue

A tiny, **unofficial** command-line client for the GMI Cloud request-queue API (the endpoint behind the video/image/audio models in the GMI console). One file, Python 3 standard library only. Not affiliated with or endorsed by GMI Cloud.

It was written to drive a music-video pipeline (MiniMax H3 lip-sync, Wan 3.0) and has one safety rule: **it never spends money unless you pass `--yes`**; `submit` first prints the estimated cost.

## Setup
```sh
export GMI_API_KEY=...            # or put the key in ~/.config/gmi/key  (or ./.secrets/gmi.key)
```
The key is never printed or stored by the script.

## Use
```sh
python3 gmi_queue.py models wan                       # list model ids containing "wan"
python3 gmi_queue.py info wan3.0-video               # price info + description (use a model id from `models`)
python3 gmi_queue.py submit <model> payload.json      # prints the estimated cost, does NOT submit
python3 gmi_queue.py submit <model> payload.json --yes --out result.mp4   # submits, waits, downloads
python3 gmi_queue.py poll <request_id> --out result.mp4                   # resume waiting for an earlier request
```
`payload.json` is the model's input object, for example (Wan 3.0, image + audio to video):
```json
{"prompt": "close-up, she sings", "first_frame": "https://example.com/frame.png", "audio_url": "https://example.com/line.mp3",
 "duration": 4, "resolution": "720P", "ratio": "adaptive"}
```
Image and audio URLs must be public HTTP(S) URLs. Field names and allowed values differ per model, read `info <model>`.

## Notes
- The result URL is read from `outcome.video_url` or `outcome.media_urls[0].url`; other result shapes print the raw outcome instead of downloading.
- Wan 3.0 per-second rates in `WAN_RATES` are approximate, the live price field only shows the top tier. Check before large runs.
- API base can be overridden with `GMI_QUEUE_BASE`. The endpoint and its behaviour can change without notice.
