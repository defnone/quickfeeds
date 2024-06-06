let pauseUpdate = false;

function toggleUpdates() {
    pauseUpdate = !pauseUpdate;
    if (!pauseUpdate) {
        updateData();
    }
}

function pauseUpdates() {
    pauseUpdate = true;
}

function resumeUpdates() {
    pauseUpdate = false;
    updateData();
}

async function fetchCategoriesAndBlogs() {
    try {
        const response = await fetch('/api/categories_and_blogs');
        const data = await response.json();
        const container = document.getElementById('categories_and_blogs');
        container.innerHTML = '';

        data.categories_and_blogs.forEach((category) => {
            if (category.feeds.length > 0) {
                let categoryHTML = `<p class="text-base mt-6 mb-1 font-medium text-gray-200"><a href="/category/${category.id}">${category.name}</a></p>`;
                category.feeds.forEach((feedData) => {
                    let feedHTML = `<div x-data="{ open: false, editMode: false, title: '${
                        feedData.feed.title
                    }', menuOpen: false }" class="">
                                <div class="flex w-full" @mouseover="open = true" @mouseout="open = false">
                                    <div class="flex flex-row w-full">
                                        <div :class="{ 'active-feed': window.location.pathname.includes('/category/${
                                            category.id
                                        }/feed/${
                        feedData.feed.id
                    }'), 'block text-sm mt-1 mb-1 pt-1 pr-2 text-gray-400 flex-grow': !window.location.pathname.includes('/category/${
                        category.id
                    }/feed/${feedData.feed.id}') }">
                                            <a x-show="!editMode" class="hover:text-white" href="/category/${
                                                category.id
                                            }/feed/${feedData.feed.id}">${
                        feedData.feed.title.length > 28
                            ? feedData.feed.title.substring(0, 25) + '...'
                            : feedData.feed.title
                    }</a>
                                            <input x-show="editMode" x-model="title" x-ref="input" @keydown.enter="editMode = false; updateFeed('${
                                                feedData.feed.id
                                            }', title).then(() => resumeUpdates());" @keydown.escape="editMode = false; resumeUpdates()" @blur="editMode = false; resumeUpdates()" class="bg-gray-800 text-white px-2 py-1 flex -m-0.5 w-full rounded" x-init="$watch('editMode', value => { if (value) setTimeout(() => $refs.input.focus(), 50) })" />

                                        </div>
                                        <div class="relative inline-block text-left" x-show="open && !editMode">
                                            <button @click="menuOpen = !menuOpen; $event.stopPropagation(); pauseUpdates();" class="inline-flex -ml-5 justify-center w-full rounded-md shadow-sm text-md font-bold hover:text-gray-200 text-white focus:outline-none">
                                                <span class="mt-1">...</span>
                                            </button>
                                        </div>
                                        ${
                                            feedData.unread_count > 0
                                                ? `<div class="flex pt-1 pb-1 px-2 mt-2 max-h-8 items-center justify-center text-xs font-bold rounded-md bg-gray-900 ml-auto">${feedData.unread_count}</div>`
                                                : ''
                                        }
                                    </div>
                                </div>
                                <div x-show="menuOpen" @click.away="menuOpen = false; resumeUpdates()"
                                x-transition:enter="transition ease-out duration-300"
                                x-transition:enter-start="opacity-0 transform scale-95"
                                x-transition:enter-end="opacity-100 transform scale-100"
                                x-transition:leave="transition ease-in duration-300"
                                x-transition:leave-start="opacity-100 transform scale-100"
                                x-transition:leave-end="opacity-0 transform scale-95"
                                class="w-full bg-slate-800 border border-gray-800 text-white py-2 px-4 mt-1 rounded-md shadow-lg flex justify-between">
                                    <div class="flex-col w-full">
                                        <div class="flex w-full">
                                            <a @click="editMode = true; menuOpen = false; pauseUpdates()" class="block px-6 py-2 text-sm text-gray-300 rounded-lg bg-stone-800 hover:bg-gray-900 hover:text-white cursor-pointer">Rename</a>
                                            <a @click="deleteFeed('${
                                                feedData.feed.id
                                            }')" class="block ml-auto px-8 py-2 text-sm text-red-700 rounded-lg bg-stone-800 hover:bg-gray-900 hover:text-red-600 cursor-pointer">Delete</a>
                                        </div>
                                        <div class="w-full flex-grow mt-2 mb-1">
                                            <select id="ns-select" @change="updateFeedCategory('${
                                                feedData.feed.id
                                            }', $event.target.value)" class="block w-full px-6 py-2 text-sm text-gray-300 rounded-lg bg-stone-800 hover:bg-gray-900 hover:text-white cursor-pointer">
                                                <option value="" disabled selected>Change category</option>
                                                ${data.categories_and_blogs
                                                    .map(
                                                        (category) =>
                                                            `<option value="${category.id}">${category.name}</option>`
                                                    )
                                                    .join('')}
                                            </select>
                                        </div>
                                    </div>
                                </div>
                            </div>`;
                    categoryHTML += feedHTML;
                });
                container.innerHTML += categoryHTML;
            }
        });
    } catch (error) {
        console.error('Ошибка при получении категорий и блогов:', error);
    }
}

document.addEventListener('click', function (event) {
    const isClickInsideMenu = event.target.closest('.menu');
    if (!isClickInsideMenu) {
        closeAllMenus();
    }
});

function closeAllMenus() {
    document.querySelectorAll('[x-data]').forEach((el) => {
        el.__x.$data.menuOpen = false;
    });
    resumeUpdates();
}

async function fetchLastSync() {
    try {
        const response = await fetch('/api/last_sync');
        const data = await response.json();

        document.getElementById('last_sync').innerText = data.last_sync;
    } catch (error) {
        console.error(
            'Ошибка при получении времени последней синхронизации:',
            error
        );
    }
}

function showMessage(message, type) {
    const messageContainer = document.createElement('div');
    messageContainer.innerHTML = `
            <div @click="open = false" x-data="{ open: false }" x-init="setTimeout(() => open = true, 100)" x-show="open" 
                x-transition:enter="transition ease-out duration-300 transform"
                x-transition:enter-start="opacity-0 translate-x-full"
                x-transition:enter-end="opacity-100 translate-x-0"
                x-transition:leave="transition ease-in duration-300 transform"
                x-transition:leave-start="opacity-100 translate-x-0"
                x-transition:leave-end="opacity-0 translate-x-full"
                class="fixed inset-0 flex items-end z-50 justify-start px-4 py-6 pointer-events-none sm:p-6 sm:items-start sm:justify-end">
                <div :class="{'shadow-md bg-red-800 border-2 border-red-900': '${type}' == 'error', ' bg-green-800 border border-green-900': '${type}' == 'success'}"
                    class="max-w-sm w-full shadow-lg rounded-lg pointer-events-auto">
                    <div class="rounded-lg shadow-xs overflow-hidden">
                        <div class="p-4">
                            <div class="flex items-start">
                                <div class="ml-3 w-0 flex-1 pt-0.5">
                                    <p class="text-base leading-5 font-medium text-white">
                                        ${message}
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    document.body.appendChild(messageContainer);
}

async function updateFeed(feedId, title) {
    try {
        const response = await fetch(`/api/feeds/${feedId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ title: title }),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Error updating feed');
        }

        // Обновляем только название фида на странице без перезагрузки
        document.querySelector(`a[href$="/feed/${feedId}"]`).textContent =
            title;

        // Показываем сообщение об успешном обновлении
        showMessage('Feed has been successfully renamed', 'success');
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

async function updateFeedCategory(feedId, categoryId) {
    try {
        pauseUpdates(); // Остановить обновление данных

        const response = await fetch(`/api/feeds/${feedId}/category`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ category_id: categoryId }),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Error updating feed category');
        }

        // Обновляем данные после изменения категории фида
        await fetchCategoriesAndBlogs();

        // Показываем сообщение об успешном изменении категории
        showMessage('Feed category updated successfully', 'success');
    } catch (error) {
        showMessage(error.message, 'error');
    } finally {
        resumeUpdates(); // Возобновить обновление данных после завершения операции
    }
}

async function deleteFeed(feedId) {
    try {
        const response = await fetch(`/api/feeds/${feedId}`, {
            method: 'DELETE',
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Error when deleting feed');
        }

        // Обновляем данные после удаления фида
        await fetchCategoriesAndBlogs();

        // Показываем сообщение об успешном удалении
        showMessage('Feed deleted successfully', 'success');
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

window.addEventListener('focus', resumeUpdates);
window.addEventListener('blur', pauseUpdates);

async function updateData() {
    if (!document.hidden && !pauseUpdate) {
        await fetchCategoriesAndBlogs();
        await fetchLastSync();
    }
}

document.addEventListener('visibilitychange', updateData);
document.addEventListener('visibilitychange', updateData);

// Обновляем данные каждые 5 секунд, если окно активно
setInterval(updateData, 5000);

// Инициализируем первоначальное получение данных
updateData();
