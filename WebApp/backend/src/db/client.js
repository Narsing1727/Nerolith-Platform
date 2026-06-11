const pool = require("../config/db")

const query = (text, params) => pool.query(text, params)

module.exports = { query }