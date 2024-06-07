document.addEventListener('DOMContentLoaded', function () {
    const feedContainer = document.getElementById('feed-container');
    let lastItemId = null;
    const limit = 5;
    let loading = false;

    checkUnreadCount();
    setInterval(checkUnreadCount, 180000);

    document
        .getElementById('feed-container')
        .addEventListener('click', function (event) {
            const btn = event.target.closest('.ai-summarize-btn');
            if (btn) {
                const feedItem = btn.closest('.feed-item');
                const itemTitle = feedItem.querySelector('.item-title');

                const itemPosition =
                    itemTitle.getBoundingClientRect().top + window.pageYOffset;

                const offsetPercentage = 20;
                const offsetPixels =
                    window.innerHeight * (offsetPercentage / 100);
                const offsetPosition = itemPosition - offsetPixels;

                window.scrollTo({
                    top: offsetPosition,
                    behavior: 'smooth',
                });

                const feedContent = feedItem.querySelector('.feed-content');
                const originalContent = feedContent.innerHTML;

                const isCollapsed = feedContent.style.overflow === 'hidden';

                if (isCollapsed) {
                    feedContent.style.maxHeight = 'none';
                    feedContent.style.overflow = 'visible';
                    const gradient =
                        feedContent.querySelector('.bg-gradient-to-t');
                    const button = feedContent.querySelector('button');
                    gradient.classList.add('hidden');
                    button.classList.add('hidden');
                }

                feedContent.innerHTML = `<div class="flex justify-center items-center w-full min-h-96">
            
            <svg width="54" height="54" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <defs>
                    <filter id="spinner-gF01">
                        <feGaussianBlur in="SourceGraphic" stdDeviation="1" result="y"/>
                        <feColorMatrix in="y" mode="matrix" values="1 0 0 0 0 0 1 0 0 0 0 0 1 0 0 0 0 0 18 -7" result="z"/>
                        <feBlend in="SourceGraphic" in2="z"/>
                    </filter>
                </defs>
                <g class="spinner_LvYV" filter="url(#spinner-gF01)">
                    <circle class="spinner_8XMC" cx="5" cy="12" r="4"/>
                    <circle class="spinner_WWWR" cx="19" cy="12" r="4"/>
                </g>
            </svg>
            
            
            </div>`;

                const postUrl = feedItem.querySelector('.item-title a').href;

                fetch('/api/summarize', {
                    method: 'POST',
                    credentials: 'include',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ url: postUrl }),
                })
                    .then((response) => response.json())
                    .then((data) => {
                        if (data.status === 'error') {
                            showMessage('Error summarizing the text', 'error');
                            feedContent.innerHTML =
                                '<div class="error">Error summarizing the text.</div>';
                        } else {
                            feedContent.innerHTML = `
                    <div x-data="{ show: false }" x-init="setTimeout(() => show = true, 100)" x-show="show"
                    x-transition:enter="transition ease-out duration-1000"
                    x-transition:enter-start="transform opacity-0 scale-90"
                    x-transition:enter-end="transform opacity-100 scale-100"
                    >
                    <p>${data.summary}</p>
                </div>`;
                        }
                    })
                    .catch((error) => {
                        showMessage('Error summarizing the text', 'error');
                        console.error('Error:', error);
                        feedContent.innerHTML = originalContent;
                    });
            }
        });

    function getApiPath() {
        const path = window.location.pathname;
        const basePath = '/api/feeditems';
        let apiPath = basePath;

        if (path === '/' || path === '') {
            apiPath += '';
        } else if (path.includes('/category/')) {
            const parts = path.split('/');
            const catId = parts[parts.indexOf('category') + 1];

            if (path.includes('/feed/')) {
                const feedId = parts[parts.indexOf('feed') + 1];
                apiPath += `/${catId}/${feedId}`;
            } else {
                apiPath += `/${catId}`;
            }
        }

        if (path.endsWith('/all')) {
            apiPath += '/all';
        }

        return `${apiPath}?limit=${limit}${lastItemId ? `&last_item_id=${lastItemId}` : ''}`;
    }

    function loadMoreItems() {
        if (loading) return;
        loading = true;

        const apiPath = getApiPath();

        fetch(apiPath)
            .then((response) => response.json())
            .then((data) => {
                if (data.length === 0) {
                    const message = window.location.pathname.includes('/all')
                        ? "There's nothing here."
                        : 'There are no more unread items.';

                    const itemElement = document.createElement('div');
                    itemElement.className = 'empty-message';
                    itemElement.innerHTML = `<div class="w-full text-center ml-auto mr-auto mt-[20%] text-gray-600">${message}<br><img src="/static/imgs/cup.png" width="100px" class="ml-auto mr-auto mt-10"></div>`;
                    feedContainer.appendChild(itemElement);
                    window.removeEventListener('scroll', handleScroll);
                } else {
                    data.forEach((item) => {
                        const itemElement = document.createElement('div');
                        itemElement.className = 'feed-item';
                        itemElement.dataset.id = item.id;
                        itemElement.dataset.read = item.read;
                        let options = {
                            weekday: 'long',
                            year: 'numeric',
                            month: 'long',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit',
                        };
                        let pubDate = new Date(item.pub_date);
                        let formattedDate = pubDate.toLocaleString(
                            'en-GB',
                            options
                        );
                        let creatorContent =
                            item.creator !== null ? item.creator : '';

                        itemElement.innerHTML = `
                        <div class="tb-feed-name">${item.feed_title}</div>
                        <h1 class="item-title"><a class="hover:text-blue-200" target="_blank" rel="noopener" href="${item.link}">${item.title}</a></h1>
                        <div class="flex-col md:flex-row flex">
                            <div class="tb-feed-date">${formattedDate}</div> 
                            <div class="tb-feed-author">${creatorContent}</div>
                        </div>
                        <div x-data="{ expanded: false }" class="feed-content relative" :class="{ 'overflow-hidden': !expanded, 'max-h-none overflow-visible': expanded }">
                        ${item.summary}
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
                        <button class="ai-summarize-btn flex items-center justify-center rounded-lg border border-gray-800 hover:border-gray-700 focus:outline-none px-3 py-2 text-gray-400 transition-all duration-500 overflow-hidden" :class="{'w-32': open, 'w-14': !open}">
                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="h-6 w-6">
                                <path fill-rule="evenodd" d="M2.625 6.75a1.125 1.125 0 1 1 2.25 0 1.125 1.125 0 0 1-2.25 0Zm4.875 0A.75.75 0 0 1 8.25 6h12a.75.75 0 0 1 0 1.5h-12a.75.75 0 0 1-.75-.75ZM2.625 12a1.125 1.125 0 1 1 2.25 0 1.125 1.125 0 0 1-2.25 0ZM7.5 12a.75.75 0 0 1 .75-.75h12a.75.75 0 0 1 0 1.5h-12A.75.75 0 0 1 7.5 12Zm-4.875 5.25a1.125 1.125 0 1 1 2.25 0 1.125 1.125 0 0 1-2.25 0Zm4.875 0a.75.75 0 0 1 .75-.75h12a.75.75 0 0 1 0 1.5h-12a.75.75 0 0 1-.75-.75Z" clip-rule="evenodd" />
                            </svg>
                            <span x-show="open" class=" text-nowrap text-base">AI Summarize</span>
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
            })
            .catch((error) => {
                console.error('Error fetching the feed items:', error);
                loading = false;
            });
    }

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

    function handleScroll() {
        const { scrollTop, scrollHeight, clientHeight } =
            document.documentElement;
        if (scrollTop + clientHeight >= scrollHeight - 300) {
            loadMoreItems();
            markLastUnreadPostAsRead();
        }
        checkPostsVisibility();
    }

    setButtonStyles();
    window.addEventListener('scroll', handleScroll);
    loadMoreItems();

    const btnDefault = document.getElementById('btnDefault');
    const btnAll = document.getElementById('btnAll');

    btnDefault.addEventListener('click', navigateDefault);
    btnAll.addEventListener('click', navigateAll);
});

function setButtonStyles() {
    const currentPath = window.location.pathname;
    const btnDefault = document.getElementById('btnDefault');
    const btnAll = document.getElementById('btnAll');

    if (currentPath.includes('/all')) {
        btnDefault.className = 'not-active-unread';
        btnAll.className = 'active-all';
    } else {
        btnDefault.className = 'active-unread';
        btnAll.className = 'not-active-all';
    }
}

function navigateDefault() {
    const currentPath = window.location.pathname;
    const newPath = modifyPath(currentPath, false);
    if (currentPath !== newPath) {
        fetch('/api/settings', {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                unread: true,
            }),
        }).then(() => {
            localStorage.setItem('lastChoice', 'unread');
            setTimeout(() => {
                window.location.href = newPath;
            }, 100);
        });
    } else {
        setButtonStyles();
    }
}

function navigateAll() {
    const currentPath = window.location.pathname;
    const newPath = modifyPath(currentPath, true);
    if (currentPath !== newPath) {
        fetch('/api/settings', {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                unread: false,
            }),
        }).then(() => {
            localStorage.setItem('lastChoice', 'all');
            setTimeout(() => {
                window.location.href = newPath;
            }, 100);
        });
    } else {
        setButtonStyles();
    }
}

function modifyPath(path, all) {
    const segments = path.split('/').filter((segment) => segment);
    if (all) {
        if (!segments.includes('all')) {
            segments.push('all');
        }
    } else {
        const allIndex = segments.indexOf('all');
        if (allIndex > -1) {
            segments.splice(allIndex, 1);
        }
    }
    return '/' + segments.join('/');
}

function checkUnreadCount() {
    fetch('/api/unread-count')
        .then((response) => response.json())
        .then((data) => {
            updateBadge(data.unread_count);
        })
        .catch((error) =>
            console.error(
                'Error when getting the number of unread messages: ',
                error
            )
        );
}

function updateBadge(count) {
    if ('setAppBadge' in navigator) {
        if (count > 0) {
            navigator.setAppBadge(count).catch((error) => {
                console.error('Error when installing badge: ', error);
            });
        } else {
            navigator.clearAppBadge().catch((error) => {
                console.error('Error when clearing badge: ', error);
            });
        }
    }
}

const readPosts = new Set();

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
                    console.error(
                        'Error marking post as read:',
                        response.statusText
                    );
                }
            })
            .catch((error) => {
                console.error('Error marking post as read:', error);
            });
    }
}

function markLastUnreadPostAsRead() {
    const feedItems = document.querySelectorAll('.feed-item');
    let lastUnreadItem = null;

    feedItems.forEach((item) => {
        const isRead = item.dataset.read === 'true';
        if (!isRead) {
            lastUnreadItem = item;
        }
    });

    if (lastUnreadItem) {
        const postId = lastUnreadItem.dataset.id;
        markAsRead(postId);
        lastUnreadItem.dataset.read = 'true';
    }
}

function checkPostsVisibility() {
    const feedItems = document.querySelectorAll('.feed-item');
    const windowHeight = window.innerHeight;

    feedItems.forEach((item) => {
        const rect = item.getBoundingClientRect();
        const postId = item.dataset.id;
        const isRead = item.dataset.read === 'true';

        if (rect.bottom <= windowHeight / 2 && !isRead) {
            markAsRead(postId);
        }
    });
}

document.addEventListener('alpine:init', () => {
    document.getElementById('modal-add').classList.remove('hidden');
    document.getElementById('modal-add').classList.add('flex');
});

let startY;
let isPulling = false;

window.addEventListener('touchstart', function (event) {
    if (window.scrollY === 0) {
        startY = event.touches[0].pageY;
        isPulling = true;
    }
});

window.addEventListener('touchmove', function (event) {
    if (isPulling) {
        let distance = event.touches[0].pageY - startY;
        if (distance > 100) {
            event.preventDefault();
        }
    }
});

window.addEventListener('touchend', function () {
    if (isPulling) {
        let distance = event.changedTouches[0].pageY - startY;
        if (distance > 100) {
            location.reload();
        }
        isPulling = false;
    }
});
