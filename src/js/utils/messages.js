/**
 * Displays a message to the user.
 *
 * @param {string} message - The message to display.
 * @param {string} type - The type of message ('error' or 'success').
 */

export function showMessage(message, type) {
    const messageContainer = document.createElement('div');
    messageContainer.innerHTML = `
            <div @click="open = false" x-data="{ open: false }" x-init="setTimeout(() => open = true, 100); setTimeout(() => open = false, 10100);" 
                x-show="open" 
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
