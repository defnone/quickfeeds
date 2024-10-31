const limit = 5;

export function getApiPath(lastItemId) {
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
