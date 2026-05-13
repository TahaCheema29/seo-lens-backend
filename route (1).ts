export const dynamic = "force-dynamic";

import { stripe } from "@/config/stripe-config";
import { createResponse } from "@/utils/createResponse";
import { NextRequest, NextResponse } from "next/server";

/**
 * @swagger
 * /api/stripe/status:
 *   get:
 *     summary: Check Stripe checkout session payment status
 *     tags: [Stripe]
 *     parameters:
 *       - in: query
 *         name: session_id
 *         required: true
 *         schema:
 *           type: string
 *         description: Stripe checkout session ID
 *     responses:
 *       200:
 *         description: Payment successful
 *         content:
 *           application/json:
 *             example:
 *               status: true
 *               message: "Payment successful"
 *               data: null
 *       204:
 *         description: No payment required
 *         content:
 *           application/json:
 *             example:
 *               status: true
 *               message: "No payment required"
 *               data: null
 *       400:
 *         description: Session ID is required
 *         content:
 *           application/json:
 *             example:
 *               status: false
 *               message: "Session ID is required."
 *               data: null
 *       402:
 *         description: Payment unpaid or pending
 *         content:
 *           application/json:
 *             example:
 *               status: false
 *               message: "Payment unpaid or pending"
 *               data: null
 *       404:
 *         description: Session not found
 *         content:
 *           application/json:
 *             example:
 *               status: false
 *               message: "Session not found."
 *               data: null
 *       500:
 *         description: Internal Server Error or Unknown payment status
 *         content:
 *           application/json:
 *             example:
 *               status: false
 *               message: "Unknown payment status"
 *               data: null
 */
export async function GET(req: NextRequest) {
  try {
    const searchParams = req.nextUrl.searchParams;
    const sessionId = searchParams.get("session_id");

    if (!sessionId) {
      return NextResponse.json(
        createResponse(false, "Session ID is required.", null),
        { status: 400 },
      );
    }

    const session = await stripe.checkout.sessions.retrieve(sessionId);

    if (!session) {
      return NextResponse.json(
        createResponse(false, "Session not found.", null),
        { status: 404 },
      );
    }

    if (session.payment_status === "paid") {
      return NextResponse.json(
        createResponse(true, "Payment successful", null),
        { status: 200 },
      );
    } else if (session.payment_status === "no_payment_required") {
      return NextResponse.json(
        createResponse(true, "No payment required", null),
        { status: 204 },
      );
    } else if (session.payment_status === "unpaid") {
      return NextResponse.json(
        createResponse(false, "Payment unpaid or pending", null),
        { status: 402 },
      );
    } else {
      return NextResponse.json(
        createResponse(false, "Unknown payment status", null),
        { status: 500 },
      );
    }
  } catch (error) {
    console.error("Stripe Error:", error);
    const errorMessage = error instanceof Error ? error.message : String(error);
    return NextResponse.json(createResponse(false, errorMessage, null), {
      status: 500,
    });
  }
}
