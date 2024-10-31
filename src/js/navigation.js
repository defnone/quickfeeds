const btnDefault = document.getElementById('btnDefault');
const btnAll = document.getElementById('btnAll');

export function setButtonStyles() {
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

export function navigationEventListeners() {
    btnDefault.addEventListener('click', navigateDefault);
    btnAll.addEventListener('click', navigateAll);
}
