import { stripe } from "@/config/stripe-config";
import { TPurchasedProduct } from "@/types/common";
import { createResponse } from "@/utils/createResponse";
import { getToken } from "next-auth/jwt";
import { NextRequest, NextResponse } from "next/server";
import Stripe from "stripe";

/**
 * @swagger
 * /api/stripe/product/checkout:
 *   post:
 *     summary: Create a Stripe checkout session for products
 *     tags: [Stripe]
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - products
 *             properties:
 *               products:
 *                 type: array
 *                 description: Array of products to checkout
 *                 items:
 *                   type: object
 *                   properties:
 *                     productId:
 *                       type: string
 *                       description: Stripe product ID
 *                     quantity:
 *                       type: integer
 *                       description: Product quantity
 *               cartId:
 *                 type: string
 *                 description: Cart ID (required)
 *     responses:
 *       200:
 *         description: Checkout session created successfully
 *         content:
 *           application/json:
 *             example:
 *               status: true
 *               message: "Checkout session created"
 *               data:
 *                 id: "cs_test_123"
 *                 url: "https://checkout.stripe.com/pay/cs_test_123"
 *       400:
 *         description: No products in cart or invalid cart item
 *         content:
 *           application/json:
 *             example:
 *               status: false
 *               message: "Invalid cart item"
 *               data: null
 *       404:
 *         description: No price found for product
 *         content:
 *           application/json:
 *             example:
 *               status: false
 *               message: "No price found for product prod_123"
 *               data: null
 *       500:
 *         description: Internal Server Error
 *         content:
 *           application/json:
 *             example:
 *               status: false
 *               message: "Internal Server Error"
 *               data: null
 */
export async function POST(req: NextRequest) {
  try {
    // const token = await getToken({ req, secret: process.env.NEXTAUTH_SECRET });

    // if (!token || token.role !== "patient") {
    //   return NextResponse.json(createResponse(false, "Unauthorized", null), {
    //     status: 401,
    //   });
    // }

    const data = await req.json();

    const products: TPurchasedProduct = data.products;

    if (
      !Array.isArray(products.products) ||
      products.products.length === 0 ||
      products.cartId === undefined
    ) {
      return NextResponse.json(
        createResponse(false, "No Product in the cart", null),
        { status: 400 },
      );
    }
    const lineItems: Stripe.Checkout.SessionCreateParams.LineItem[] = [];

    for (const product of products.products) {
      const productId = String(product.productId ?? "").trim();
      const quantity = product.quantity ?? 1;

      if (!productId || typeof quantity !== "number" || quantity <= 0) {
        return NextResponse.json(
          createResponse(false, "Invalid cart item", null),
          { status: 400 },
        );
      }

      const prices = await stripe.prices.list({
        product: productId,
        active: true,
      });

      if (!prices.data.length) {
        return NextResponse.json(
          createResponse(
            false,
            `No price found for product ${productId}`,
            null,
          ),
          { status: 404 },
        );
      }

      lineItems.push({
        price: prices.data[0].id,
        quantity,
      });
    }

    const checkoutSession = await stripe.checkout.sessions.create({
      payment_method_types: ["card"],
      line_items: lineItems,
      mode: "payment",
      // customer_email: email,
      success_url: `${process.env.URL}/patient/store?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${process.env.URL}/patient/store?session_id={CHECKOUT_SESSION_ID}`,
      metadata: {
        products: JSON.stringify(products),
        payment_for: "product",
        // patient_id: token.id as string,
      },
    });

    return NextResponse.json(
      createResponse(true, "Checkout session created", checkoutSession),
      { status: 200 },
    );
  } catch (error) {
    console.log(error);
    if (error instanceof Stripe.errors.StripeError) {
      return NextResponse.json(createResponse(false, error.message, null), {
        status: 400,
      });
    }

    const errorMessage = error instanceof Error ? error.message : String(error);
    return NextResponse.json(createResponse(false, errorMessage, null), {
      status: 500,
    });
  }
}
