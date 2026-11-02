import "./Directory.css";
import { useState } from "react";
import { directoryEntries } from "../data/directoryEntries.js";

export default function Directory() {
  const [query, setQuery] = useState("");
  const q = query.trim().toLowerCase();

  const matches = directoryEntries.filter(
    (e) => e.name.toLowerCase().includes(q) || e.category.toLowerCase().includes(q)
  );

  return (
    <section className="directory">
      <h2>Official contacts</h2>
      <input
        type="search"
        placeholder="Search by name or category"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      {matches.length === 0 && <p>No matching institutions.</p>}
      <ul className="directory-list">
        {matches.map((e) => (
          <li key={e.name} className="directory-card">
            <h3>{e.name}</h3>
            <p>Category: {e.category}</p>
            <p>
              Phone:{" "}
              <a href={`tel:${e.phone.replace(/[\s()]/g, "")}`}>{e.phone}</a>
            </p>
            <p>Website: {e.website}</p>
            <p className="verified">Verified on {e.lastVerified}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
