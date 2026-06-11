const ApiError = require("../utils/ApiError")

const validateEmail = (req, res, next) => {
  const { email } = req.body

  if (!email || typeof email !== "string") {
    return next(new ApiError(400, "Email is required"))
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(email)) {
    return next(new ApiError(400, "Invalid email format"))
  }

  req.body.email = email.toLowerCase().trim()
  next()
}

module.exports = { validateEmail }