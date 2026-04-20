const { syncTabBar } = require("../../utils/tabbar");
const { getHerbList, getFormulaList } = require("../../services/api");

const QUICK_TAGS = {
  herb: ["补气", "清热", "活血", "安神"],
  formula: ["解表", "补益", "理气", "安神"],
};

Page({
  data: {
    mode: "herb",
    keyword: "",
    loading: false,
    refreshing: false,
    errorText: "",
    list: [],
    page: 1,
    pageSize: 10,
    total: 0,
    hasMore: true,
    quickTags: QUICK_TAGS.herb,
  },

  onLoad(options) {
    this.applyRouteOptions(options || {});
  },

  onShow() {
    syncTabBar(this, 1);
    const changed = this.consumePendingState();
    if (!changed && !this.data.list.length) {
      this.fetchList(true);
    }
  },

  onPullDownRefresh() {
    this.setData({ refreshing: true });
    this.fetchList(true).finally(() => {
      this.setData({ refreshing: false });
      wx.stopPullDownRefresh();
    });
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.loading) {
      this.fetchList(false);
    }
  },

  applyRouteOptions(options) {
    const nextMode = options.mode === "formula" ? "formula" : "herb";
    this.setData({
      mode: nextMode,
      keyword: options.keyword || "",
      quickTags: QUICK_TAGS[nextMode],
    });
  },

  consumePendingState() {
    const pendingKeyword = wx.getStorageSync("pendingQueryKeyword");
    const pendingMode = wx.getStorageSync("pendingQueryMode");

    if (!pendingKeyword && !pendingMode) {
      return false;
    }

    this.setData({
      keyword: pendingKeyword || this.data.keyword,
      mode: pendingMode === "formula" ? "formula" : this.data.mode,
      quickTags: QUICK_TAGS[pendingMode === "formula" ? "formula" : this.data.mode],
    });

    wx.removeStorageSync("pendingQueryKeyword");
    wx.removeStorageSync("pendingQueryMode");
    this.fetchList(true);
    return true;
  },

  switchMode(event) {
    const { mode } = event.currentTarget.dataset;
    if (mode === this.data.mode) {
      return;
    }

    this.setData({
      mode,
      list: [],
      total: 0,
      hasMore: true,
      page: 1,
      quickTags: QUICK_TAGS[mode],
      errorText: "",
    });
    this.fetchList(true);
  },

  onKeywordInput(event) {
    this.setData({ keyword: event.detail.value });
  },

  useQuickTag(event) {
    const { keyword } = event.currentTarget.dataset;
    this.setData({ keyword });
    this.fetchList(true);
  },

  submitSearch() {
    this.fetchList(true);
  },

  async fetchList(reset) {
    const { mode, keyword, page, pageSize, list } = this.data;
    const nextPage = reset ? 1 : page;
    this.setData({ loading: true, errorText: "" });

    const params = {
      keyword: keyword.trim(),
      page: nextPage,
      pageSize: pageSize,
    };

    try {
      const response =
        mode === "herb" ? await getHerbList(params) : await getFormulaList(params);
      const mergedList = reset ? response.list : list.concat(response.list);
      const total = response.pagination.total;
      const currentPage = response.pagination.page;

      this.setData({
        list: mergedList,
        total,
        page: currentPage + 1,
        hasMore: mergedList.length < total,
      });
    } catch (error) {
      this.setData({
        errorText: error.message || "数据加载失败",
      });
    } finally {
      this.setData({ loading: false });
    }
  },

  openDetail(event) {
    const { id } = event.currentTarget.dataset;
    const route =
      this.data.mode === "herb"
        ? `/pages/herb-detail/index?id=${id}`
        : `/pages/formula-detail/index?id=${id}`;
    wx.navigateTo({ url: route });
  }
});
