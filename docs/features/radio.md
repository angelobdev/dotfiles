# Radio and music

`Super + M`, the antenna button in the Control Center's media tile, **Radio & Music** in the launcher, and `desktop-radio` all open the Radio panel. It plays web radio stations and DJ sets, and it finds YouTube mixes and playlists. Sound plays in one mpv of its own, with no window, and video shows in the panel itself.

The `radio` profile installs what it needs: `mpv`, `mpv-mpris`, `yt-dlp` and Qt Multimedia (`qt6-qtmultimedia`; on Arch `qt6-multimedia` with its FFmpeg backend), plus `ytfzf` on Arch. `mpv-mpris` puts that mpv on MPRIS, so the bar, the Control Center, the lock screen and the media keys show and control it like any other player. On Fedora `ytfzf` is not packaged, and search uses `yt-dlp` alone.

## The panel

From top to bottom:

1. **Header:** the title, the video button and close.
2. **Content:** search and the list, or, with video on, the picture of what plays.
3. **Controls:** what plays now, always there. The title is the stream's track title, read from mpv while the panel is open, and the station below it. The buttons are previous and next (playlists), play/pause and stop.
4. **Footer:** the keys to use, or what went wrong.

The list:

- **Categories:** **All**, **Web radio** (streams only), one chip per category of the stations, **Saved** and **YouTube**. The text field filters the stations as you type.
- **Playing:** Enter or a click plays the highlighted item. On the item that is playing, it pauses or resumes.
- **YouTube:** **YouTube**, or Enter when no station matches, searches YouTube with `ytfzf`, or with `yt-dlp` when `ytfzf` finds nothing or is missing. The chips under it pick all results, playlists only, or mixes and videos.
- **Saved:** the pin on a result saves it; the trash icon removes a saved item.

**Video.** The monitor button is on for a YouTube item or a file, never for a web radio, which has no picture. It puts the video in place of the list, and search is off meanwhile.

- **The picture:** `radio.py video` asks yt-dlp for the picture alone, the best H.264 stream up to 720p, and the panel plays it muted through Qt Multimedia. YouTube no longer serves a stream with both sound and picture.
- **The sound:** mpv keeps playing it, so the bar, the lock screen and the media keys go on showing and controlling it.
- **Keeping in step:** with the video open, the panel reads mpv's position every second. The picture follows mpv's pause, and jumps when it drifts more than 0.6 s from the sound. When mpv moves to another item of a playlist, the picture of that item loads.
- **Closing:** turning video off or closing the panel only removes the picture.

Without Qt Multimedia, the video area says that the radio profile installs it, and the rest of the panel works.

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
| `desktop-radio play ID\|URL` | Plays a station, a stream, a YouTube link or a file |
| `desktop-radio toggle`, `stop`, `next`, `previous` | Controls playback |
| `desktop-radio video` | Opens the panel with the picture of what plays |
| `desktop-radio search QUERY [all\|playlist\|video]` | Searches YouTube |
| `desktop-radio list`, `status` | Prints the stations and the state as JSON |

These commands act only on the radio's own mpv, through `$XDG_RUNTIME_DIR/desktop-shell/radio-mpv.sock`. Another mpv you started yourself is never paused, skipped or closed. The state is kept in `radio.json` next to that socket.
