import { showMessage } from './messages';
import { htmlToMarkdown } from './htmlToMD';

export function summarizeEnetListener() {
    document.addEventListener('click', function (event) {
        const summarizeBtn = event.target.closest('.ai-summarize-btn, .ai-summarize-daily-btn');
        const copyBtn = event.target.closest('.copy-btn');

        if (summarizeBtn) {
            let articleId;
            let isDaily = false;
            let feedContent;
            let postUrl;
            let itemTitle;
            let expHidden;

            if (summarizeBtn.classList.contains('ai-summarize-daily-btn')) {
                articleId = summarizeBtn.dataset.id;
                const dailyItem = summarizeBtn.closest('.daily-item');
                feedContent = dailyItem.querySelector('.d-content');
                itemTitle = dailyItem;
                isDaily = true;
            } else {
                const feedItem = summarizeBtn.closest('.feed-item');
                itemTitle = feedItem.querySelector('.item-title');
                postUrl = feedItem.querySelector('.item-title a').href;
                articleId = feedItem.dataset.id;
                feedContent = feedItem.querySelector('.feed-content');
                expHidden = feedItem.querySelector('#exp-hidden');

                if (expHidden) {
                    expHidden.setAttribute('x-data', '{expanded: true}');
                    expHidden.style.maxHeight = 'none';
                }
            }

            const itemPosition = itemTitle.getBoundingClientRect().top + window.scrollY;
            const offsetPercentage = 20;
            const offsetPixels = window.innerHeight * (offsetPercentage / 100);
            const offsetPosition = itemPosition - offsetPixels;

            window.scrollTo({
                top: offsetPosition,
                behavior: 'smooth',
            });

            const scrollDuration = 500; // duration in milliseconds

            const originalContent = feedContent.innerHTML;
            feedContent.innerHTML = `
            <div class="space-y-4 w-full">
                <div class="line"></div>
                <div class="line short"></div>
                <div class="line"></div>
                <div class="line"></div>
                <div class="line short"></div>
                <div class="line"></div>
                <div class="line"></div>
                <div class="line short"></div>
                <div class="line"></div>
                <div class="line"></div>
                <div class="line short"></div>
                <div class="line"></div>
            </div>`;

            const summarizeUrl = isDaily ? `/api/daily/summarize/${articleId}` : '/api/summarize';

            const requestBody = isDaily ? {} : { url: postUrl };

            setTimeout(() => {
                fetch(summarizeUrl, {
                    method: 'POST',
                    credentials: 'include',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(requestBody),
                })
                    .then((response) => response.json())
                    .then((data) => {
                        if (data.status === 'error') {
                            if (data.error.includes('Failed to get text')) {
                                feedContent.innerHTML = originalContent;
                                showMessage('Failed to get article text from the URL.', 'error');
                                return;
                            }
                            showMessage(
                                'Error summarizing the text. Check Groq API in <a class="underline" href="/settings">Settings</a>.',
                                'error'
                            );
                            feedContent.innerHTML = originalContent;
                        } else {
                            feedContent.innerHTML = `
                        <div class="w-full animate-itemShow">
                            <div id="summary-text">${data.summary}</div>
                        ${buttonTemplate()}
                        </div>`;
                        }
                    })
                    .catch((error) => {
                        showMessage('Error summarizing the text', 'error');
                        console.error('Error:', error);
                        feedContent.innerHTML = originalContent;
                    });
            }, scrollDuration);
        }

        if (copyBtn) {
            const summaryElement = copyBtn.parentElement.parentElement.querySelector('#summary-text');
            const summaryText = htmlToMarkdown(summaryElement.innerHTML);
            navigator.clipboard
                .writeText(summaryText)
                .then(() => {
                    showMessage('The text has been copied to clipboard.', 'success');
                })
                .catch((error) => {
                    console.error('Error copying text: ', error);
                    showMessage('Error copying text', 'error');
                });
        }
    });
}

const buttonTemplate = () => `
    <div class="w-fit mt-4 mb-4 ml-auto ">

        <button class="relative copy-btn flex ml-auto hover:text-stone-700 group">

        <span class="absolute bg-gray-900 rounded-md px-2.5 py-2 -top-1 left-0 -ml-56 text-nowrap invisible text-sm group-hover:visible  text-white">Copy summary to clipboard</span>   
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="size-6">
                <path fill-rule="evenodd" d="M7.502 6h7.128A3.375 3.375 0 0 1 18 9.375v9.375a3 3 0 0 0 3-3V6.108c0-1.505-1.125-2.811-2.664-2.94a48.972 48.972 0 0 0-.673-.05A3 3 0 0 0 15 1.5h-1.5a3 3 0 0 0-2.663 1.618c-.225.015-.45.032-.673.05C8.662 3.295 7.554 4.542 7.502 6ZM13.5 3A1.5 1.5 0 0 0 12 4.5h4.5A1.5 1.5 0 0 0 15 3h-1.5Z" clip-rule="evenodd" />
                <path fill-rule="evenodd" d="M3 9.375C3 8.339 3.84 7.5 4.875 7.5h9.75c1.036 0 1.875.84 1.875 1.875v11.25c0 1.035-.84 1.875-1.875 1.875h-9.75A1.875 1.875 0 0 1 3 20.625V9.375ZM6 12a.75.75 0 0 1 .75-.75h.008a.75.75 0 0 1 .75.75v.008a.75.75 0 0 1-.75.75H6.75a.75.75 0 0 1-.75-.75V12Zm2.25 0a.75.75 0 0 1 .75-.75h3.75a.75.75 0 0 1 0 1.5H9a.75.75 0 0 1-.75-.75ZM6 15a.75.75 0 0 1 .75-.75h.008a.75.75 0 0 1 .75.75v.008a.75.75 0 0 1-.75.75H6.75a.75.75 0 0 1-.75-.75V15Zm2.25 0a.75.75 0 0 1 .75-.75h3.75a.75.75 0 0 1 0 1.5H9a.75.75 0 0 1-.75-.75ZM6 18a.75.75 0 0 1 .75-.75h.008a.75.75 0 0 1 .75.75v.008a.75.75 0 0 1-.75.75H6.75a.75.75 0 0 1-.75-.75V18Zm2.25 0a.75.75 0 0 1 .75-.75h3.75a.75.75 0 0 1 0 1.5H9a.75.75 0 0 1-.75-.75Z" clip-rule="evenodd" />
            </svg>  
                
        </button>
        
        
    </div>`;
