const router = require("express").Router();
const billing = require("../services/billing");

router.post("/", async (req, res) => {
  const sub = await billing.subscribe(req.body.customerId, req.body.priceId);
  res.status(201).json(sub);
});

router.delete("/:id", async (req, res) => {
  await billing.cancel(req.params.id);
  res.status(204).end();
});

module.exports = router;
