// Function to check the count of unread messages
export function checkUnreadCount() {
    fetch('/api/unread-count')
        .then((response) => response.json())
        .then((data) => {
            updateBadge(data.unread_count);
        })
        .catch((error) => console.error('Error when getting the number of unread messages: ', error));
}

// Function to update the badge with the unread count
function updateBadge(count) {
    //console.log('Setting badge count:', count);
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
    } else {
        console.error('Badge API not supported');
    }
}

export function initBadgeUpdate() {
    checkUnreadCount();
    setInterval(checkUnreadCount, 60000 * 5);
}
