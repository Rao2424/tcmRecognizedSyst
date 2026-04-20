const { getHerbDetail } = require("../../services/api");

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
        errorText: "缺少药材编号"
      });
      return;
    }

    this.setData({ loading: true, errorText: "" });
    try {
      const detail = await getHerbDetail(id);
      this.setData({ detail });
    } catch (error) {
      this.setData({
        errorText: error.message || "药材详情获取失败"
      });
    } finally {
      this.setData({ loading: false });
    }
  }
});
