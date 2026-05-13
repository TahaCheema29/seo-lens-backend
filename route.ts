import Stripe from "stripe";
import { NextRequest, NextResponse } from "next/server";
import prisma from "@/lib/db";
import { stripe } from "@/config/stripe-config";
import { TPurchasedProduct } from "@/types/common";
import { PaymentStatus } from "@prisma/client";

/**
 * @swagger
 * /api/webhooks/checkout:
 *   post:
 *     summary: Handle Stripe webhook events for payment processing
 *     tags: [Webhooks]
 *     parameters:
 *       - in: header
 *         name: stripe-signature
 *         required: true
 *         schema:
 *           type: string
 *         description: Stripe webhook signature for verification
 *     requestBody:
 *       required: true
 *       content:
 *         application/octet-stream:
 *           schema:
 *             type: string
 *             format: binary
 *     responses:
 *       200:
 *         description: Webhook processed successfully
 *         content:
 *           application/json:
 *             example:
 *               received: true
 *       400:
 *         description: Webhook signature verification failed or invalid event
 *         content:
 *           application/json:
 *             example:
 *               error: "Webhook Error"
 *       500:
 *         description: Internal error processing webhook event
 *         content:
 *           application/json:
 *             example:
 *               error: "Internal error handling event"
 *     description: |
 *       Handles the following Stripe events:
 *       - checkout.session.completed
 *       - checkout.session.async_payment_succeeded
 *       - payment_intent.payment_failed
 *       - charge.refund.updated
 */
export async function POST(request: NextRequest) {
  const body = await request.text();
  const sig = request.headers.get("stripe-signature");
  const endpointSecret = process.env.STRIPE_SECRET_WEBHOOK_KEY!;

  let event: Stripe.Event;

  try {
    if (!sig) throw new Error("Missing Stripe signature header");
    event = stripe.webhooks.constructEvent(body, sig, endpointSecret);
  } catch (err) {
    console.error("Webhook signature verification failed:", err);
    return NextResponse.json({ error: "Webhook Error" }, { status: 400 });
  }

  const eventType = event.type;

  try {
    switch (eventType) {
      case "checkout.session.completed":
      case "checkout.session.async_payment_succeeded":
        console.log("Handling successful payment");
        await handleItemPaymentSuccess(
          event.data.object as Stripe.Checkout.Session,
        );
        break;

      case "payment_intent.payment_failed":
        console.log("Handling failed payment");
        await handleItemPaymentFailure(
          event.data.object as Stripe.PaymentIntent,
        );
        break;

      case "charge.refund.updated":
        await handleItemRefundUpdated(event.data.object as Stripe.Refund);
        break;
      default:
        console.log(`ℹUnhandled event type: ${eventType}`);
    }
  } catch (err) {
    console.error("Error processing event:", err);
    return NextResponse.json(
      { error: "Internal error handling event" },
      { status: 500 },
    );
  }

  return NextResponse.json({ received: true }, { status: 200 });
}

const handleItemPaymentSuccess = async (
  eventObject: Stripe.Checkout.Session,
) => {
  try {
    console.log("checkout session is ", eventObject);
    const email = eventObject.customer_details?.email;
    if (!email) throw new Error("Customer email not found in session.");

    const metadata = eventObject.metadata;
    if (!metadata) throw new Error("Metadata missing in Stripe session.");

    const products = JSON.parse(metadata.products) as TPurchasedProduct;
    const patientId = metadata.patient_id as string;

    if (products.products.length === 0) {
      throw new Error("Purchased Products are missing in session metadata.");
    }

    if (!patientId) {
      throw new Error("Patient ID is missing in session metadata.");
    }

    if (!eventObject.amount_total) throw new Error("Invalid amount.");

    await prisma.$transaction(async (tx) => {
      // 1. Create payment record
      await tx.productPayment.create({
        data: {
          email,
          patientId,
          paymentIntent: eventObject.payment_intent as string,
          amount: eventObject.amount_total! / 100,
          status: "SUCCESSFUL",
          products: {
            create: products.products.map((product) => ({
              productId: product.productId,
              quantity: product.quantity,
              patientId: patientId,
              product: {
                connect: { id: product.id },
              },
            })),
          },
        },
        // delete cart data
      });
      await tx.cart.delete({
        where: { id: products.cartId },
      });

      // 2. Subtract quantity from actual stock for each item
      for (const product of products.products) {
        const dbItem = await tx.product.findUnique({
          where: { id: product.productId },
          select: { stock: true },
        });

        if (!dbItem)
          throw new Error(`Item with id ${product.productId} not found`);

        if (dbItem.stock < product.quantity) {
          throw new Error(
            `Not enough stock for item ${product.productId}. Available: ${dbItem.stock}, requested: ${product.quantity}`,
          );
        }

        await tx.product.update({
          where: { id: product.productId },
          data: {
            stock: { decrement: product.quantity },
          },
        });
      }
    });

    console.log("Payment success stored:", {
      email,
      amount: eventObject.amount_total,
      paymentId: eventObject.id,
      products: products,
    });
  } catch (error) {
    console.error("Error in handleItemPaymentSuccess:", error);
  }
};

const handleItemPaymentFailure = async (eventObject: Stripe.PaymentIntent) => {
  try {
    const customerId = eventObject.customer;
    const customer = await stripe.customers.retrieve(customerId as string);
    const email = (customer as Stripe.Customer).email;

    if (!email) throw new Error("Customer email not found.");

    const metadata = eventObject.metadata;
    if (!metadata) throw new Error("Metadata missing in Stripe session.");

    const products = JSON.parse(metadata.products) as TPurchasedProduct;
    const patientId = metadata.patient_id as string;

    if (products.products.length === 0) {
      throw new Error("Purchased Products are missing in session metadata.");
    }

    if (!patientId) {
      throw new Error("Patient ID is missing in session metadata.");
    }

    if (!eventObject.amount) throw new Error("Invalid amount.");

    await prisma.$transaction(async (prisma) => {
      await prisma.productPayment.create({
        data: {
          email,
          patientId,
          paymentIntent: eventObject.id as string,
          amount: eventObject.amount / 100,
          status: "FAILED",
          products: {
            create: products.products.map((product) => ({
              productId: product.productId,
              quantity: product.quantity,
              patientId: patientId,
              product: {
                connect: { id: product.id }, // internal product id from your Product table
              },
            })),
          },
        },
      });
    });

    console.log("Payment failure stored:", {
      email,
      amount: eventObject.amount / 100,
      paymentId: eventObject.id,
    });
  } catch (error) {
    console.error("Error in handlePaymentFailure:", error);
  }
};

const handleItemRefundUpdated = async (refund: Stripe.Refund) => {
  try {
    console.log("Refund updated event:", refund);

    const paymentIntentId = refund.payment_intent;
    const chargeId = refund.charge;

    if (!paymentIntentId || !chargeId) {
      console.warn("Missing paymentIntentId or chargeId in refund");
      return;
    }

    const charge = await stripe.charges.retrieve(chargeId as string);
    const email = charge.billing_details?.email;

    if (!email) {
      console.warn("Missing billing email in charge data");
      return;
    }

    const existingPayment = await prisma.productPayment.findUnique({
      where: {
        email_paymentIntent: {
          email,
          paymentIntent: paymentIntentId as string,
        },
      },
      include: {
        products: true, // Include PurchasedItem
      },
    });

    if (!existingPayment) {
      console.warn("No matching payment found for refund update");
      return;
    }

    let newStatus: PaymentStatus | undefined;
    let quantityDelta = 0;

    switch (refund.status) {
      case "succeeded":
        newStatus = PaymentStatus.REFUNDED;
        quantityDelta = 1; // Add quantity back
        break;
      case "pending":
        newStatus = PaymentStatus.REFUND_PENDING;
        break;
      case "failed":
        newStatus = PaymentStatus.REFUND_FAILED;
        break;
      case "canceled":
        newStatus = PaymentStatus.SUCCESSFUL;
        quantityDelta = -1; // Reduce quantity again
        break;
      default:
        console.warn("Unhandled refund status:", refund.status);
        return;
    }

    await prisma.$transaction(async (tx) => {
      // Update payment status
      await tx.productPayment.update({
        where: {
          email_paymentIntent: {
            email,
            paymentIntent: paymentIntentId as string,
          },
        },
        data: {
          status: newStatus!,
        },
      });

      // Adjust stock if needed
      if (quantityDelta !== 0) {
        for (const purchased of existingPayment.products) {
          await tx.product.update({
            where: {
              id: purchased.productId,
            },
            data: {
              stock: {
                increment: quantityDelta * purchased.quantity,
              },
            },
          });
        }
      }
    });

    console.log(
      `Refund status '${refund.status}' handled. Updated status to '${
        PaymentStatus[newStatus!]
      }'`,
    );
  } catch (err) {
    console.error("Error handling refund update:", err);
  }
};
