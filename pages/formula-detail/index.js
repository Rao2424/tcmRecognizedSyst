const { getFormulaDetail } = require("../../services/api");

Page({
  data: {
    id: null,
    loading: true,
    errorText: "",
    detail: null
  },

  onLoad(options) {
    const id = options.id;
    this.setData({ id });
    this.loadDetail(id);
  },

  async loadDetail(id) {
    if (!id) {
      this.setData({
        loading: false,
        errorText: "缺少方剂编号"
      });
      return;
    }

    this.setData({ loading: true, errorText: "" });
    try {
      const detail = await getFormulaDetail(id);
      this.setData({ detail });
    } catch (error) {
      this.setData({
        errorText: error.message || "方剂详情获取失败"
      });
    } finally {
      this.setData({ loading: false });
    }
  },

  openHerb(event) {
    const { id } = event.currentTarget.dataset;
    if (!id) {
      return;
    }
    wx.navigateTo({
      url: `/pages/herb-detail/index?id=${id}`
    });
  }
});
