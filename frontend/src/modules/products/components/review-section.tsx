"use client"

import { Button } from "@medusajs/ui"
import { useState, useEffect, useTransition } from "react"

type Review = { id: string; rating: number; title: string | null; content: string; created_at: string | null; account_name: string | null }

const PROXY = "/api/backend"

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(PROXY + path, { ...init, credentials: "include" })
  if (!r.ok) { const b = await r.json().catch(() => ({})); throw new Error(b.detail || `Failed: ${r.status}`) }
  return r.json()
}

export default function ReviewSection({ productIdentity }: { productIdentity: string }) {
  const [reviews, setReviews] = useState<Review[]>([])
  const [rating, setRating] = useState(5)
  const [content, setContent] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [isPending, startTransition] = useTransition()
  const [deleteId, setDeleteId] = useState<string | null>(null)

  const loadReviews = () => {
    api<Review[]>(`/shop/${encodeURIComponent(productIdentity)}/reviews`)
      .then(setReviews)
      .catch((e) => { console.error("Failed to load reviews:", e) })
  }

  useEffect(() => { loadReviews() }, [productIdentity])

  const handleSubmit = () => {
    if (!content.trim()) return
    setLoading(true)
    setError("")
    api(`/shop/${encodeURIComponent(productIdentity)}/reviews`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ rating, content: content.trim() }),
    })
      .then(() => { setContent(""); loadReviews() })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }

  const handleDelete = (reviewId: string) => {
    startTransition(async () => {
      try {
        await api(`/accounts/me/reviews/${reviewId}`, { method: "DELETE" })
        setDeleteId(null)
        loadReviews()
      } catch {}
    })
  }

  const avgRating = reviews.length > 0
    ? (reviews.reduce((sum, r) => sum + r.rating, 0) / reviews.length).toFixed(1)
    : null

  return (
    <div className="mt-12 border-t border-ui-border-base pt-8">
      <div className="flex items-baseline gap-2 mb-6">
        <h2 className="text-xl-semi">Reviews</h2>
        <span className="text-small-regular text-ui-fg-muted">({reviews.length} {reviews.length === 1 ? "review" : "reviews"})</span>
        {avgRating && (
          <span className="text-small-regular text-ui-fg-muted"> &middot; Average {avgRating} ★</span>
        )}
      </div>

      {reviews.length > 0 && (
        <div className="space-y-2 mb-8">
          {reviews.map((r) => (
            <div key={r.id} className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-yellow-500 text-sm">{'★'.repeat(r.rating)}{'☆'.repeat(5 - r.rating)}</span>
                  <span className="text-small-regular font-medium">{r.account_name || "Anonymous"}</span>
                  <span className="text-small-regular text-ui-fg-muted">{r.created_at ? new Date(r.created_at).toLocaleDateString() : ""}</span>
                </div>
                <button className="text-small-regular text-rose-500 hover:text-rose-700" onClick={() => setDeleteId(r.id)}>
                  Delete
                </button>
              </div>
              {r.title && <p className="mt-1 text-small-regular font-medium">{r.title}</p>}
              {r.content && <p className="mt-1 text-small-regular text-ui-fg-subtle">{r.content}</p>}
            </div>
          ))}
        </div>
      )}

      {reviews.length === 0 && (
        <p className="text-small-regular text-ui-fg-muted mb-6">No reviews yet. Be the first to share your thoughts!</p>
      )}

      <div className="bg-gray-50 rounded-lg p-5 mb-8">
        <h3 className="text-base-semi mb-3">Write a review</h3>
        <div className="flex items-center gap-2 mb-3">
          <span className="text-small-regular">Rating:</span>
          {[1, 2, 3, 4, 5].map((n) => (
            <button key={n} className={`text-xl ${n <= rating ? "text-yellow-500" : "text-gray-300"}`} onClick={() => setRating(n)}>
              ★
            </button>
          ))}
        </div>
        <textarea
          className="w-full border rounded p-3 text-small-regular min-h-[80px]"
          placeholder="Share your thoughts about this product..."
          value={content}
          onChange={(e) => setContent(e.target.value)}
        />
        {error && <p className="text-rose-500 text-small-regular mt-2">{error}</p>}
        <Button className="mt-3 h-9" onClick={handleSubmit} isLoading={loading} disabled={!content.trim()}>
          Submit Review
        </Button>
      </div>

      {deleteId && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center">
          <div className="fixed inset-0 bg-black/50" onClick={() => setDeleteId(null)} />
          <div className="relative bg-white rounded-lg shadow-xl p-6 max-w-sm w-full mx-4">
            <h3 className="text-lg font-medium">Delete Review</h3>
            <p className="mt-2 text-small-regular text-ui-fg-subtle">Are you sure you want to delete this review?</p>
            <div className="mt-6 flex justify-end gap-3">
              <Button variant="secondary" onClick={() => setDeleteId(null)}>Cancel</Button>
              <Button onClick={() => handleDelete(deleteId)} isLoading={isPending}>Delete</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
