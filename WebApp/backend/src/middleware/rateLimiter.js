const rateLimit = require("express-rate-limit")

const earlyAccessLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 10,
  message: { success: false, message: "Too many requests, please try again later" },
})

module.exports = { earlyAccessLimiter }