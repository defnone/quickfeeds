import { initDaily } from './daily';
import { updateFeedListData, initFeedListListeners, initSetInterval } from './feedList';
import { initAddfeedModal } from './addFeedModal';
import { summarizeEnetListener as summarizeEventListener } from './utils/summary';
import { loadMoreItems, feedListEventListeners } from './feedItemsList';
import { setButtonStyles, navigationEventListeners } from './navigation';
import { initBadgeUpdate } from './unreadCount';
import { getUserSettings, settingEventListeners as settingsEventListeners, safariDetector } from './settings';
import { fetchAndRenderCategories, initCategoryListeners } from './settingsManageCat';
import { initDailySettings } from './settingsDaily';
import { swipeToReload } from './utils/swipes';

updateFeedListData();
initFeedListListeners();
initSetInterval();

if (window.location.pathname === '/daily') {
    initDaily();
    summarizeEventListener();
}

if (
    window.location.pathname.endsWith('/') ||
    window.location.pathname.endsWith('/all') ||
    window.location.pathname.includes('/category')
) {
    loadMoreItems();
    setButtonStyles();
    navigationEventListeners();
    summarizeEventListener();
    feedListEventListeners();
}

if (window.location.pathname.endsWith('/categories')) {
    async function initCat() {
        await fetchAndRenderCategories();
    }
    initCat();
    initCategoryListeners();
}

if (window.location.pathname.endsWith('/settings')) {
    getUserSettings();
    settingsEventListeners();
    safariDetector();
}

if (window.location.pathname.endsWith('settings/daily')) {
    initDailySettings();
}

initAddfeedModal();
initBadgeUpdate();
swipeToReload();
