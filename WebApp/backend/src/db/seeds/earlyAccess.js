const { query } = require("../client")

const seed = async () => {
  await query(
    "INSERT INTO early_access (email) VALUES ($1) ON CONFLICT DO NOTHING",
    ["test@nerolith.io"]
  )
  console.log("Seed complete")
  process.exit(0)
}

seed()