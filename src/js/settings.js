import { showMessage } from './utils/messages';

const updateIntervalInput = document.getElementById('update-interval');
const cleanAfterInput = document.getElementById('clean-after');
const timezoneSelect = document.getElementById('timezone');
const languageSelect = document.getElementById('language');
const groqApiKeyInput = document.getElementById('groq-api-key');
const checkGroqApiKeyButton = document.getElementById('check-groq-api-key');
const translateToggle = document.getElementById('translate');
const changePasswordButton = document.getElementById('change_password');
const newPasswordInput = document.getElementById('new_password');
const confirmPasswordInput = document.getElementById('confirm_password');
const saveSettingsButton = document.getElementById('save-settings');
const fontSizeSelect = document.getElementById('font-size');

export function getUserSettings() {
    fetch('/api/settings', {
        method: 'GET',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
        },
    })
        .then((response) => response.json())
        .then((data) => {
            updateIntervalInput.value = data.update_interval;
            cleanAfterInput.value = data.clean_after_days;
            timezoneSelect.value = data.timezone;
            languageSelect.value = data.language;
            groqApiKeyInput.value = data.groq_api_key;
            translateToggle.checked = data.translate;
            translateToggle.dispatchEvent(new Event('change'));
            fontSizeSelect.value = localStorage.getItem('font-size') || 'text-lg';
        })
        .catch((error) => {
            console.error('Error fetching settings:', error);
            showMessage('Failed to load settings', 'error');
        });
}

function saveUserSettings() {
    localStorage.setItem('font-size', fontSizeSelect.value);
    return new Promise((resolve, reject) => {
        const updateInterval = updateIntervalInput.value;
        const cleanAfterDays = cleanAfterInput.value;
        const timezone = timezoneSelect.value;
        const language = languageSelect.value;
        const translate = translateToggle.checked;
        let groqApiKey = groqApiKeyInput.value;

        let settings = {
            update_interval: updateInterval,
            clean_after_days: cleanAfterDays,
            timezone: timezone,
            language: language,
            translate: translate,
        };

        if (!/^[*]+$/.test(groqApiKey)) {
            settings.groq_api_key = groqApiKey;
        }

        fetch('/api/settings', {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(settings),
        })
            .then((response) => response.json())
            .then((data) => {
                showMessage('Settings saved successfully', 'success');
                resolve(data);
            })
            .catch((error) => {
                console.error('Error saving settings:', error);
                showMessage('Failed to save settings', 'error');
                reject(error);
            });
    });
}

function checkGroqApiKey() {
    saveUserSettings()
        .then(() => {
            return fetch('/api/groq/check', {
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json',
                },
                method: 'GET',
            });
        })
        .then((response) => response.json())
        .then((data) => {
            if (data.status === 'success') {
                showMessage('API key is valid', 'success');
            } else {
                showMessage('API key is invalid', 'error');
            }
        })
        .catch((error) => {
            console.error('Error checking API key:', error);
            showMessage(`Failed to check API key ${error}`, 'error');
        });
}

function changePassword() {
    const newPassword = newPasswordInput.value;
    const confirmPassword = confirmPasswordInput.value;

    fetch('/api/settings/change_password', {
        method: 'POST',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            new_password: newPassword,
            confirm_password: confirmPassword,
        }),
    })
        .then((response) => response.json())
        .then((data) => {
            if (data.status === 'success') {
                showMessage('Password changed successfully', 'success');
            } else {
                showMessage(data.error, 'error');
            }
        })
        .catch((error) => {
            console.error('Error changing password:', error);
            showMessage('Failed to change password', 'error');
        });
}

export function settingEventListeners() {
    checkGroqApiKeyButton.addEventListener('click', checkGroqApiKey);
    changePasswordButton.addEventListener('click', changePassword);
    saveSettingsButton.addEventListener('click', saveUserSettings);
}

export function safariDetector() {
    function isSafari() {
        const userAgent = navigator.userAgent.toLowerCase();
        return userAgent.includes('safari') && !userAgent.includes('chrome') && !userAgent.includes('android');
    }

    function isNotWebApp() {
        return !window.navigator.standalone;
    }

    if (isSafari() && isNotWebApp()) {
        document.getElementById('web-app-message').innerText =
            'You can create a Safari web app and open it as an application on your device (on macOS Sonoma and later or iOS 11.3 and later). Click the share button and select "Add to Dock" or "Add to Home Screen".';
    }
}
