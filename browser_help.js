// --- IMPROVED TWITTER SPACE URL HUNTER ---
(function() {
    console.clear();
    console.log("%c Twitter Space URL Hunter v2", "font-weight: bold; font-size: 20px; color: #1d9bf0");
    
    // Intercept future requests by overriding fetch
    const originalFetch = window.fetch;
    window.fetch = async function(...args) {
        const url = args[0]?.url || args[0];
        if (typeof url === 'string') {
            if (url.includes('.m3u8')) {
                console.log("%c🎵 PLAYLIST URL:", "color: lime; font-weight: bold");
                console.log(url);
            }
            if (url.includes('/key')) {
                console.log("%c🔑 KEY URL:", "color: cyan; font-weight: bold");
                console.log(url);
            }
        }
        return originalFetch.apply(this, args);
    };
    
    // Also intercept XHR
    const originalOpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(method, url) {
        if (url.includes('.m3u8')) {
            console.log("%c PLAYLIST URL (XHR):", "color: lime; font-weight: bold");
            console.log(url);
        }
        if (url.includes('/key')) {
            console.log("%c KEY URL (XHR):", "color: cyan; font-weight: bold");
            console.log(url);
        }
        return originalOpen.apply(this, arguments);
    };
    
    console.log("%c Interceptors installed!", "color: green; font-weight: bold");
    console.log("Now REFRESH the page or seek in the Space audio.");
    console.log("URLs will appear here as they're requested.");
    console.log("");
    console.log("%c FOR COOKIES:", "color: yellow; font-weight: bold");
    console.log("1. Open Network tab (F12 → Network)");
    console.log("2. Filter by 'key' or 'm3u8'");
    console.log("3. Click any matching request");
    console.log("4. Headers → Request Headers → Cookie → Right-click → Copy value");
})();
