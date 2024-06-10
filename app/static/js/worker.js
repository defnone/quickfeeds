self.addEventListener(
    'message',
    function (e) {
        if (e.data === 'start') {
            checkUnreadCount();
            setInterval(checkUnreadCount, 60000);
        }

        function checkUnreadCount() {
            fetch('/api/unread-count')
                .then((response) => response.json())
                .then((data) => {
                    self.postMessage(data.unread_count);
                })
                .catch((error) =>
                    console.error(
                        'Error when getting the number of unread messages: ',
                        error
                    )
                );
        }
    },
    false
);
