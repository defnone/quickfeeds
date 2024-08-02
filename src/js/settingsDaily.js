import { showMessage } from './utils/messages';

const active = document.getElementById('active');
const compareTitles = document.getElementById('title-compare');
const otherSettings = document.getElementById('other-settings');
const translate = document.getElementById('translate');
const processRead = document.getElementById('process-read');
const hoursSummary = document.getElementById('hours-summary');
const syncAtHours = document.getElementById('sync-at-hours');
const syncAtMinutes = document.getElementById('sync-at-minutes');

const save = document.getElementById('save-settings');

function convertTime(data) {
    const timeParts = data.split(' ')[0].split(':');
    const localHours = timeParts[0];
    const localMinutes = timeParts[1];

    syncAtHours.value = localHours;
    syncAtMinutes.value = localMinutes;
}

function feedList(data) {
    const feedList = document.getElementById('feed-list');
    feedList.innerHTML = '';

    data.feeds.forEach((feed) => {
        const option = document.createElement('div');
        const feedId = 'feed-' + feed.id;
        const maxLength = 22;
        const title = feed.title.length > maxLength ? feed.title.substring(0, maxLength) + '...' : feed.title;
        option.innerHTML = `
        <label class="flex min-w-60 mr-6 p-4 border rounded-lg font-bold mb-4 ${
            feed.daily_enabled ? 'border-green-800 text-white bg-green-800' : ' text-gray-500 border-gray-700'
        }">
        <input type="checkbox" class="mr-2 hidden" id="${feedId}" name="myCheckbox" ${feed.active ? 'checked' : ''} />
        ${title} 
        </label>
        `;
        const checkbox = option.querySelector(`#${feedId}`);
        checkbox.addEventListener('change', (event) => {
            const parentLabel = checkbox.parentElement;
            if (event.target.checked) {
                parentLabel.classList.add('border-green-800', 'text-white', 'bg-green-800');
                fetch('/api/settings/daily/feed', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({ id: feed.id, dailyEnabled: true }),
                }).catch(console.error());
            } else {
                parentLabel.classList.remove('border-green-800', 'text-white', 'bg-green-800');
                parentLabel.classList.add('text-gray-500', 'border-gray-700');
                fetch('/api/settings/daily/feed', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({ id: feed.id, dailyEnabled: false }),
                }).catch(console.error());
            }
        });

        feedList.appendChild(option);
    });
}

function getDailySettings() {
    fetch('/api/settings/daily', {
        method: 'GET',
        credentials: 'include',
    })
        .then((response) => response.json())
        .then((data) => {
            hoursSummary.value = data.hours_summary;
            processRead.checked = data.process_read;
            processRead.dispatchEvent(new Event('change'));
            translate.checked = data.translate;
            translate.dispatchEvent(new Event('change'));
            compareTitles.checked = data.compare_titles;
            compareTitles.dispatchEvent(new Event('change'));
            active.checked = data.active;
            active.dispatchEvent(new Event('change'));
            convertTime(data.daily_sync_at);
            feedList(data);
            return data;
        })
        .catch((err) => {
            console.log('Error: ', err);
            showMessage('Error fetching daily settings', 'error');
        });
}

function postDailySettings() {
    const data = {
        hours_summary: hoursSummary.value,
        process_read: processRead.checked,
        translate: translate.checked,
        compare_titles: compareTitles.checked,
        active: active.checked,
        sync_at: `${syncAtHours.value}:${syncAtMinutes.value}:00`,
    };
    fetch('/api/settings/daily', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
        credentials: 'include',
    })
        .then((response) => response.json())
        .then(() => {
            showMessage('Daily settings saved successfully', 'success');
            getDailySettings();
        })
        .catch((err) => {
            console.log('Error: ', err);
            showMessage('Error saving daily settings', 'error');
        });
}

function eventListeners() {
    active.addEventListener('change', () => {
        if (active.checked) {
            otherSettings.classList.remove('hidden');
            otherSettings.classList.add('flex', 'flex-col');
        } else {
            otherSettings.classList.remove('flex', 'flex-col');
            otherSettings.classList.add('hidden');
        }
    });

    save.addEventListener('click', () => {
        postDailySettings();
    });
}

export function initDailySettings() {
    eventListeners();
    getDailySettings();
}
