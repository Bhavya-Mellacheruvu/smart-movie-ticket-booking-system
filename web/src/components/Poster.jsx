import { useState } from "react";
import { releaseDateLabel } from "../utils.js";

const POSTER_IMAGES = {
  "godzilla-minus-zero":
    "https://images.squarespace-cdn.com/content/v1/5bbcad0f2727be3646b9fee1/23b248aa-b236-4ecd-a1af-e926ea528e81/IMG_1910.jpeg",
  "hunger-games-sunrise":
    "https://cdn-origin.cool-style.com.tw/cool/2025/11/G6M-OQtacAsfdjw.jpeg",
  "focker-in-law":
    "https://dx35vtwkllhj9.cloudfront.net/universalstudios/focker-in-law/images/regions/us/onesheet.jpg",
  "avengers-doomsday":
    "https://catalog.cinema-api.com/cf/images/ncg-images/04a9cb3d9fd24b45af544b44cd4b4105.jpg?version=BDA0A2AE6D2C54940BE5B87E4252394E",
  "dune-part-three":
    "https://images.ctfassets.net/c4ucztjx9pmu/5GKRRV43QjQtzHI8ScLPKg/f88bb5d8ae463cc052e68e2623a4c9ce2/DUNE3_CHARACTER_TIMOTHEE_1080x1600px_V01.jpg",
  "jumanji-open-world":
    "https://image.tmdb.org/t/p/original/aUJg1QoAenZ7GodF38OrfyiOtKu.jpg",
};
const art = {
  midnight: (
    <>
      <div className="art-moon" />
      <div className="art-window" />
      <div className="art-silhouette" />
    </>
  ),
  wild: (
    <>
      <div className="wild-sun" />
      <div className="wild-hill h1" />
      <div className="wild-hill h2" />
      <div className="wild-stem" />
    </>
  ),
  orbit: (
    <>
      <div className="orbit-planet" />
      <div className="orbit-ring" />
      <div className="orbit-ship">✦</div>
      <div className="orbit-stars">
        ✦　·　✧
        <br />
        ·　✦　·　✧
      </div>
    </>
  ),
  paper: (
    <>
      <div className="paper-moon" />
      <div className="paper-hills" />
      <div className="paper-house">⌂</div>
      <div className="paper-stars">✦ · ✧ · ✦</div>
    </>
  ),
  blue: (
    <>
      <div className="blue-moon" />
      <div className="blue-city" />
    </>
  ),
  last: (
    <>
      <div className="last-sun" />
      <div className="last-lines">
        〰<br />
        〰〰
        <br />〰
      </div>
      <div className="last-hill" />
    </>
  ),
};

export default function Poster({ movie, large = false }) {
  const [failed, setFailed] = useState(false),
    image = POSTER_IMAGES[movie.id];
  return (
    <div
      className={`poster poster-${movie.poster} ${large ? "poster-large" : ""} ${image && !failed ? "has-photo" : ""}`}
      style={{ "--poster-accent": movie.accent || "#586b78" }}
    >
      {image && !failed && (
        <img
          className="poster-photo"
          src={image}
          alt={`${movie.title} poster`}
          onError={() => setFailed(true)}
        />
      )}
      <div className="poster-art">
        {art[movie.poster] || (
          <>
            <div className="generated-orb" />
            <div className="generated-arch" />
            <div className="generated-stars">✦　·　✧</div>
          </>
        )}
      </div>
      <div className="poster-grain" />
      <div className="poster-copy">
        <span className="poster-tag">{movie.tag || "2026 RELEASE"}</span>
        <div className="poster-title">{movie.title}</div>
        <div className="poster-meta">
          {movie.release_date
            ? releaseDateLabel(movie.release_date).toUpperCase() + "　·　2026"
            : movie.year}
        </div>
      </div>
      <span className="poster-mark">F</span>
    </div>
  );
}
