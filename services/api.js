const { request } = require("../utils/request");

function getOverview() {
  return request({ url: "/api/statistics/overview" });
}

function getHerbEfficacyStats() {
  return request({ url: "/api/statistics/herb-efficacy" });
}

function getFormulaCategoryStats() {
  return request({ url: "/api/statistics/formula-category" });
}

function getFormulaHerbTopStats() {
  return request({ url: "/api/statistics/formula-herb-top" });
}

function getHerbList(data) {
  return request({ url: "/api/herbs", data });
}

function getHerbDetail(id) {
  return request({ url: `/api/herbs/${id}` });
}

function getFormulaList(data) {
  return request({ url: "/api/formulas", data });
}

function getFormulaDetail(id) {
  return request({ url: `/api/formulas/${id}` });
}

function normalizeUploadPayload(fileInput) {
  if (typeof fileInput === "string") {
    return {
      filePath: fileInput,
      clientFilename: "",
      clientContentType: "",
    };
  }

  const filePath =
    (fileInput &&
      (fileInput.filePath ||
        fileInput.tempFilePath ||
        fileInput.path ||
        fileInput.url)) ||
    "";

  const clientFilename =
    (fileInput &&
      (fileInput.clientFilename || fileInput.name || fileInput.fileName)) ||
    "";

  const clientContentType =
    (fileInput &&
      (fileInput.clientContentType || fileInput.mimeType || fileInput.type)) ||
    "";

  return {
    filePath,
    clientFilename,
    clientContentType,
  };
}

function materializeUploadPayload(uploadPayload) {
  return new Promise((resolve, reject) => {
    if (!uploadPayload.filePath) {
      reject(new Error("未获取到可上传的图片文件"));
      return;
    }

    if (!/^https?:\/\/tmp\//i.test(uploadPayload.filePath)) {
      resolve(uploadPayload);
      return;
    }

    wx.saveFile({
      tempFilePath: uploadPayload.filePath,
      success: (res) => {
        console.log("[recognition] materialized temp file", {
          from: uploadPayload.filePath,
          to: res.savedFilePath,
        });

        resolve({
          ...uploadPayload,
          filePath: res.savedFilePath,
          savedFilePath: res.savedFilePath,
        });
      },
      fail: (error) => {
        console.error("[recognition] materialize temp file fail", {
          filePath: uploadPayload.filePath,
          error,
        });

        reject(new Error("图片临时文件转换失败，请重新拍照后重试"));
      },
    });
  });
}

function cleanupSavedFile(savedFilePath) {
  if (!savedFilePath) {
    return;
  }

  wx.removeSavedFile({
    filePath: savedFilePath,
    fail: () => {},
  });
}

function recognizeHerbImage(fileInput, sourceType = "album") {
  const app = getApp();
  const baseUrl = app && app.globalData ? app.globalData.apiBaseUrl : "";
  const url = `${baseUrl}/api/recognitions/herb-image`;
  const initialPayload = normalizeUploadPayload(fileInput);

  return new Promise((resolve, reject) => {
    materializeUploadPayload(initialPayload)
      .then((uploadPayload) => {
        console.log("[recognition] upload start", {
          url,
          sourceType,
          filePath: uploadPayload.filePath,
          clientFilename: uploadPayload.clientFilename,
          clientContentType: uploadPayload.clientContentType,
        });

        wx.uploadFile({
          url,
          filePath: uploadPayload.filePath,
          name: "file",
          formData: {
            sourceType,
            clientFilename: uploadPayload.clientFilename,
            clientContentType: uploadPayload.clientContentType,
          },
          timeout: 20000,
          success: (res) => {
            let payload = {};

            cleanupSavedFile(uploadPayload.savedFilePath);

            try {
              payload = JSON.parse(res.data || "{}");
            } catch (error) {
              reject(new Error("识别服务返回了无法解析的结果"));
              return;
            }

            console.log("[recognition] upload success", {
              statusCode: res.statusCode,
              payload,
            });

            if (res.statusCode >= 200 && res.statusCode < 300 && payload.code === 0) {
              resolve(payload.data);
              return;
            }

            reject(new Error(payload.message || `识别失败(${res.statusCode})`));
          },
          fail: (error) => {
            cleanupSavedFile(uploadPayload.savedFilePath);

            console.error("[recognition] upload fail", {
              url,
              sourceType,
              filePath: uploadPayload.filePath,
              error,
            });

            reject(
              new Error(
                (error && error.errMsg) || "图片上传失败，请检查网络或后端服务"
              )
            );
          },
        });
      })
      .catch(reject);
  });
}

module.exports = {
  getOverview,
  getHerbEfficacyStats,
  getFormulaCategoryStats,
  getFormulaHerbTopStats,
  getHerbList,
  getHerbDetail,
  getFormulaList,
  getFormulaDetail,
  recognizeHerbImage,
};
