import { useEffect, useState } from "react";
import { listGallery } from "../api/visits";
import { ApiError, mediaUrl } from "../api/client";
import { WorkerLayout } from "../layouts/WorkerLayout";
import type { GalleryMediaItem } from "../types/api";
import "./GalleryPage.css";

export function GalleryPage() {
  const [items, setItems] = useState<GalleryMediaItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    listGallery()
      .then(setItems)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load gallery"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <WorkerLayout title="Gallery">
      <div className="gallery animate-in">
        <p className="gallery__hint">Photos from your saved field visits</p>
        {loading ? <p className="gallery__muted">Loading…</p> : null}
        {error ? <p className="gallery__error">{error}</p> : null}
        {!loading && items.length === 0 ? (
          <p className="gallery__muted">No photos yet. Save a visit with context photos.</p>
        ) : null}
        <div className="gallery__grid">
          {items.map((item) => (
            <figure key={`${item.visit_id}-${item.path}`} className="gallery__item">
              <img src={mediaUrl(item.path)} alt={`${item.location} — ${item.media_type}`} loading="lazy" />
              <figcaption>
                <span className={`gallery__tag gallery__tag--${item.media_type}`}>
                  {item.media_type === "field" ? "Context" : "Notes"}
                </span>
                {item.location}
              </figcaption>
            </figure>
          ))}
        </div>
      </div>
    </WorkerLayout>
  );
}
