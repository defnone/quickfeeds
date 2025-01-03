import sanitizeHtml from 'sanitize-html';

export function htmlToMarkdown(html) {
    // Sanitize HTML input
    html = sanitizeHtml(html, {
        allowedTags: [],
        allowedAttributes: {}
    });
    // Convert list items
    html = html.replace(/<li>(.*?)<\/li>/g, '- $1\n');
    // Convert unordered lists
    html = html.replace(/<\/ul>/g, '\n').replace(/<ul>/g, '');
    // Convert paragraphs
    html = html.replace(/<p>(.*?)<\/p>/g, '$1\n\n');
    // Remove other tags
    // Tags are already removed by sanitizeHtml
    return html;
}
