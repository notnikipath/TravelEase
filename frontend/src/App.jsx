import React, { useMemo, useState } from "react";
import { dateAfterDays } from "./dates";

const apiBase = import.meta.env.VITE_GATEWAY_URL || "http://localhost:8500";

const tomorrow = () => dateAfterDays(1);
const plusDays = (days) => dateAfterDays(days);

export default function App() {
  const [city, setCity] = useState("Sochi");
  const [queryText, setQueryText] = useState("beach all inclusive");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [selectedItem, setSelectedItem] = useState(null);
  const [bookingState, setBookingState] = useState(null);
  const [startDate, setStartDate] = useState(tomorrow());
  const [endDate, setEndDate] = useState(plusDays(7));

  const canBook = useMemo(() => selectedItem && startDate < endDate, [selectedItem, startDate, endDate]);

  const runSearch = async () => {
    setLoading(true);
    setMessage("");
    try {
      const response = await fetch(`${apiBase}/workflow/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: "user-demo",
          city,
          query_text: queryText,
          min_rating: 4.4,
          amenities: ["wifi"],
        }),
      });
      if (!response.ok) throw new Error(`Search failed (${response.status})`);
      const payload = await response.json();
      setResults(payload.results.items || []);
      setMessage(`Found ${payload.results.count || 0} offers`);
      if (payload.results.items?.length) {
        setSelectedItem(payload.results.items[0]);
      }
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  };

  const bookSelected = async () => {
    if (!selectedItem) return;
    setLoading(true);
    setMessage("");
    try {
      const response = await fetch(`${apiBase}/workflow/book-hotel`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: "user-demo",
          item_id: selectedItem.item_id,
          start_date: startDate,
          end_date: endDate,
          travelers: 2,
          payment_method: "card",
        }),
      });
      if (!response.ok) throw new Error(`Booking failed (${response.status})`);
      const payload = await response.json();
      setBookingState(payload);
      setMessage(`Booking ${payload.booking.booking_id} confirmed`);
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="page">
      <header className="hero">
        <p className="kicker">TravelEase</p>
        <h1>Find your next journey</h1>
        <p className="sub">Search hotels, flights, rail tickets, excursions, and all-inclusive tours from one flow.</p>
      </header>

      <section className="card form">
        <div className="row">
          <label>
            City
            <input value={city} onChange={(e) => setCity(e.target.value)} placeholder="Sochi" />
          </label>
          <label>
            Semantic request
            <input value={queryText} onChange={(e) => setQueryText(e.target.value)} placeholder="beach all inclusive" />
          </label>
          <button disabled={loading} onClick={runSearch}>
            {loading ? "Searching..." : "Find offers"}
          </button>
        </div>
      </section>

      <section className="grid">
        <div className="card">
          <h2>Search results</h2>
          <ul className="list">
            {results.map((item) => (
              <li
                key={item.item_id}
                className={selectedItem?.item_id === item.item_id ? "active" : ""}
                onClick={() => setSelectedItem(item)}
              >
                <strong>{item.name}</strong>
                <span>{item.city}</span>
                <span>{item.service_type}</span>
                <span>{item.base_price} RUB</span>
              </li>
            ))}
            {!results.length && <li className="placeholder">No offers yet. Run search.</li>}
          </ul>
        </div>

        <div className="card">
          <h2>Book selected offer</h2>
          <div className="row compact">
            <label>
              Start
              <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
            </label>
            <label>
              End
              <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
            </label>
            <button disabled={!canBook || loading} onClick={bookSelected}>
              Confirm booking
            </button>
          </div>
          {selectedItem && (
            <div className="selected">
              <p>{selectedItem.name}</p>
              <p>{selectedItem.rating} rating</p>
            </div>
          )}
          {bookingState && (
            <div className="result">
              <p>Total: {bookingState.booking.total_price} RUB</p>
              <p>Loyalty level: {bookingState.loyalty.level}</p>
            </div>
          )}
        </div>
      </section>

      {message && <p className="message">{message}</p>}
    </section>
  );
}
