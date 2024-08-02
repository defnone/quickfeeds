export function htmlToMarkdown(html) {
    // Convert list items
    html = html.replace(/<li>(.*?)<\/li>/g, '- $1\n');
    // Convert unordered lists
    html = html.replace(/<\/ul>/g, '\n').replace(/<ul>/g, '');
    // Convert paragraphs
    html = html.replace(/<p>(.*?)<\/p>/g, '$1\n\n');
    // Remove other tags
    html = html.replace(/<\/?[^>]+>/g, '');
    return html;
}
