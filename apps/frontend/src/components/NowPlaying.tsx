import "./NowPlaying.css";

export interface NowPlayingData {
  art_url?: string;
  station?: string;
  track?: string;
  artist?: string;
  play_status?: string;
  source?: string;
}

interface NowPlayingProps {
  nowPlaying?: NowPlayingData | null;
  onPlayPause?: () => void;
}

const BT_ICON =
  "M17.71 7.71L12 2h-1v7.59L6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 11 14.41V22h1l5.71-5.71-4.3-4.29 4.3-4.29zM13 5.83l1.88 1.88L13 9.59V5.83zm1.88 10.46L13 18.17v-3.76l1.88 1.88z";
const RADIO_ICON =
  "M20 6H8.3l8.26-3.34L15.88 1 3.24 6.15C2.51 6.43 2 7.17 2 8v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm-8 11c-1.66 0-3-1.34-3-3s1.34-3 3-3 3 1.34 3 3-1.34 3-3 3z";

function getStationDisplay(station?: string, source?: string): string {
  if (station) return station;
  if (source === "BLUETOOTH") return "Kein Gerät verbunden";
  return "Kein Sender";
}

function getSourceBadge(source?: string) {
  if (source === "BLUETOOTH") {
    return (
      <div className="np-source-badge bluetooth" title="Bluetooth">
        <svg viewBox="0 0 24 24" width="16" height="16">
          <path fill="currentColor" d={BT_ICON} />
        </svg>
      </div>
    );
  }
  if (source === "INTERNET_RADIO" || source === "TUNEIN") {
    return (
      <div className="np-source-badge radio" title="Radio">
        <svg viewBox="0 0 24 24" width="16" height="16">
          <path fill="currentColor" d={RADIO_ICON} />
        </svg>
      </div>
    );
  }
  return null;
}

export default function NowPlaying({ nowPlaying, onPlayPause }: NowPlayingProps) {
  if (!nowPlaying) {
    return (
      <div className="now-playing empty">
        <div className="np-placeholder">Keine Wiedergabe</div>
      </div>
    );
  }

  const isPlaying = nowPlaying.play_status === "PLAY_STATE";

  return (
    <div className="now-playing">
      <div className="np-art">
        {nowPlaying.art_url ? (
          <img src={nowPlaying.art_url} alt="" />
        ) : (
          <div className="np-art-placeholder">🎵</div>
        )}
        {onPlayPause && (
          <button
            className="np-play-overlay"
            onClick={onPlayPause}
            aria-label={isPlaying ? "Pause" : "Play"}
          >
            <svg viewBox="0 0 24 24" width="32" height="32" fill="white">
              {isPlaying ? (
                <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z" />
              ) : (
                <path d="M8 5v14l11-7z" />
              )}
            </svg>
          </button>
        )}
      </div>
      <div className="np-info">
        <div className="np-station">{getStationDisplay(nowPlaying.station, nowPlaying.source)}</div>
        {nowPlaying.track && <div className="np-track">{nowPlaying.track}</div>}
        {nowPlaying.artist && <div className="np-artist">{nowPlaying.artist}</div>}
      </div>
      {getSourceBadge(nowPlaying.source)}
    </div>
  );
}
