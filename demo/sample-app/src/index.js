const express = require("express");
const customers = require("./routes/customers");
const subscriptions = require("./routes/subscriptions");

const app = express();
app.use(express.json());
app.get("/health", (req, res) => res.json({ ok: true }));
app.use("/customers", customers);
app.use("/subscriptions", subscriptions);

const port = process.env.PORT || 3000;
app.listen(port, () => console.log(`orbit-api listening on :${port}`));
