import { useState } from "react";

const SUGGESTIONS = [
  "Amul Butter 500g", "Tata Salt 1kg", "Aashirvaad Atta 5kg",
  "Maggi Noodles", "Fortune Oil 1L", "Parle-G Biscuits",
];

const CITIES = [
  { id: "Delhi",     display: "Delhi / NCR" },
  { id: "Mumbai",    display: "Mumbai" },
  { id: "Bengaluru", display: "Bengaluru" },
  { id: "Hyderabad", display: "Hyderabad" },
  { id: "Chennai",   display: "Chennai" },
  { id: "Kolkata",   display: "Kolkata" },
  { id: "Pune",      display: "Pune" },
  { id: "Ahmedabad", display: "Ahmedabad" },
];

export default function SearchBar({ onSearch, loading }) {
  const [query, setQuery]         = useState("");
  const [city, setCity]           = useState("Delhi");
  const [locStatus, setLocStatus] = useState("idle");
  const [customLoc, setCustomLoc] = useState(null);

  function doSearch(q, loc) {
    if (!q || q.trim().length < 2) return;
    const l = loc ?? customLoc;
    if (l) {
      onSearch(q.trim(), { lat: l.lat, lon: l.lon });
    } else {
      onSearch(q.trim(), { city });
    }
  }

  function handleSubmit(e) {
    e.preventDefault();
    doSearch(query);
  }

  function handleGeolocate() {
    if (!navigator.geolocation) { setLocStatus("error"); return; }
    setLocStatus("locating");
    navigator.geolocation.getCurrentPosition(
      ({ coords: { latitude, longitude } }) => {
        const loc = { lat: String(latitude), lon: String(longitude) };
        setCustomLoc(loc);
        setLocStatus("done");
        if (query.trim().length >= 2) doSearch(query, loc);
      },
      () => setLocStatus("error"),
      { timeout: 8000 },
    );
  }

  return (
    <div className="w-full">
      <form onSubmit={handleSubmit}>
        <div className="relative mb-2">
          <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400 text-lg pointer-events-none">🔍</span>
          <input
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Search product (e.g. Amul Butter 500g)"
            className="w-full h-12 pl-11 pr-4 rounded-xl border-2 border-gray-200 bg-white
                       text-gray-900 placeholder-gray-400 text-base
                       focus:outline-none focus:border-indigo-400 transition-colors"
            disabled={loading}
            autoComplete="off"
          />
        </div>
        <div className="flex gap-2">
          <div className="relative flex-1">
            <select
              value={customLoc ? "__gps__" : city}
              onChange={e => { setCity(e.target.value); setCustomLoc(null); setLocStatus("idle"); }}
              disabled={loading}
              className="w-full h-11 pl-3 pr-7 rounded-xl border border-gray-200 bg-white
                         text-gray-800 text-sm appearance-none focus:outline-none
                         focus:border-indigo-400 transition-colors cursor-pointer"
            >
              {customLoc && <option value="__gps__">My location</option>}
              {CITIES.map(c => <option key={c.id} value={c.id}>{c.display}</option>)}
            </select>
            <span className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none text-xs">▼</span>
          </div>
          <button
            type="button"
            onClick={handleGeolocate}
            disabled={loading || locStatus === "locating"}
            title="Use my current location"
            className={`w-11 h-11 rounded-xl border text-base flex-shrink-0 flex items-center justify-center transition-colors ${
              locStatus === "done"     ? "bg-green-50 border-green-300" :
              locStatus === "error"    ? "bg-red-50 border-red-300" :
              locStatus === "locating" ? "bg-indigo-50 border-indigo-200 animate-pulse" :
                                        "bg-white border-gray-200 hover:border-indigo-300"
            }`}
          >
            {locStatus === "locating" ? "⏳" : locStatus === "done" ? "✅" : locStatus === "error" ? "❌" : "📍"}
          </button>
          <button
            type="submit"
            disabled={loading || query.trim().length < 2}
            className="h-11 px-5 rounded-xl bg-indigo-600 text-white font-semibold text-sm
                       flex-shrink-0 disabled:opacity-50 hover:bg-indigo-700 active:bg-indigo-800
                       transition-colors"
          >
            {loading ? "…" : "Compare"}
          </button>
        </div>
      </form>
      <div className="mt-2.5 flex gap-1.5 flex-wrap">
        {SUGGESTIONS.map(s => (
          <button
            key={s}
            onClick={() => { setQuery(s); doSearch(s); }}
            disabled={loading}
            className="px-2.5 py-1 text-xs rounded-full bg-gray-100 text-gray-600
                       hover:bg-indigo-50 hover:text-indigo-600 transition-colors disabled:opacity-50"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}
