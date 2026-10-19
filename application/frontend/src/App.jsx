import { useCallback, useEffect, useState } from "react";
import * as api from "./api.js";

const money = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 });
const EMPTY_ITEM = { name: "", sku: "", category: "General", supplier: "", quantity: 0, unit_price: 0, reorder_level: 5 };

export default function App() {
  const [items, setItems] = useState([]);
  const [summary, setSummary] = useState(null);
  const [categories, setCategories] = useState([]);
  const [filters, setFilters] = useState({ search: "", category: "", reorder_only: false });
  const [editing, setEditing] = useState(null); // null = closed, {} = new item, item = edit
  const [historyFor, setHistoryFor] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const [list, stats, cats] = await Promise.all([api.listItems(filters), api.getSummary(), api.getCategories()]);
      setItems(list);
      setSummary(stats);
      setCategories(cats);
      setError("");
    } catch (err) {
      setError(`Could not reach the API: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    const timer = setTimeout(refresh, 200); // debounce typing in the search box
    return () => clearTimeout(timer);
  }, [refresh]);

  const run = async (action) => {
    try {
      await action();
      await refresh();
    } catch (err) {
      setError(err.message);
    }
  };

  const adjust = (item, change) =>
    run(() => api.moveStock(item.id, change, change > 0 ? "Received" : "Shipped"));

  const remove = (item) => {
    if (window.confirm(`Delete ${item.name} (${item.sku})?`)) run(() => api.deleteItem(item.id));
  };

  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand">
          <img src="/favicon.svg" alt="" width="32" height="32" />
          <div>
            <h1>InvenTrack</h1>
            <p>Stock control for the shop floor</p>
          </div>
        </div>
        <button className="btn primary" onClick={() => setEditing({})}>+ New item</button>
      </header>

      {error && (
        <div className="banner" role="alert">
          {error}
          <button className="link" onClick={() => setError("")}>Dismiss</button>
        </div>
      )}

      <section className="kpis" aria-label="Inventory summary">
        <Kpi label="Items" value={summary?.item_count} />
        <Kpi label="Units in stock" value={summary?.units_in_stock} />
        <Kpi label="Stock value" value={summary && money.format(summary.stock_value)} />
        <Kpi label="Need reorder" value={summary?.reorder_count} alert={summary?.reorder_count > 0} />
      </section>

      <section className="panel">
        <div className="toolbar">
          <input
            type="search"
            placeholder="Search name, SKU or supplier"
            value={filters.search}
            onChange={(e) => setFilters({ ...filters, search: e.target.value })}
            aria-label="Search"
          />
          <select
            value={filters.category}
            onChange={(e) => setFilters({ ...filters, category: e.target.value })}
            aria-label="Category"
          >
            <option value="">All categories</option>
            {categories.map((c) => <option key={c}>{c}</option>)}
          </select>
          <label className="check">
            <input
              type="checkbox"
              checked={filters.reorder_only}
              onChange={(e) => setFilters({ ...filters, reorder_only: e.target.checked })}
            />
            Needs reorder
          </label>
        </div>

        {loading ? (
          <p className="empty">Loading…</p>
        ) : items.length === 0 ? (
          <p className="empty">No items match. Add one with “New item”.</p>
        ) : (
          <table className="grid">
            <thead>
              <tr>
                <th>Item</th><th>Category</th><th>Supplier</th>
                <th className="num">Price</th><th className="num">In stock</th><th aria-label="Actions" />
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id} className={item.needs_reorder ? "low" : ""}>
                  <td data-label="Item">
                    <strong>{item.name}</strong>
                    <span className="sku">{item.sku}</span>
                  </td>
                  <td data-label="Category"><span className="tag">{item.category}</span></td>
                  <td data-label="Supplier">{item.supplier || "—"}</td>
                  <td data-label="Price" className="num">{money.format(item.unit_price)}</td>
                  <td data-label="In stock" className="num">
                    <div className="stepper">
                      <button onClick={() => adjust(item, -1)} disabled={item.quantity === 0} aria-label={`Ship one ${item.name}`}>−</button>
                      <span>{item.quantity}</span>
                      <button onClick={() => adjust(item, 1)} aria-label={`Receive one ${item.name}`}>+</button>
                    </div>
                    {item.needs_reorder && <span className="badge">Reorder at {item.reorder_level}</span>}
                  </td>
                  <td className="actions">
                    <button className="link" onClick={() => setHistoryFor(item)}>History</button>
                    <button className="link" onClick={() => setEditing(item)}>Edit</button>
                    <button className="link danger" onClick={() => remove(item)}>Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <footer className="foot">InvenTrack v1.2 · Abhi Gandhi · 10397 · deployed by Argo CD</footer>

      {editing && (
        <ItemForm
          item={editing}
          onClose={() => setEditing(null)}
          onSave={async (data) => {
            if (editing.id) await api.updateItem(editing.id, data);
            else await api.createItem(data);
            setEditing(null);
            await refresh();
          }}
        />
      )}
      {historyFor && <History item={historyFor} onClose={() => setHistoryFor(null)} />}
    </div>
  );
}

function Kpi({ label, value, alert }) {
  return (
    <div className={`kpi ${alert ? "alert" : ""}`}>
      <span>{label}</span>
      <strong>{value ?? "–"}</strong>
    </div>
  );
}

function ItemForm({ item, onClose, onSave }) {
  const [form, setForm] = useState({ ...EMPTY_ITEM, ...item, supplier: item.supplier ?? "" });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await onSave({
        name: form.name.trim(),
        sku: form.sku.trim().toUpperCase(),
        category: form.category.trim() || "General",
        supplier: form.supplier.trim() || null,
        quantity: Number(form.quantity),
        unit_price: Number(form.unit_price),
        reorder_level: Number(form.reorder_level),
      });
    } catch (err) {
      setError(err.message);
      setSaving(false);
    }
  };

  return (
    <Modal title={item.id ? `Edit ${item.name}` : "New item"} onClose={onClose}>
      <form className="form" onSubmit={submit}>
        <Field label="Name"><input required value={form.name} onChange={set("name")} autoFocus /></Field>
        <Field label="SKU"><input required pattern="[A-Za-z0-9\-]+" value={form.sku} onChange={set("sku")} /></Field>
        <Field label="Category"><input value={form.category} onChange={set("category")} /></Field>
        <Field label="Supplier"><input value={form.supplier} onChange={set("supplier")} /></Field>
        <Field label="Quantity"><input type="number" min="0" value={form.quantity} onChange={set("quantity")} /></Field>
        <Field label="Unit price (₹)"><input type="number" min="0" step="0.01" value={form.unit_price} onChange={set("unit_price")} /></Field>
        <Field label="Reorder level"><input type="number" min="0" value={form.reorder_level} onChange={set("reorder_level")} /></Field>
        {error && <p className="form-error">{error}</p>}
        <div className="form-actions">
          <button type="button" className="btn" onClick={onClose}>Cancel</button>
          <button className="btn primary" disabled={saving}>{saving ? "Saving…" : "Save"}</button>
        </div>
      </form>
    </Modal>
  );
}

function History({ item, onClose }) {
  const [moves, setMoves] = useState(null);
  useEffect(() => {
    api.getMovements(item.id).then(setMoves).catch(() => setMoves([]));
  }, [item.id]);

  return (
    <Modal title={`Stock history · ${item.name}`} onClose={onClose}>
      {moves === null ? (
        <p className="empty">Loading…</p>
      ) : moves.length === 0 ? (
        <p className="empty">No stock movements yet.</p>
      ) : (
        <ul className="history">
          {moves.map((m) => (
            <li key={m.id}>
              <span className={m.change > 0 ? "in" : "out"}>{m.change > 0 ? `+${m.change}` : m.change}</span>
              <span>{m.reason || "—"}</span>
              <span className="muted">→ {m.quantity_after} left</span>
              <time className="muted">{m.created_at ? new Date(m.created_at).toLocaleString() : ""}</time>
            </li>
          ))}
        </ul>
      )}
    </Modal>
  );
}

function Modal({ title, onClose, children }) {
  useEffect(() => {
    const onKey = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  return (
    <div className="overlay" onClick={onClose}>
      <div className="modal" role="dialog" aria-modal="true" aria-label={title} onClick={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <h2>{title}</h2>
          <button className="link" onClick={onClose} aria-label="Close">✕</button>
        </div>
        {children}
      </div>
    </div>
  );
}

function Field({ label, children }) {
  return (
    <label className="field">
      <span>{label}</span>
      {children}
    </label>
  );
}
