const { syncTabBar } = require("../../utils/tabbar");
const {
  getOverview,
  getHerbEfficacyStats,
  getFormulaCategoryStats,
  getFormulaHerbTopStats
} = require("../../services/api");

function withPercent(list) {
  const max = list.length ? list[0].value || 1 : 1;
  return list.map((item) => ({
    name: item.name,
    value: item.value,
    percent: Math.max(12, Math.round((item.value / max) * 100))
  }));
}

Page({
  data: {
    loading: false,
    errorText: "",
    overview: {
      herbCount: 0,
      formulaCount: 0,
      categoryCount: 0
    },
    herbEfficacyList: [],
    formulaCategoryList: [],
    formulaHerbTopList: []
  },

  onShow() {
    syncTabBar(this, 2);
    this.loadAll();
  },

  async loadAll() {
    this.setData({ loading: true, errorText: "" });
    try {
      const [overview, herbEfficacyList, formulaCategoryList, formulaHerbTopList] =
        await Promise.all([
          getOverview(),
          getHerbEfficacyStats(),
          getFormulaCategoryStats(),
          getFormulaHerbTopStats()
        ]);

      this.setData({
        overview,
        herbEfficacyList: withPercent(herbEfficacyList),
        formulaCategoryList: withPercent(formulaCategoryList),
        formulaHerbTopList: withPercent(formulaHerbTopList)
      });
    } catch (error) {
      this.setData({
        errorText: error.message || "分析数据获取失败"
      });
    } finally {
      this.setData({ loading: false });
    }
  }
});
