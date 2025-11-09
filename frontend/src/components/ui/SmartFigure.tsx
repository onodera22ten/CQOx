/**
 * SmartFigure Component - NASA/Google Standard
 *
 * Purpose: Automatically handle different figure types (img/iframe/video)
 * Features:
 * - Extension-based rendering (<img> vs <iframe>)
 * - WolframONE HTML support
 * - Lazy loading
 * - Error handling
 */

import { useState } from "react";

export interface SmartFigureProps {
  src: string;
  alt?: string;
  title?: string;
  className?: string;
}

export function SmartFigure({ src, alt, title, className = "" }: SmartFigureProps) {
  const [error, setError] = useState(false);

  // Determine type by extension
  const isHTML = /\.html?($|\?)/i.test(src);
  const isVideo = /\.(mp4|webm|mov)($|\?)/i.test(src);
  const isImage = !isHTML && !isVideo;

  if (error) {
    return (
      <div className={`flex items-center justify-center bg-slate-800/50 rounded-xl border border-slate-700 ${className}`}
           style={{ minHeight: "300px" }}>
        <div className="text-center text-slate-400">
          <svg className="w-12 h-12 mx-auto mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-sm">Failed to load figure</p>
          <p className="text-xs mt-1 text-slate-500">{src}</p>
        </div>
      </div>
    );
  }

  if (isHTML) {
    return (
      <iframe
        src={src}
        title={title || alt || "Figure"}
        className={`w-full rounded-xl border border-slate-700 ${className}`}
        style={{ minHeight: "420px", height: "420px" }}
        onError={() => setError(true)}
        loading="lazy"
        sandbox="allow-scripts allow-same-origin"
      />
    );
  }

  if (isVideo) {
    return (
      <video
        src={src}
        className={`w-full h-auto rounded-xl ${className}`}
        controls
        onError={() => setError(true)}
      >
        Your browser does not support the video tag.
      </video>
    );
  }

  // Default: image
  return (
    <img
      src={src}
      alt={alt || title || "Figure"}
      className={`w-full h-auto rounded-xl ${className}`}
      onError={() => setError(true)}
      loading="lazy"
    />
  );
}
