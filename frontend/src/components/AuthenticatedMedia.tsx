import { useEffect, useState } from "react";
import { fetchMediaBlob, mediaUrl } from "../api/client";
import "./AuthenticatedMedia.css";

interface AuthenticatedAudioProps {
  path: string;
  className?: string;
  label?: string;
}

export function AuthenticatedAudio({ path, className = "", label }: AuthenticatedAudioProps) {
  const [src, setSrc] = useState<string | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let objectUrl: string | null = null;
    let cancelled = false;

    fetchMediaBlob(path)
      .then((blob) => {
        if (cancelled) return;
        objectUrl = URL.createObjectURL(blob);
        setSrc(objectUrl);
      })
      .catch(() => {
        if (!cancelled) setError(true);
      });

    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [path]);

  if (error) {
    return <p className="auth-media__error">Unable to load recording</p>;
  }
  if (!src) {
    return <p className="auth-media__loading">{label ? `Loading ${label}…` : "Loading audio…"}</p>;
  }

  return <audio controls preload="metadata" src={src} className={className} />;
}

interface AuthenticatedImageProps {
  path: string;
  alt: string;
  className?: string;
}

export function AuthenticatedImage({ path, alt, className = "" }: AuthenticatedImageProps) {
  const [src, setSrc] = useState<string | null>(null);

  useEffect(() => {
    let objectUrl: string | null = null;
    let cancelled = false;

    fetchMediaBlob(path)
      .then((blob) => {
        if (cancelled) return;
        objectUrl = URL.createObjectURL(blob);
        setSrc(objectUrl);
      })
      .catch(() => {
        if (!cancelled) setSrc(mediaUrl(path));
      });

    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [path]);

  if (!src) {
    return <div className={`auth-media__placeholder ${className}`} aria-hidden />;
  }

  return <img src={src} alt={alt} className={className} loading="lazy" />;
}
