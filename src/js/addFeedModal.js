export function initAddfeedModal() {
    document.getElementById('create-category-link').addEventListener('click', function (event) {
        event.preventDefault();
        document.getElementById('create-category-link').style.display = 'none';
        document.getElementById('category-select').style.display = 'none';
        document.getElementById('new-category-input').style.display = 'block';
        document.getElementById('choose-category-link').style.display = 'flex';
    });

    document.getElementById('choose-category-link').addEventListener('click', function (event) {
        event.preventDefault();
        document.getElementById('create-category-link').style.display = 'flex';
        document.getElementById('category-select').style.display = 'block';
        document.getElementById('new-category-input').style.display = 'none';
        document.getElementById('choose-category-link').style.display = 'none';
    });

    document.getElementById('submit-button').addEventListener('click', async function (event) {
        event.preventDefault();

        document.getElementById('loading-spinner').style.display = 'block';
        document.querySelector('.add-feed-text').style.display = 'none';

        const newCategoryInput = document.getElementById('new-category-input');
        const categorySelect = document.getElementById('category-select');
        const categoryField = document.getElementById('category');

        if (newCategoryInput.style.display === 'block' && newCategoryInput.value.trim() !== '') {
            categoryField.value = newCategoryInput.value.trim();
        } else {
            categoryField.value = categorySelect.options[categorySelect.selectedIndex].text;
        }

        const form = document.getElementById('add_feed');
        const formData = new FormData(form);

        try {
            const response = await fetch('/add_feed', {
                method: 'POST',
                body: formData,
            });
            const data = await response.json();

            document.getElementById('loading-spinner').style.display = 'none';
            document.querySelector('.add-feed-text').style.display = 'block';

            if (data.success) {
                window.location.href = '/';
            } else {
                document.getElementById('error').innerText = data.error;
            }
        } catch (error) {
            document.getElementById('loading-spinner').style.display = 'none';
            document.querySelector('.add-feed-text').style.display = 'block';
            document.getElementById('error').innerText = 'An error occurred while submitting the form.';
            console.error('Error:', error);
        }
    });

    document.addEventListener('DOMContentLoaded', async () => {
        const addFeedButton = document.getElementById('modal-add');
        addFeedButton.classList.remove('hidden');
        addFeedButton.classList.add('flex');
        const categorySelect = document.getElementById('category-select');

        try {
            const response = await fetch('/api/categories_and_blogs');
            const data = await response.json();

            data.categories_and_blogs.forEach((category) => {
                const option = document.createElement('option');
                option.value = category.id;
                option.text = category.name;
                categorySelect.appendChild(option);
            });
        } catch (error) {
            console.error('Error getting categories:', error);
        }
    });
}
