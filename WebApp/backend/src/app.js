const express = require("express")
const cors = require("cors")
const errorHandler = require("./middleware/errorHandler")
const earlyAccessRoutes = require("./modules/earlyAccess/earlyAccess.routes")

const app = express()

app.use(cors({
  origin: ["http://localhost:5173", "https://www.nerolith.in", "https://nerolith.in"],
  methods: ["GET", "POST"],
}))

app.use(express.json())

app.use("/api/early-access", earlyAccessRoutes)
app.use("/api/waitlist", earlyAccessRoutes)

app.use(errorHandler)

module.exports = app