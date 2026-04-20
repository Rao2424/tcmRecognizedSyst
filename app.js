const { resolveApiConfig } = require("./utils/env");

const apiConfig = resolveApiConfig();

App({
  globalData: {
    apiBaseUrl: apiConfig.baseUrl,
    apiEnv: apiConfig.env,
    apiEnvVersion: apiConfig.envVersion,
  },
});
