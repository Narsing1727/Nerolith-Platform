const app = require("./app")
const env = require("./config/env")
const logger = require("./config/logger")
const pool = require("./config/db")

const start = async () => {
  await pool.query("SELECT 1")
  logger.info("Database connected")

  app.listen(env.port, () => {
    logger.info(`Server running on port ${env.port}`)
  })
}

start()