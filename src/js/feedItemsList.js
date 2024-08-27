import { getApiPath } from './utils/getApiPath';
import { fetchCategoriesAndBlogs } from './feedList';
import { checkUnreadCount } from './unreadCount';

let loading = false;
let lastItemId = null;
let EOF = false;
const readPosts = new Set();

export function reloadFeedList() {
    loading = false;
    lastItemId = null;
    EOF = false;
    readPosts.clear();
    document.getElementById('feed-container').innerHTML = '';
    loadMoreItems();
}

export function feedListEventListeners() {
    window.addEventListener('scroll', handleScroll);
}

// Function to load items from the API and append them to the feed container
export function loadMoreItems() {
    const feedContainer = document.getElementById('feed-container');
    if (loading) return;
    if (EOF) return;
    loading = true;
    const apiPath = getApiPath(lastItemId);

    fetch(apiPath)
        .then((response) => response.json())
        .then((data) => {
            if (data.length > 0) {
                data.forEach((item) => {
                    const itemElement = document.createElement('div');
                    itemElement.classList.add('feed-item', 'animate-itemShow');
                    itemElement.dataset.read = item.read;
                    itemElement.dataset.id = item.id;

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
                    let creatorContent = item.creator !== null ? item.creator : '';

                    itemElement.innerHTML = `
                            <div class="tb-feed-name">${item.feed_title}</div>
                            <h1 class="item-title"><a class="hover:text-blue-200" target="_blank" rel="noopener noreferrer" href="${
                                item.link
                            }">${item.title}</a></h1>
                            <div class="flex-col md:flex-row flex">
                                <div class="tb-feed-date">${formattedDate}</div> 
                                <div class="tb-feed-author">${creatorContent}</div>
                            </div>
                            <div id="exp-hidden" x-data="{ expanded: false }" class="feed-content relative ${
                                localStorage.getItem('font-size') ? localStorage.getItem('font-size') : 'text-lg'
                            }" :class="{ 'overflow-hidden': !expanded, 'max-h-none overflow-visible': expanded }">
                                ${item.summary}c
                                <div class="absolute bottom-0 left-0 w-full h-60 bg-gradient-to-t from-slate-800 via-slate-800/90 to-slate-800/0 pointer-events-none" x-show="!expanded"></div>
                                <button class="absolute bottom-0 left-0 w-full text-center py-2 font-bold text-white transition-colors focus:outline-none" x-show="!expanded" @click="expanded = true">
                                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="size-11 w-15 h-15 ml-auto mr-auto shadow-2xl shadow-stone-950 bg-black transition duration-50 hover:bg-stone-700 mb-4 p-3 rounded-full gradient-arrow">
                                        <path fill-rule="evenodd" d="M11.47 13.28a.75.75 0 0 0 1.06 0l7.5-7.5a.75.75 0 0 0-1.06-1.06L12 11.69 5.03 4.72a.75.75 0 0 0-1.06 1.06l7.5 7.5Z" clip-rule="evenodd" />
                                        <path fill-rule="evenodd" d="M11.47 19.28a.75.75 0 0 0 1.06 0l7.5-7.5a.75.75 0 1 0-1.06-1.06L12 17.69l-6.97-6.97a.75.75 0 0 0-1.06 1.06l7.5 7.5Z" clip-rule="evenodd" />
                                    </svg>
                                </button>
                            </div>

                            <!-- AI Summarize -->
                            <div class="flex  ml-6 xl:ml-16 mr-6 mt-4 justify-start max-w-3xl">
                                <div x-data="{ open: false }" @mouseover="open = true" @mouseout="open = false" class="relative">
                                    <button class="ai-summarize-btn flex items-center justify-center rounded-lg border border-gray-800 hover:border-gray-700 focus:outline-none px-3 py-2 text-gray-400 transition-all duration-700 overflow-hidden" :class="{'w-32': open, 'w-14': !open}">
                                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="h-6 w-6">
                                            <path fill-rule="evenodd" d="M2.625 6.75a1.125 1.125 0 1 1 2.25 0 1.125 1.125 0 0 1-2.25 0Zm4.875 0A.75.75 0 0 1 8.25 6h12a.75.75 0 0 1 0 1.5h-12a.75.75 0 0 1-.75-.75ZM2.625 12a1.125 1.125 0 1 1 2.25 0 1.125 1.125 0 0 1-2.25 0ZM7.5 12a.75.75 0 0 1 .75-.75h12a.75.75 0 0 1 0 1.5h-12A.75.75 0 0 1 7.5 12Zm-4.875 5.25a1.125 1.125 0 1 1 2.25 0 1.125 1.125 0 0 1-2.25 0Zm4.875 0a.75.75 0 0 1 .75-.75h12a.75.75 0 0 1 0 1.5h-12a.75.75 0 0 1-.75-.75Z" clip-rule="evenodd" />
                                        </svg>
                                        <span id="ai-summarize-btn-text" x-show="open" class="flex text-nowrap text-base">AI Summarize</span>
                                    </button>
                                </div>
                            </div>
                        `;
                    feedContainer.appendChild(itemElement);
                    handleOverflow(itemElement);
                });

                lastItemId = data[data.length - 1].id;
                loading = false;
            }
            if (data.length === 1 || data.length === 2) {
                emptyMessage(feedContainer);
                loading = false;
            } else if (data.length === 0) {
                emptyMessage(feedContainer);
                loading = false;
                EOF = true;
            }
        })
        .catch((error) => {
            console.error('Error fetching the feed items:', error);
            loading = false;
        });
}

// Function to display an empty message
function emptyMessage(feedContainer) {
    if (document.getElementById('empty')) {
        return;
    }
    const message = window.location.pathname.includes('/all')
        ? "There's nothing here."
        : 'There are no more unread items.';

    const itemElement = document.createElement('div');
    itemElement.id = 'empty';
    itemElement.className = 'empty-message';
    itemElement.innerHTML = `
                <div class="w-full text-center ml-auto mb-[50%] mr-auto mt-[20%] text-gray-600">
                  ${message}<br><img src="/static/imgs/cup.png" width="100px" class="ml-auto mr-auto mt-10">
                </div>`;
    feedContainer.appendChild(itemElement);
}

// Function to handle overflow of feed content
function handleOverflow(item) {
    const content = item.querySelector('.feed-content');
    const windowHeight = window.innerHeight;
    const itemHeight = item.offsetHeight;

    if (itemHeight > windowHeight * 0.8) {
        content.style.maxHeight = `${windowHeight * 0.8}px`;
        content.style.overflow = 'hidden';

        const gradient = content.querySelector('.bg-gradient-to-t');
        const button = content.querySelector('button');

        gradient.classList.remove('hidden');
        button.classList.remove('hidden');

        button.addEventListener('click', () => {
            content.style.maxHeight = 'none';
            content.style.overflow = 'visible';
            gradient.classList.add('hidden');
            button.classList.add('hidden');

            checkPostsVisibility();
        });
    } else {
        const gradient = content.querySelector('.bg-gradient-to-t');
        const button = content.querySelector('button');

        if (gradient) {
            gradient.classList.add('hidden');
        }
        if (button) {
            button.classList.add('hidden');
        }
    }
}

// Function to check the visibility of posts and mark them as read if they are visible
function checkPostsVisibility() {
    const feedItems = document.querySelectorAll('.feed-item');
    const windowHeight = window.innerHeight;

    feedItems.forEach((item) => {
        if (item.dataset.read === 'true') {
            return;
        }

        const rect = item.getBoundingClientRect();
        const postId = item.dataset.id;
        const isRead = item.dataset.read === 'true';

        if (rect.bottom <= windowHeight * 0.7 && !isRead) {
            markAsRead(postId);
            item.dataset.read = 'true';
        }
    });
}

// Function to mark a post as read
function markAsRead(postId) {
    if (!readPosts.has(postId)) {
        fetch(`/mark_as_read/${postId}`, {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
            },
        })
            .then((response) => {
                if (response.ok) {
                    readPosts.add(postId);
                    checkUnreadCount();
                    fetchCategoriesAndBlogs();
                } else {
                    console.error('Error marking post as read:', response.statusText);
                }
            })
            .catch((error) => {
                console.error('Error marking post as read:', error);
            });
    }
}

function handleScroll() {
    const { scrollTop, scrollHeight, clientHeight } = document.documentElement;
    if (scrollTop + clientHeight >= scrollHeight * 0.7) {
        loadMoreItems();
    }
    checkPostsVisibility();
}
