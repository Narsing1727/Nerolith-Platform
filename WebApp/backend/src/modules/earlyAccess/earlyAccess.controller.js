const service = require("./earlyAccess.service")
const ApiResponse = require("../../utils/ApiResponse")

const join = async (req, res, next) => {
  try {
    const entry = await service.register(req.body.email)
    ApiResponse.success(res, 201, entry)
  } catch (err) {
    next(err)
  }
}

const list = async (req, res, next) => {
  try {
    const entries = await service.getAll()
    ApiResponse.success(res, 200, entries)
  } catch (err) {
    next(err)
  }
}

module.exports = { join, list }