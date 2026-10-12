const router = require("express").Router();
const db = require("../db");

router.get("/", async (req, res) => {
  const { rows } = await db.query("SELECT id, email, plan FROM customers ORDER BY id");
  res.json(rows);
});

router.post("/", async (req, res) => {
  const { email } = req.body;
  const { rows } = await db.query("INSERT INTO customers (email) VALUES ($1) RETURNING *", [email]);
  res.status(201).json(rows[0]);
});

module.exports = router;
