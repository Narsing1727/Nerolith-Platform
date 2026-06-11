const db = require("../../db/client")

const insert = async (email) => {
  const result = await db.query(
    "INSERT INTO early_access (email) VALUES ($1) RETURNING *",
    [email]
  )
  return result.rows[0]
}

const findByEmail = async (email) => {
  const result = await db.query(
    "SELECT * FROM early_access WHERE email = $1",
    [email]
  )
  return result.rows[0]
}

const findAll = async () => {
  const result = await db.query("SELECT * FROM early_access ORDER BY created_at DESC")
  return result.rows
}

module.exports = { insert, findByEmail, findAll }