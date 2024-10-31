import { showMessage } from './utils/messages';
import { fetchCategoriesAndBlogs } from './feedList';

export async function fetchAndRenderCategories() {
    try {
        const response = await fetch('/api/categories_and_blogs');
        const data = await response.json();
        const container = document.getElementById('cat-list');
        container.innerHTML = '';
        data.categories_and_blogs.forEach((category) => {
            let deleteButtonHTML = '';
            if (category.name !== 'Unnamed') {
                deleteButtonHTML = `
                <button id="delete-${category.id}" class="text-sm px-3 text-red-700 hover:text-red-800 focus:outline-none ml-auto">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="size-6">
                        <path fill-rule="evenodd" d="M16.5 4.478v.227a48.816 48.816 0 0 1 3.878.512.75.75 0 1 1-.256 1.478l-.209-.035-1.005 13.07a3 3 0 0 1-2.991 2.77H8.084a3 3 0 0 1-2.991-2.77L4.087 6.66l-.209.035a.75.75 0 0 1-.256-1.478A48.567 48.567 0 0 1 7.5 4.705v-.227c0-1.564 1.213-2.9 2.816-2.951a52.662 52.662 0 0 1 3.369 0c1.603.051 2.815 1.387 2.815 2.951Zm-6.136-1.452a51.196 51.196 0 0 1 3.273 0C14.39 3.05 15 3.684 15 4.478v.113a49.488 49.488 0 0 0-6 0v-.113c0-.794.609-1.428 1.364-1.452Zm-.355 5.945a.75.75 0 1 0-1.5.058l.347 9a.75.75 0 1 0 1.499-.058l-.346-9Zm5.48.058a.75.75 0 1 0-1.498-.058l-.347 9a.75.75 0 0 0 1.5.058l.345-9Z" clip-rule="evenodd" />
                    </svg>
                </button>`;
            }

            let categoryHTML = `
                <div x-data="{ editMode: false, newName: '${category.name}', timeout: null }" class="flex w-full border-b border-gray-900 ">
                    <span x-show="!editMode" class="block text-base w-full mt-4 mb-2 pb-2 pt-2 px-3 font-medium text-gray-200 cursor-pointer" @click="if('${category.name}' !== 'Unnamed') { editMode = true; requestAnimationFrame(() => { $refs.input.focus(); }); }">${category.name}</span>

                    <input x-show="editMode" x-model="newName" x-ref="input" @keydown.enter="saveCategory(${category.id}, newName); editMode = false" type="text" class="text-base flex w-full mt-4 mb-2 pb-2 pt-2 px-3 mr-1 font-medium text-gray-200 bg-slate-900 rounded-lg border-0 focus:outline-none" @blur="timeout = setTimeout(() => editMode = false, 100)" x-init="$watch('editMode', value => { if (value) setTimeout(() => $refs.input.focus(), 50) })" />

                    <button x-show="editMode" @click="clearTimeout(timeout); saveCategory(${category.id}, newName); editMode = false" class="ml-2 mr-2 mt-4 mb-2 px-3 py-1 h-10 font-semibold text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-md focus:outline-none">Save</button>
                    ${deleteButtonHTML}
                </div>`;
            container.innerHTML += categoryHTML;
        });

        // Add event listeners to delete buttons
        data.categories_and_blogs.forEach((category) => {
            if (category.name !== 'Unnamed') {
                document.getElementById(`delete-${category.id}`).addEventListener('click', async () => {
                    try {
                        const response = await fetch(`/api/settings/categories/delete/${category.id}`, {
                            method: 'DELETE',
                        });
                        if (response.ok) {
                            fetchAndRenderCategories();
                            fetchCategoriesAndBlogs(true);
                            showMessage('Category deleted successfully', 'success');
                        } else {
                            console.error('Error deleting category:', await response.text());
                        }
                    } catch (error) {
                        console.error('Error deleting category:', error);
                    }
                });
            }
        });
    } catch (error) {
        showMessage('Error fetching categories and blogs', 'error');
        console.error('Error fetching categories and blogs:', error);
    }
}

async function addCategory() {
    const categoryNameInput = document.getElementById('new-category');
    const categoryName = categoryNameInput.value;

    if (!categoryName) {
        showMessage('Category name is required', 'error');
        return;
    }

    const response = await fetch('/api/settings/categories/add', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name: categoryName }),
    });

    const data = await response.json();

    if (!response.ok) {
        showMessage('Error: ' + data.error, 'error');
        return;
    }

    categoryNameInput.value = '';
    showMessage('Category added successfully', 'success');
    fetchAndRenderCategories();
    fetchCategoriesAndBlogs(true);
}

window.saveCategory = async (categoryId, newName) => {
    const response = await fetch(`/api/settings/categories/rename/${categoryId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ new_name: newName }),
    });

    const data = await response.json();

    if (!response.ok) {
        showMessage('Error: ' + data.error, 'error');
        return;
    }

    showMessage('Category renamed successfully', 'success');
    fetchAndRenderCategories();
    fetchCategoriesAndBlogs(true);
};

export function initCategoryListeners() {
    document.getElementById('add-new-category').addEventListener('click', addCategory);

    document.getElementById('new-category').addEventListener('keydown', async (event) => {
        if (event.key === 'Enter') {
            addCategory();
        }
    });
}
