"use client";

import { useCallback, useEffect, useState } from "react";
import axios from "axios";
import { loadStripe } from "@stripe/stripe-js";
import { toast } from "sonner";

type SubscriptionPayload = {
  status: string;
  message?: string;
  data?: {
    plan_code: string;
    status: string;
    stripe_subscription_id: string | null;
    current_period_end: string | null;
    cancel_at_period_end: boolean;
  };
};

const box: React.CSSProperties = {
  border: "1px solid var(--border)",
  borderRadius: 12,
  padding: "1.25rem 1.35rem",
  background: "var(--surface)",
  flex: "1 1 260px",
  minWidth: 0,
};

const title: React.CSSProperties = { margin: "0 0 0.35rem", fontSize: "1.15rem" };
const muted: React.CSSProperties = { color: "var(--muted)", margin: 0, fontSize: "0.95rem" };

function getAuthHeader(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const token = localStorage.getItem("access_token");
  if (token) return { Authorization: `Bearer ${token}` };
  return {};
}

export default function SubscriptionPage() {
  const [loading, setLoading] = useState(true);
  const [plan, setPlan] = useState<string>("basic");
  const [subStatus, setSubStatus] = useState<string>("active");
  const [checkoutLoading, setCheckoutLoading] = useState(false);

  const loadSubscription = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await axios.get<SubscriptionPayload>("/api/billing/subscription", {
        headers: getAuthHeader(),
      });
      if (data?.data) {
        setPlan(data.data.plan_code);
        setSubStatus(data.data.status);
      }
    } catch {
      toast.error("Could not load subscription. Sign in and ensure the API is reachable.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadSubscription();
  }, [loadSubscription]);

  const handleSubmit = async () => {
    const publishableKey = process.env.NEXT_PUBLIC_STRIPE_PUBLIC_KEY;
    if (!publishableKey) {
      toast.error("Missing NEXT_PUBLIC_STRIPE_PUBLIC_KEY.");
      return;
    }

    const stripe = await loadStripe(publishableKey);
    if (!stripe) {
      toast.error("Stripe failed to initialize.");
      return;
    }

    setCheckoutLoading(true);
    try {
      const response = await axios.post(
        "/api/stripe/checkout",
        {
          priceId: process.env.NEXT_PUBLIC_STRIPE_PRO_PRICE_ID ?? "",
          price: "",
          description: "SEO Lens Pro",
          success_path: "/dashboard/subscription",
          cancel_path: "/dashboard/subscription",
        },
        { headers: getAuthHeader() }
      );

      const data = response.data as {
        status?: string;
        message?: string;
        data?: { id?: string };
        result?: { id?: string };
      };

      if (data.status !== "success" || !(data.result?.id || data.data?.id)) {
        toast.error(data.message || "Checkout failed.");
        return;
      }

      const sessionId = data.result?.id ?? data.data?.id;
      const { error } = await stripe.redirectToCheckout({ sessionId: sessionId! });
      if (error) {
        toast.error(error.message || "Redirect failed.");
      }
    } catch {
      toast.error("Checkout failed. Please try again.");
    } finally {
      setCheckoutLoading(false);
    }
  };

  const isPro = plan === "pro";

  return (
    <div>
      <h1 style={{ marginTop: 0, fontSize: "1.75rem" }}>Subscription</h1>
      <p style={{ ...muted, marginBottom: "1.5rem" }}>
        Basic is included for free. Upgrade to Pro for full-site analysis, competitor workflows, and more.
      </p>

      {loading ? (
        <p style={muted}>Loading plan…</p>
      ) : (
        <div
          style={{
            display: "flex",
            gap: "1.25rem",
            flexWrap: "wrap",
            alignItems: "stretch",
          }}
        >
          <div style={box}>
            <h2 style={title}>Basic plan</h2>
            <p style={{ ...muted, marginBottom: "0.75rem" }}>Status</p>
            <p style={{ margin: 0, fontSize: "1.25rem", fontWeight: 600, color: "var(--success)" }}>Free</p>
            <p style={{ ...muted, marginTop: "0.75rem" }}>
              Current tier: <strong>{plan}</strong> · billing status: <strong>{subStatus}</strong>
            </p>
          </div>

          <div style={box}>
            <h2 style={title}>Pro Plan</h2>
            <p style={muted}>Unlock Pro features with a secure Stripe checkout.</p>
            <button
              type="button"
              onClick={() => void handleSubmit()}
              disabled={checkoutLoading || isPro}
              style={{
                marginTop: "1rem",
                padding: "0.65rem 1.1rem",
                borderRadius: 8,
                border: "none",
                cursor: isPro || checkoutLoading ? "not-allowed" : "pointer",
                fontWeight: 600,
                fontSize: "0.95rem",
                background: isPro ? "var(--border)" : "var(--accent)",
                color: isPro ? "var(--muted)" : "#0a0f14",
                opacity: checkoutLoading ? 0.75 : 1,
              }}
            >
              {isPro ? "Current plan" : checkoutLoading ? "Starting checkout…" : "Upgrade to Pro"}
            </button>
            {isPro && (
              <p style={{ ...muted, marginTop: "0.75rem", marginBottom: 0 }}>
                You are on Pro. Manage billing in Stripe (portal can be wired later).
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
