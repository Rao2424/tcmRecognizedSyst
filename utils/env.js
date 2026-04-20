const API_ENV_URLS = {
  local: "http://127.0.0.1:8000",
  lan: "http://192.168.1.100:8000",
  prod: "https://your-production-api.example.com",
};

const DEFAULT_API_ENV = "local";

function getMiniProgramEnvVersion() {
  try {
    const accountInfo = wx.getAccountInfoSync();
    return accountInfo.miniProgram.envVersion || "develop";
  } catch (error) {
    return "develop";
  }
}

function resolveApiEnv(envVersion) {
  try {
    const overrideEnv = wx.getStorageSync("apiEnv");
    if (overrideEnv && API_ENV_URLS[overrideEnv]) {
      return overrideEnv;
    }
  } catch (error) {
    // Ignore storage access issues and fall back to defaults.
  }

  if (envVersion === "release") {
    return "prod";
  }

  return DEFAULT_API_ENV;
}

function resolveApiConfig() {
  const envVersion = getMiniProgramEnvVersion();
  const env = resolveApiEnv(envVersion);

  return {
    env,
    envVersion,
    baseUrl: API_ENV_URLS[env],
  };
}

module.exports = {
  API_ENV_URLS,
  resolveApiConfig,
};
