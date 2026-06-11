const schema = {
  early_access: {
    id: "SERIAL PRIMARY KEY",
    email: "VARCHAR(255) NOT NULL UNIQUE",
    created_at: "TIMESTAMP DEFAULT NOW()",
  },
}

module.exports = schema