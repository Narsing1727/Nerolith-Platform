const express = require("express")
const router = express.Router()
const controller = require("./earlyAccess.controller")
const { earlyAccessLimiter } = require("../../middleware/rateLimiter")
const { validateEmail } = require("../../middleware/validateRequest")

router.post("/", earlyAccessLimiter, validateEmail, controller.join)
router.get("/", controller.list)

module.exports = router