const repository = require("./earlyAccess.repository")
const ApiError = require("../../utils/ApiError")

const register = async (email) => {
  const existing = await repository.findByEmail(email)

  if (existing) {
    throw new ApiError(409, "Email already registered")
  }

  const entry = await repository.insert(email)
  return entry
}

const getAll = async () => {
  return await repository.findAll()
}

module.exports = { register, getAll }