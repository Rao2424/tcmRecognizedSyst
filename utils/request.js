function request(options) {
  const app = getApp();
  const baseUrl = app && app.globalData ? app.globalData.apiBaseUrl : "";
  const url = `${baseUrl}${options.url}`;
  const method = options.method || "GET";
  const data = options.data || {};

  console.log("[request] start", {
    url,
    method,
    data,
    apiEnv: app && app.globalData ? app.globalData.apiEnv : "",
    apiEnvVersion: app && app.globalData ? app.globalData.apiEnvVersion : "",
  });

  return new Promise((resolve, reject) => {
    wx.request({
      url,
      method,
      data,
      timeout: options.timeout || 10000,
      success: (res) => {
        const payload = res.data || {};

        console.log("[request] success", {
          url,
          statusCode: res.statusCode,
          payload,
        });

        if (res.statusCode >= 200 && res.statusCode < 300 && payload.code === 0) {
          resolve(payload.data);
          return;
        }

        reject(new Error(payload.message || `请求失败(${res.statusCode})`));
      },
      fail: (error) => {
        console.error("[request] fail", {
          url,
          method,
          data,
          error,
        });

        reject(
          new Error(
            (error && error.errMsg) || "网络请求失败，请检查后端地址或开发者工具设置"
          )
        );
      },
    });
  });
}

module.exports = {
  request,
};
