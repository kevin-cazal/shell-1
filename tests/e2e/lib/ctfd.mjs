const DEFAULT_URL = "http://localhost:9042/ctfd/default";
const DEFAULT_ADMIN_TOKEN =
  "ctfd_0cb2ccac1f05fd0d545f187bb21bed7a7a630eb974a47e6d2c76ce69f7736afa";

/**
 * @param {string} token
 */
function authHeaders(token) {
  return {
    Authorization: `Token ${token}`,
    "Content-Type": "application/json",
    Accept: "application/json",
  };
}

/**
 * @param {string} html
 */
function parseLoginNonce(html) {
  const m = html.match(/name="nonce"\s+type="hidden"\s+value="([^"]+)"/);
  return m?.[1] ?? null;
}

/**
 * @param {string} baseUrl
 * @param {string} token
 * @param {string} path
 * @param {RequestInit & { params?: Record<string, string> }} [init]
 */
async function api(baseUrl, token, path, init = {}) {
  const params = init.params
    ? `?${new URLSearchParams(init.params).toString()}`
    : "";
  const url = `${baseUrl.replace(/\/$/, "")}${path}${params}`;
  const { params: _p, ...rest } = init;
  const res = await fetch(url, {
    ...rest,
    headers: { ...authHeaders(token), ...rest.headers },
  });
  let body;
  const text = await res.text();
  try {
    body = text ? JSON.parse(text) : {};
  } catch {
    throw new Error(
      `${init.method ?? "GET"} ${path} → non-JSON (${res.status}): ${text.slice(0, 200)}`,
    );
  }
  if (!res.ok || body.success === false) {
    const err = body.errors ? JSON.stringify(body.errors) : text.slice(0, 300);
    throw new Error(
      `${init.method ?? "GET"} ${path} failed (${res.status}): ${err}`,
    );
  }
  return body;
}

/**
 * @param {string} baseUrl
 * @param {string} name
 * @param {string} password
 */
async function sessionLoginAndCreateToken(baseUrl, name, password) {
  const loginUrl = `${baseUrl.replace(/\/$/, "")}/login`;
  const jar = new Map();

  /** @param {Response} res */
  function storeCookies(res) {
    const raw = res.headers.getSetCookie?.() ?? [];
    for (const line of raw) {
      const part = line.split(";")[0];
      const eq = part.indexOf("=");
      if (eq > 0) {
        jar.set(part.slice(0, eq), part.slice(eq + 1));
      }
    }
  }

  function cookieHeader() {
    return [...jar.entries()].map(([k, v]) => `${k}=${v}`).join("; ");
  }

  let res = await fetch(loginUrl);
  storeCookies(res);
  let nonce = parseLoginNonce(await res.text());
  if (!nonce) {
    throw new Error("Could not parse CSRF nonce from CTFd login page");
  }

  res = await fetch(loginUrl, {
    method: "POST",
    redirect: "manual",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      Cookie: cookieHeader(),
    },
    body: new URLSearchParams({ name, password, nonce }).toString(),
  });
  storeCookies(res);

  res = await fetch(loginUrl, { headers: { Cookie: cookieHeader() } });
  storeCookies(res);
  nonce = parseLoginNonce(await res.text()) ?? nonce;

  const tokenRes = await fetch(
    `${baseUrl.replace(/\/$/, "")}/api/v1/tokens`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Cookie: cookieHeader(),
        "CSRF-Token": nonce,
      },
      body: JSON.stringify({
        expiration: "2099-12-31",
        description: "shell101-e2e",
      }),
    },
  );
  const tokenBody = await tokenRes.json();
  if (!tokenRes.ok || !tokenBody.success) {
    throw new Error(
      `Token creation failed: ${JSON.stringify(tokenBody).slice(0, 300)}`,
    );
  }
  const value = tokenBody.data?.value;
  if (!value) {
    throw new Error("Token response missing data.value");
  }
  return value;
}

export class CtfdClient {
  /**
   * @param {{ baseUrl?: string, adminToken?: string, userToken?: string }} opts
   */
  constructor(opts = {}) {
    this.baseUrl = opts.baseUrl ?? process.env.CTFD_URL ?? DEFAULT_URL;
    this.adminToken =
      opts.adminToken ?? process.env.CTFD_ADMIN_TOKEN ?? DEFAULT_ADMIN_TOKEN;
    this.userToken = opts.userToken ?? null;
    /** @type {Map<string, number>} */
    this.challengeIds = new Map();
  }

  async ping() {
    await this.fetchAllChallenges();
  }

  async fetchAllChallenges() {
    const all = [];
    let page = 1;
    while (true) {
      const body = await api(this.baseUrl, this.adminToken, "/api/v1/challenges", {
        params: { view: "admin", page: String(page), max_per_page: "100" },
      });
      all.push(...(body.data ?? []));
      const next = body.meta?.pagination?.next;
      if (!next) {
        break;
      }
      page = Number(next);
    }
    return all;
  }

  /** @param {string[]} requiredNames */
  async loadChallenges(requiredNames) {
    const list = await this.fetchAllChallenges();
    for (const ch of list) {
      this.challengeIds.set(ch.name, ch.id);
    }
    const missing = requiredNames.filter((n) => !this.challengeIds.has(n));
    if (missing.length) {
      throw new Error(
        `CTFd missing ${missing.length} challenge(s):\n${missing.map((n) => `  - ${n}`).join("\n")}\nDeploy with deploy_challenges.py --force`,
      );
    }
  }

  /** @returns {number} */
  challengeId(name) {
    const id = this.challengeIds.get(name);
    if (id == null) {
      throw new Error(`Unknown challenge: ${name}`);
    }
    return id;
  }

  async createE2eUser() {
    const stamp = new Date().toISOString().replace(/[:.]/g, "-");
    const name = `e2e-${stamp}`;
    const password = `e2e-${Math.random().toString(36).slice(2, 14)}`;
    const email = `${name}@example.com`;

    await api(this.baseUrl, this.adminToken, "/api/v1/users", {
      method: "POST",
      body: JSON.stringify({ name, email, password, verified: true }),
    });

    const token = await sessionLoginAndCreateToken(
      this.baseUrl,
      name,
      password,
    );
    this.userToken = token;
    return { name, password, token };
  }

  /**
   * @param {string} challengeName
   * @param {string} submission
   */
  async submit(challengeName, submission) {
    if (!this.userToken) {
      throw new Error("No user token — call createE2eUser() first");
    }
    const challenge_id = this.challengeId(challengeName);
    const body = await api(
      this.baseUrl,
      this.userToken,
      "/api/v1/challenges/attempt",
      {
        method: "POST",
        body: JSON.stringify({ challenge_id, submission }),
      },
    );
    const status = body.data?.status;
    const message = body.data?.message ?? "";
    if (status !== "correct") {
      throw new Error(
        `Flag rejected for "${challengeName}": status=${status} message=${message} submission=${submission}`,
      );
    }
    return { status, message };
  }
}

export { DEFAULT_URL, DEFAULT_ADMIN_TOKEN };
