Component({
  data: {
    selected: 0,
    tabs: [
      { text: "首页", route: "/pages/home/index", icon: "庭" },
      { text: "查询", route: "/pages/query/index", icon: "索" },
      { text: "分析", route: "/pages/analysis/index", icon: "析" },
      { text: "我的", route: "/pages/profile/index", icon: "我" }
    ],
  },
  methods: {
    switchTab(event) {
      const { index } = event.currentTarget.dataset;
      const target = this.data.tabs[index];
      if (!target || index === this.data.selected) {
        return;
      }

      this.setData({ selected: index });
      wx.switchTab({ url: target.route });
    },
  },
});
