import { showMessage } from './utils/messages';
import { checkUnreadCount } from './unreadCount';

let isLoading = false;
let lastItemId = null;
let loadedItems = new Set();
let currentUrl = null;
let displayEOF = true;
let stopped = false;

const lsActive = localStorage.getItem('active') ? parseInt(localStorage.getItem('active'), 10) : 1;
const dailyContainer = document.getElementById('daily-container');

function resetConstants() {
    isLoading = false;
    lastItemId = null;
    loadedItems = new Set();
    stopped = false;
}

function setActive(elId) {
    const all = document.getElementById('all');
    const unread = document.getElementById('unread');
    const bg = document.getElementById('button-bg');

    if (elId === 1) {
        bg.style.left = all.offsetLeft + 'px';
        bg.style.width = all.offsetWidth + 'px';
        bg.style.height = all.offsetHeight + 'px';
        all.classList.add('text-white');
        unread.classList.remove('text-white');
        localStorage.setItem('active', 1);

        displayEOF = false;
        currentUrl = '/api/daily/feed';
        resetConstants();
        dailyContainer.innerHTML = '';
        fetchDailyData(currentUrl);
    } else if (elId === 2) {
        bg.style.left = unread.offsetLeft + 'px';
        bg.style.width = unread.offsetWidth + 'px';
        bg.style.height = unread.offsetHeight + 'px';
        unread.classList.add('text-white');
        all.classList.remove('text-white');
        localStorage.setItem('active', 2);

        displayEOF = true;
        currentUrl = '/api/daily/feed?unread=true';
        resetConstants();
        dailyContainer.innerHTML = '';
        fetchDailyData(currentUrl);
    }
    bg.classList.add('transition-all');
}

export function initDaily() {
    if (lsActive === 1) {
        currentUrl = '/api/daily/feed';
    } else {
        currentUrl = '/api/daily/feed?unread=true';
    }

    window.onload = () => {
        setActive(lsActive);
    };

    window.setActive = setActive;

    dailyScrollListener();
}

function fetchDailyData(url) {
    if (stopped) {
        return;
    }
    if (isLoading) {
        return;
    } else {
        isLoading = true;
    }

    if (lastItemId) {
        url += `?last_item_id=${lastItemId}`;
    }

    fetch(url)
        .then((response) => response.json())
        .then((data) => {
            displayDailyData(data);
            isLoading = false;
        })
        .catch((error) => {
            console.error('Error fetching daily data:', error);
            showMessage('Failed to fetch the daily data', 'error');
            isLoading = false;
        });
}

function displayDailyData(data) {
    data.forEach((item) => {
        if (loadedItems.has(item.id)) {
            return;
        }
        loadedItems.add(item.id);
        let options = {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        };
        let pubDate = new Date(item.pub_date);
        let formattedDate = pubDate.toLocaleString('en-GB', options);
        const itemElement = document.createElement('div');
        itemElement.className = 'daily-item';
        itemElement.dataset.id = item.id;
        itemElement.dataset.read = item.read;

        itemElement.innerHTML = dailyHTMLTemplate(item, formattedDate);
        dailyContainer.appendChild(itemElement);
    });
    if (data.length > 0) {
        lastItemId = data[data.length - 1].id;
    } else {
        stopped = true;
        console.log('No more items');
    }
    if (data.length < 3 && displayEOF) {
        const noDataMessage = document.createElement('div');
        noDataMessage.innerHTML = noMoreItemsTemplate();
        dailyContainer.appendChild(noDataMessage);
        displayEOF = false;
    }
}

function dailyHTMLTemplate(item, formattedDate) {
    return `
        <!-- Article item -->
        <div class="flex flex-col w-full mt-14 animate-itemShow">
            <div class="w-full flex flex-col lg:flex-row">
                ${
                    item.image !== null
                        ? `<div class="flex flex-col mr-6 mb-4 lg:mb-0 pt-2"><img src="${item.image}" class="max-w-[200px] min-w-[200px] rounded-2xl"></div>`
                        : '<div class="flex flex-col mr-6 mb-4 lg:mb-0 pt-2 min-w-[200px] rounded-2xl items-center justify-center text-gray-500"></div>'
                }
                <div class="flex w-full flex-col">
                    <div class="flex flex-col w-full d-content ${
                        localStorage.getItem('font-size') ? localStorage.getItem('font-size') : 'text-lg'
                    }" ${item.read ? 'style="color: #c4c4c4;"' : ''}>
                            ${item.summary}
                            </div>
                                                
                    <div class="flex flex-col w-full">
                        <div class="flex w-full mt-3">
                            <ul class="flex flex-col w-full d-links">
                                ${item.articles
                                    .map(
                                        (article) => `
                                    <li class="mb-3">
                                        <a href="${article.link}" class="${
                                            item.read ? 'text-gray-500"' : ''
                                        }" target="_blank">${
                                            article.title
                                        }</a><br><span class="text-gray-700 uppercase text-xs mb-2">${
                                            article.feed_title
                                        }</span>
                                    </li>`
                                    )
                                    .join('')}
                            </ul>
                        </div>

                        <div class="flex w-full mt-3 d-pubdate">
                            ${formattedDate} &nbsp&nbsp&nbsp  &nbsp&nbsp&nbsp
                            <button class="flex ai-summarize-daily-btn -mt-0.5 hover:text-white relative" data-id="${
                                item.id
                            }"><span class="absolute group">
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="h-6 w-6">
                                            <path fill-rule="evenodd" d="M2.625 6.75a1.125 1.125 0 1 1 2.25 0 1.125 1.125 0 0 1-2.25 0Zm4.875 0A.75.75 0 0 1 8.25 6h12a.75.75 0 0 1 0 1.5h-12a.75.75 0 0 1-.75-.75ZM2.625 12a1.125 1.125 0 1 1 2.25 0 1.125 1.125 0 0 1-2.25 0ZM7.5 12a.75.75 0 0 1 .75-.75h12a.75.75 0 0 1 0 1.5h-12A.75.75 0 0 1 7.5 12Zm-4.875 5.25a1.125 1.125 0 1 1 2.25 0 1.125 1.125 0 0 1-2.25 0Zm4.875 0a.75.75 0 0 1 .75-.75h12a.75.75 0 0 1 0 1.5h-12a.75.75 0 0 1-.75-.75Z" clip-rule="evenodd" />
                                </svg><span class="invisible group-hover:visible relative -top-14 -left-12 px-2 py-1.5 rounded bg-gray-900 text-white text-nowrap">Article Summary</span></span>
                                
                            </button>
                            <div class="ml-12">
                            ${
                                item.read
                                    ? '<span class="absolute group"><svg class="-mt-0.5 w-6 h-6 text-gray-700" xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true" > <path fill-rule="evenodd" d="M2 12C2 6.477 6.477 2 12 2s10 4.477 10 10-4.477 10-10 10S2 17.523 2 12Zm13.707-1.293a1 1 0 0 0-1.414-1.414L11 12.586l-1.793-1.793a1 1 0 0 0-1.414 1.414l2.5 2.5a1 1 0 0 0 1.414 0l4-4Z" clip-rule="evenodd" /></svg><span class="invisible group-hover:visible relative -top-14 -left-10 px-2 py-1.5 rounded bg-gray-900 text-white normal-case text-nowrap">Already Read</span></span>'
                                    : ''
                            }
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div> 
    `;
}

function noMoreItemsTemplate() {
    return `
        <div class="flex justify-center items-center h-64 mb-[100%] text-gray-500 text-base">
        There are no more unread items.
        </div>
    `;
}

function dailyScrollListener() {
    window.addEventListener('scroll', () => {
        if (window.innerHeight + window.scrollY >= document.body.offsetHeight - document.body.offsetHeight / 2) {
            fetchDailyData(currentUrl);
        }
        markVisibleUnreadSummarizedArticlesAsRead();
    });
}

function markVisibleUnreadSummarizedArticlesAsRead() {
    const dailyItems = document.querySelectorAll('.daily-item');

    dailyItems.forEach((article) => {
        const isRead = article.dataset.read === 'true';
        if (!isRead && isElementInViewport(article)) {
            const articleId = article.dataset.id;
            markSummarizedArticleAsRead(articleId);
            article.dataset.read = 'true';
        }
    });
}

function markSummarizedArticleAsRead(articleId) {
    fetch(`/mark_as_read/daily/${articleId}`, {
        method: 'POST',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
        },
    })
        .then((response) => {
            if (response.ok) {
                checkUnreadCount();
            } else {
                console.error(`Error marking summarized article ${articleId} as read`);
            }
        })
        .catch((error) => {
            console.error(`Error marking summarized article ${articleId} as read`, error);
            showMessage('Error marking article as read', 'error');
        });
}

// Helper function to check if an element is in the viewport
function isElementInViewport(el) {
    const rect = el.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}
