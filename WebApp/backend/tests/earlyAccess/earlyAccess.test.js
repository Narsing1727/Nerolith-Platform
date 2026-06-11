const request = require("supertest")
const app = require("../../src/app")

describe("Early Access", () => {
  it("POST /api/early-access — registers a new email", async () => {
    const res = await request(app)
      .post("/api/early-access")
      .send({ email: "test@nerolith.io" })

    expect([201, 409]).toContain(res.statusCode)
  })

  it("POST /api/early-access — rejects invalid email", async () => {
    const res = await request(app)
      .post("/api/early-access")
      .send({ email: "notanemail" })

    expect(res.statusCode).toBe(400)
    expect(res.body.success).toBe(false)
  })

  it("POST /api/early-access — rejects missing email", async () => {
    const res = await request(app)
      .post("/api/early-access")
      .send({})

    expect(res.statusCode).toBe(400)
  })

  it("GET /api/early-access — returns list", async () => {
    const res = await request(app).get("/api/early-access")
    expect(res.statusCode).toBe(200)
    expect(res.body.success).toBe(true)
  })
})