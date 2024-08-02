export function swipeToReload() {
    let startY = null;
    window.addEventListener('touchstart', (event) => {
        startY = event.touches[0].clientY;
    });

    window.addEventListener('touchend', (event) => {
        const endY = event.changedTouches[0].clientY;
        const distance = endY - startY;
        if (distance > 200) {
            location.reload();
        }
    });
}
