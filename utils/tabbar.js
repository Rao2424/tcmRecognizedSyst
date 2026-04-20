function syncTabBar(pageInstance, selected) {
  if (!pageInstance || typeof pageInstance.getTabBar !== "function") {
    return;
  }

  const tabBar = pageInstance.getTabBar();
  if (tabBar && typeof tabBar.setData === "function") {
    tabBar.setData({ selected });
  }
}

module.exports = {
  syncTabBar,
};
