document.addEventListener('DOMContentLoaded', function () {
    const feedContainer = document.getElementById('feed-container');
    let lastItemId = null;
    const limit = 5;
    let loading = false;

    // Event listener for AI Summarize button click
    document
        .getElementById('feed-container')
        .addEventListener('click', function (event) {
            const btn = event.target.closest('.ai-summarize-btn');
            if (btn) {
                const feedItem = btn.closest('.feed-item');
                const itemTitle = feedItem.querySelector('.item-title');

                // Scroll to the item position with an offset
                const itemPosition =
                    itemTitle.getBoundingClientRect().top + window.scrollY;
                const offsetPercentage = 20;
                const offsetPixels =
                    window.innerHeight * (offsetPercentage / 100);
                const offsetPosition = itemPosition - offsetPixels;

                window.scrollTo({
                    top: offsetPosition,
                    behavior: 'smooth',
                });

                // Calculate the scroll duration (assuming a fixed scroll speed)
                const scrollDuration = 500; // duration in milliseconds

                setTimeout(() => {
                    const feedContent = feedItem.querySelector('.feed-content');
                    const originalContent = feedContent.innerHTML;
                    const isCollapsed = feedContent.style.overflow === 'hidden';

                    // Toggle content visibility
                    if (isCollapsed) {
                        feedContent.style.maxHeight = 'none';
                        feedContent.style.overflow = 'visible';
                        const gradient =
                            feedContent.querySelector('.bg-gradient-to-t');
                        const button = feedContent.querySelector('button');
                        gradient.classList.add('hidden');
                        button.classList.add('hidden');
                    }

                    // Show loading placeholder while fetching the summary
                    feedContent.innerHTML = `
                <div class="space-y-4">
                    <div class="line"></div>
                    <div class="line short"></div>
                    <div class="line"></div>
                    <div class="line"></div>
                    <div class="line short"></div>
                    <div class="line"></div>
                    <div class="line"></div>
                    <div class="line short"></div>
                    <div class="line"></div>
                    <div class="line"></div>
                    <div class="line short"></div>
                    <div class="line"></div>
                </div>`;

                    const postUrl =
                        feedItem.querySelector('.item-title a').href;

                    // Fetch the summary from the API
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
                                showMessage(
                                    'Error summarizing the text. Check Groq API in <a class="underline" href="/settings">Settings</a>.',
                                    'error'
                                );
                                feedContent.innerHTML = originalContent;
                            } else {
                                feedContent.innerHTML = `
                            <div x-data="{ show: false }" x-init="setTimeout(() => show = true, 0)" x-show="show"
                            x-transition:enter="transition ease-out duration-[2000ms]"
                            x-transition:enter-start="transform max-h-0 opacity-0"
                            x-transition:enter-end="transform max-h-full opacity-100">
                                <div id="summary-text">${data.summary}</div>

                                        <button class="copy-btn flex ml-auto">
                                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="size-6">
                                        <path fill-rule="evenodd" d="M7.502 6h7.128A3.375 3.375 0 0 1 18 9.375v9.375a3 3 0 0 0 3-3V6.108c0-1.505-1.125-2.811-2.664-2.94a48.972 48.972 0 0 0-.673-.05A3 3 0 0 0 15 1.5h-1.5a3 3 0 0 0-2.663 1.618c-.225.015-.45.032-.673.05C8.662 3.295 7.554 4.542 7.502 6ZM13.5 3A1.5 1.5 0 0 0 12 4.5h4.5A1.5 1.5 0 0 0 15 3h-1.5Z" clip-rule="evenodd" />
                                        <path fill-rule="evenodd" d="M3 9.375C3 8.339 3.84 7.5 4.875 7.5h9.75c1.036 0 1.875.84 1.875 1.875v11.25c0 1.035-.84 1.875-1.875 1.875h-9.75A1.875 1.875 0 0 1 3 20.625V9.375ZM6 12a.75.75 0 0 1 .75-.75h.008a.75.75 0 0 1 .75.75v.008a.75.75 0 0 1-.75.75H6.75a.75.75 0 0 1-.75-.75V12Zm2.25 0a.75.75 0 0 1 .75-.75h3.75a.75.75 0 0 1 0 1.5H9a.75.75 0 0 1-.75-.75ZM6 15a.75.75 0 0 1 .75-.75h.008a.75.75 0 0 1 .75.75v.008a.75.75 0 0 1-.75.75H6.75a.75.75 0 0 1-.75-.75V15Zm2.25 0a.75.75 0 0 1 .75-.75h3.75a.75.75 0 0 1 0 1.5H9a.75.75 0 0 1-.75-.75ZM6 18a.75.75 0 0 1 .75-.75h.008a.75.75 0 0 1 .75.75v.008a.75.75 0 0 1-.75.75H6.75a.75.75 0 0 1-.75-.75V18Zm2.25 0a.75.75 0 0 1 .75-.75h3.75a.75.75 0 0 1 0 1.5H9a.75.75 0 0 1-.75-.75Z" clip-rule="evenodd" />
                                        </svg></button>

                            </div>`;
                            }
                        })
                        .catch((error) => {
                            showMessage('Error summarizing the text', 'error');
                            console.error('Error:', error);
                            feedContent.innerHTML = originalContent;
                        });
                }, scrollDuration); // delay in milliseconds
            }
        });

    // Function to convert HTML to Markdown
    function htmlToMarkdown(html) {
        // Convert list items
        html = html.replace(/<li>(.*?)<\/li>/g, '- $1\n');
        // Convert unordered lists
        html = html.replace(/<\/ul>/g, '\n').replace(/<ul>/g, '');
        // Convert paragraphs
        html = html.replace(/<p>(.*?)<\/p>/g, '$1\n\n');
        // Remove other tags
        html = html.replace(/<[^>]+>/g, '');
        return html;
    }

    // Event listener for copy button click
    document
        .getElementById('feed-container')
        .addEventListener('click', function (event) {
            const copyBtn = event.target.closest('.copy-btn');
            if (copyBtn) {
                const summaryElement = copyBtn.previousElementSibling;
                const summaryText = htmlToMarkdown(summaryElement.innerHTML);
                navigator.clipboard
                    .writeText(summaryText)
                    .then(() => {
                        showMessage(
                            'The text has been copied to the clipboard.',
                            'success'
                        );
                    })
                    .catch((error) => {
                        console.error('Error copying text: ', error);
                    });
            }
        });

    // Function to construct the API path based on current URL
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

    // Function to load more items from the API
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
                            <h1 class="item-title"><a class="hover:text-blue-200" target="_blank" rel="noopener noreferrer" href="${item.link}">${item.title}</a></h1>
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

    // Function to handle scroll event for loading more items
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

// Function to set styles for buttons based on the current path
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

// Function to navigate to default feed
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

// Function to navigate to all feed
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

// Function to modify the URL path based on the selection (all/unread)
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

// Runs the worker to check the unread count in the background
if (window.Worker) {
    const worker = new Worker('/static/js/worker.js');

    worker.addEventListener(
        'message',
        function (e) {
            const unreadCount = e.data;
            updateBadge(unreadCount);
        },
        false
    );

    worker.postMessage('start');
}

// Function to check the count of unread messages
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

// Function to update the badge with the unread count
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

// Function to mark the last unread post as read
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

// Function to check the visibility of posts and mark them as read if they are visible
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

// Initialize Alpine.js when document is ready
document.addEventListener('alpine:init', () => {
    document.getElementById('modal-add').classList.remove('hidden');
    document.getElementById('modal-add').classList.add('flex');
});

let startY;
let isPulling = false;

// Touch events for pull-to-refresh functionality
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
