const express = require("express");

const app = express();
const stripeKey = process.env.STRIPE_KEY;
const port = process.env.PORT || 3000;

app.get("/health", (_req, res) => res.json({ ok: true, billing: Boolean(stripeKey) }));
app.listen(port);
