import "./NowPlaying.css";

export interface NowPlayingData {
  art_url?: string;
  station?: string;
  track?: string;
  artist?: string;
  play_status?: string;
}

interface NowPlayingProps {
  nowPlaying?: NowPlayingData | null;
  onPlayPause?: () => void;
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
        <div className="np-station">{nowPlaying.station || "Kein Sender"}</div>
        {nowPlaying.track && <div className="np-track">{nowPlaying.track}</div>}
        {nowPlaying.artist && <div className="np-artist">{nowPlaying.artist}</div>}
      </div>
    </div>
  );
}
