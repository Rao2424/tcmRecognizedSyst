const { recognizeHerbImage } = require("../../services/api");

function formatConfidence(value) {
  const confidence = Number(value);
  if (Number.isNaN(confidence)) {
    return "--";
  }

  return `${Math.round(confidence * 100)}%`;
}

function decorateMatchedResult(result) {
  if (!result) {
    return null;
  }

  return {
    ...result,
    confidenceText: formatConfidence(result.confidence),
    reasonText: result.reason || "已命中本地药材库。",
  };
}

function decorateCandidates(candidates) {
  return (candidates || []).map((item) => ({
    ...item,
    confidenceText: formatConfidence(item.confidence),
    reasonText: item.reason || "暂无补充说明",
  }));
}

function getFileExtension(filePath) {
  if (!filePath || typeof filePath !== "string") {
    return "";
  }

  const cleanPath = filePath.split("?")[0];
  const match = cleanPath.match(/\.([a-zA-Z0-9]+)$/);
  return match ? match[1].toLowerCase() : "";
}

function inferContentType(filePath, rawContentType) {
  if (rawContentType && /^image\//.test(rawContentType)) {
    return rawContentType;
  }

  const extension = getFileExtension(filePath);
  if (extension === "jpg" || extension === "jpeg") {
    return "image/jpeg";
  }

  if (extension === "png") {
    return "image/png";
  }

  return "";
}

function normalizeSelectedFile(file, fallbackPath) {
  const filePath =
    (file && (file.tempFilePath || file.path || file.filePath)) || fallbackPath || "";

  if (!filePath) {
    return null;
  }

  const fileName = filePath.split(/[\\/]/).pop() || "";
  return {
    filePath,
    size: Number(file && file.size) || 0,
    clientFilename: fileName,
    clientContentType: inferContentType(filePath, file && (file.type || file.mimeType)),
  };
}

Page({
  data: {
    imageUrl: "",
    selectedFile: null,
    sourceType: "",
    sourceTypeLabel: "未选择",
    uploading: false,
    analyzing: false,
    result: null,
    candidates: [],
    errorText: "",
    statusText: "",
    unmatchedName: "",
    unmatchedText: "",
    hasResult: false,
    actionText: "开始识别",
  },

  onUnload() {
    this.clearStatusTimer();
  },

  clearStatusTimer() {
    if (this.statusTimer) {
      clearTimeout(this.statusTimer);
      this.statusTimer = null;
    }
  },

  selectImage(sourceType) {
    wx.chooseImage({
      count: 1,
      sizeType: ["original", "compressed"],
      sourceType: [sourceType],
      success: (res) => {
        const file =
          normalizeSelectedFile(
            res.tempFiles && res.tempFiles[0],
            res.tempFilePaths && res.tempFilePaths[0]
          ) || null;

        if (!file) {
          wx.showToast({
            title: "未获取到可用图片，请重试",
            icon: "none",
          });
          return;
        }

        if (file.size > 5 * 1024 * 1024) {
          wx.showToast({
            title: "图片不能超过 5MB",
            icon: "none",
          });
          return;
        }

        console.log("[recognition] selected image", file);

        this.setData({
          imageUrl: file.filePath,
          selectedFile: file,
          sourceType,
          sourceTypeLabel: sourceType === "camera" ? "拍照上传" : "相册上传",
          uploading: false,
          analyzing: false,
          result: null,
          candidates: [],
          errorText: "",
          statusText: "",
          unmatchedName: "",
          unmatchedText: "",
          hasResult: false,
          actionText: "开始识别",
        });
      },
      fail: (error) => {
        if (error && error.errMsg && error.errMsg.indexOf("cancel") > -1) {
          return;
        }

        wx.showToast({
          title: "选择图片失败，请重试",
          icon: "none",
        });
      },
    });
  },

  takePhoto() {
    this.selectImage("camera");
  },

  chooseFromAlbum() {
    this.selectImage("album");
  },

  async startRecognition() {
    const { imageUrl, selectedFile, sourceType, uploading, analyzing } = this.data;
    if (!imageUrl) {
      wx.showToast({
        title: "请先选择一张药材图片",
        icon: "none",
      });
      return;
    }

    if (uploading || analyzing) {
      return;
    }

    this.clearStatusTimer();
    this.setData({
      uploading: true,
      analyzing: false,
      errorText: "",
      result: null,
      candidates: [],
      unmatchedName: "",
      unmatchedText: "",
      hasResult: false,
      statusText: "正在上传图片...",
      actionText: "正在上传...",
    });

    this.statusTimer = setTimeout(() => {
      this.setData({
        uploading: false,
        analyzing: true,
        statusText: "正在分析药材特征...",
        actionText: "正在识别...",
      });
    }, 600);

    try {
      const response = await recognizeHerbImage(
        selectedFile || imageUrl,
        sourceType || "album"
      );
      const unmatchedName = response.unmatchedName || "";

      this.clearStatusTimer();
      this.setData({
        uploading: false,
        analyzing: false,
        result: decorateMatchedResult(response.matched),
        candidates: decorateCandidates(response.candidates),
        unmatchedName,
        unmatchedText: unmatchedName
          ? `未匹配到本地药材库：${unmatchedName}，可以尝试重新拍摄更清晰的图片。`
          : "未匹配到本地药材库，可以尝试重新拍摄更清晰的图片。",
        hasResult: true,
        statusText: response.matched
          ? "识别完成，已匹配到药材库。"
          : "识别完成，但暂未匹配到本地药材。",
        actionText: "重新识别",
      });
    } catch (error) {
      this.clearStatusTimer();
      this.setData({
        uploading: false,
        analyzing: false,
        errorText: error.message || "识别失败，请稍后重试",
        statusText: "",
        unmatchedText: "",
        hasResult: false,
        actionText: "重新识别",
      });
    }
  },

  viewDetail() {
    const { result } = this.data;
    if (!result || !result.herbId) {
      return;
    }

    wx.navigateTo({
      url: `/pages/herb-detail/index?id=${result.herbId}`,
    });
  },
});
