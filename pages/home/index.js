const { syncTabBar } = require("../../utils/tabbar");
const { getOverview } = require("../../services/api");

Page({
  data: {
    keyword: "",
    loading: false,
    overview: {
      herbCount: 0,
      formulaCount: 0,
      categoryCount: 0,
    },
    quickEntries: [
      {
        title: "中药查询",
        desc: "快速检索药材功效、主治与用法",
        route: "/pages/query/index?mode=herb",
        tone: "forest",
      },
      {
        title: "方剂查询",
        desc: "查看方剂组成、主治方向与出处",
        route: "/pages/query/index?mode=formula",
        tone: "amber",
      },
      {
        title: "数据分析",
        desc: "从图形卡片中理解中医药分布特征",
        route: "/pages/analysis/index",
        tone: "mist",
      },
      {
        title: "拍照识别",
        desc: "预留拍照识别入口，便于后续扩展",
        route: "/pages/recognition/index",
        tone: "clay",
      }
    ],
    featuredHerbs: ["黄芪", "当归", "金银花", "甘草"],
    featuredFormulas: ["四君子汤", "六味地黄丸", "银翘散", "逍遥散"],
  },

  onShow() {
    syncTabBar(this, 0);
    this.loadOverview();
  },

  onKeywordInput(event) {
    this.setData({ keyword: event.detail.value });
  },

  submitSearch() {
    const { keyword } = this.data;
    if (keyword && keyword.trim()) {
      wx.setStorageSync("pendingQueryKeyword", keyword.trim());
      wx.setStorageSync("pendingQueryMode", "herb");
    }
    wx.switchTab({ url: "/pages/query/index" });
  },

  navigateEntry(event) {
    const { route } = event.currentTarget.dataset;
    if (route.indexOf("/pages/query/index") === 0) {
      const mode = route.indexOf("mode=formula") > -1 ? "formula" : "herb";
      wx.setStorageSync("pendingQueryMode", mode);
      wx.switchTab({ url: "/pages/query/index" });
      return;
    }

    if (route === "/pages/analysis/index") {
      wx.switchTab({ url: route });
      return;
    }

    wx.navigateTo({ url: route });
  },

  goWithPreset(event) {
    const { keyword, mode } = event.currentTarget.dataset;
    wx.setStorageSync("pendingQueryKeyword", keyword);
    wx.setStorageSync("pendingQueryMode", mode);
    wx.switchTab({ url: "/pages/query/index" });
  },

  async loadOverview() {
    this.setData({ loading: true });
    try {
      const overview = await getOverview();
      this.setData({ overview });
    } catch (error) {
      wx.showToast({
        title: "统计数据获取失败",
        icon: "none",
      });
    } finally {
      this.setData({ loading: false });
    }
  }
});
