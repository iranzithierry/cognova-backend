function compress_text(text) {
    return text.split().join(' ');
}
const formatContent = (content) => {
    const formattedContent = compress_text(content)
        .replace(/=+\n/g, '')
        .replace(/\n+/g, '\n')
        .replace(/_([^_]+)_/g, '<em>$1</em>')
        .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br/>')
        .replace(/(<br\/?>\s*){2,}/g, '<br/>');

    return formattedContent
}

