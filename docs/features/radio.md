# Radio and music

`Super + M`, the antenna button in the Control Center's media tile, **Radio & Music** in the launcher, and `desktop-radio` all open the Radio panel. It plays web radio stations and DJ sets, and it finds YouTube mixes and playlists. Everything plays in one mpv of its own, without a window unless you ask for video.

The `media` profile installs what it needs: `mpv`, `mpv-mpris` and `yt-dlp`, plus `ytfzf` on Arch. `mpv-mpris` puts that mpv on MPRIS, so the bar, the Control Center, the lock screen and the media keys show and control it like any other player. On Fedora `ytfzf` is not packaged, and search uses `yt-dlp` alone.

## The panel

- **Categories:** **All**, **Web radio** (streams only), one chip per category of the stations, **Saved** and **YouTube**. The text field filters the stations as you type.
- **Playing:** Enter or a click plays the highlighted item. On the item that is playing, it pauses or resumes. The box at the top shows the title (the stream's track title, read from mpv while the panel is open), the station, and previous, play/pause, next and stop.
- **Video:** the monitor button in the header turns mpv's video window on or off, for what plays now and what comes next. Without video, mpv fetches only the audio of a YouTube item. Turning video on then starts that item again with its picture: a video resumes where it was, and a playlist at the same item, from its beginning. A web radio has no video, so the button is off while one plays.
- **YouTube:** **YouTube**, or Enter when no station matches, searches YouTube with `ytfzf`, or with `yt-dlp` when `ytfzf` finds nothing or is missing. The chips under it pick all results, playlists only, or mixes and videos.
- **Saved:** the pin on a result saves it; the trash icon removes a saved item.

## Stations

The shipped stations are in `shell/.local/share/desktop/radio/stations.json` (linked to `~/.local/share/desktop/radio/stations.json`). That file holds `categories`, the order of the category chips, and `stations`. Each station has:

- `id`, and optionally `aliases`;
- `title` and `subtitle`;
- `category`;
- `kind`: `radio`, `youtube`, `playlist` or `file`, found from the URL when it is left out;
- `url`.

`~/.config/desktop/radio.json` is yours, outside the repository. Its `stations` use the same format: one with the `id` of a shipped station replaces it, any other adds to them, and a new category gets a chip after the shipped ones. Its `saved` list is what the panel pins, and the panel rewrites only that key.

```json
{
  "stations": [
    {"id": "fip", "title": "FIP", "category": "eclectic", "url": "https://icecast.radiofrance.fr/fip-midfi.mp3"}
  ]
}
```

Only `http://`, `https://` and `ytdl://` URLs and files on disk are played, whatever the item came from, and mpv receives the URL after `--`. Anything else is refused.

## From a terminal

`desktop-radio` with no argument toggles the panel. Other commands:

| Command | What it does |
| --- | --- |
| `desktop-radio ID` (or an alias) | Plays a station |
| `desktop-radio play ID\|URL [--video]` | Plays a station, a stream, a YouTube link or a file |
| `desktop-radio toggle`, `stop`, `next`, `previous` | Controls playback |
| `desktop-radio video [on\|off\|toggle]` | Turns the video window on or off |
| `desktop-radio search QUERY [all\|playlist\|video]` | Searches YouTube |
| `desktop-radio list`, `status` | Prints the stations and the state as JSON |

These commands act only on the radio's own mpv, through `$XDG_RUNTIME_DIR/desktop-shell/radio-mpv.sock`. Another mpv you started yourself is never paused, skipped or closed. The state is kept in `radio.json` next to that socket.
