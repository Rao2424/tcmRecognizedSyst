const { syncTabBar } = require("../../utils/tabbar");
const { getOverview } = require("../../services/api");

Page({
  data: {
    projectName: "本草视界",
    apiBaseUrl: "",
    errorText: "",
    overview: {
      herbCount: 0,
      formulaCount: 0,
      categoryCount: 0,
    },
    shortcutCards: [
      {
        title: "中药材检索",
        desc: "按名称、别名和功效快速查找",
        badge: "常用",
        tone: "forest",
        mode: "herb",
      },
      {
        title: "方剂检索",
        desc: "直接切到方剂视角继续查询",
        badge: "推荐",
        tone: "amber",
        mode: "formula",
      },
      {
        title: "统计分析",
        desc: "查看分类分布和高频药材排行",
        badge: "洞察",
        tone: "mist",
        target: "analysis",
      },
      {
        title: "拍照识别",
        desc: "从图片入口衔接后续识别流程",
        badge: "扩展",
        tone: "clay",
        target: "recognition",
      },
    ],
    serviceCards: [
      {
        title: "收藏夹",
        desc: "适合沉淀常查药材、常用方剂和学习清单",
        meta: "规划中",
      },
      {
        title: "最近搜索",
        desc: "保留高频关键词，回看更顺手",
        meta: "规划中",
      },
      {
        title: "识别记录",
        desc: "后续可串起拍照识别与详情复习",
        meta: "二期扩展",
      },
    ],
    statusTags: ["查询主流程可用", "统计接口已接入", "识别入口已预留"],
  },

  onShow() {
    syncTabBar(this, 3);
    this.loadPageData();
  },

  async loadPageData() {
    const app = getApp();
    this.setData({
      apiBaseUrl: app && app.globalData ? app.globalData.apiBaseUrl : "",
      errorText: "",
    });

    try {
      const overview = await getOverview();
      this.setData({ overview });
    } catch (error) {
      this.setData({
        errorText: error.message || "统计信息获取失败",
      });
    }
  },

  openShortcut(event) {
    const { mode, target } = event.currentTarget.dataset;

    if (target === "analysis") {
      wx.switchTab({ url: "/pages/analysis/index" });
      return;
    }

    if (target === "recognition") {
      wx.navigateTo({ url: "/pages/recognition/index" });
      return;
    }

    if (mode) {
      wx.setStorageSync("pendingQueryMode", mode);
      wx.removeStorageSync("pendingQueryKeyword");
      wx.switchTab({ url: "/pages/query/index" });
    }
  },

  showPlannedFeature(event) {
    const { title } = event.currentTarget.dataset;
    wx.showToast({
      title: `${title}将在后续版本开放`,
      icon: "none",
    });
  },

  copyApiBase() {
    if (!this.data.apiBaseUrl) {
      wx.showToast({
        title: "当前还没有可复制的地址",
        icon: "none",
      });
      return;
    }

    wx.setClipboardData({
      data: this.data.apiBaseUrl,
    });
  },
});
