const API_URL = "http://127.0.0.1:8000/predict";

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === "CHECK_IMAGE") {

        fetch(message.imageUrl)
            .then(res => res.blob())
            .then(blob => {
                const fd = new FormData();
                fd.append("file", blob, "image.jpg");

                return fetch(API_URL, {
                    method: "POST",
                    body: fd
                });
            })
            .then(res => res.json())
            .then(data => {
                sendResponse({ success: true, data });
            })
            .catch(err => {
                console.error("API error:", err);
                sendResponse({ success: false, error: err.toString() });
            });

        return true; // async
    }

});
