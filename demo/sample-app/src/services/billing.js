const Stripe = require("stripe");
const db = require("../db");
const stripe = Stripe(process.env.STRIPE_SECRET_KEY);

async function subscribe(customerId, priceId) {
  const { rows } = await db.query("SELECT stripe_id FROM customers WHERE id = $1", [customerId]);
  const sub = await stripe.subscriptions.create({ customer: rows[0].stripe_id, items: [{ price: priceId }] });
  await db.query("UPDATE customers SET plan = $1 WHERE id = $2", [priceId, customerId]);
  return sub;
}

async function cancel(subscriptionId) {
  return stripe.subscriptions.cancel(subscriptionId);
}

module.exports = { subscribe, cancel };
