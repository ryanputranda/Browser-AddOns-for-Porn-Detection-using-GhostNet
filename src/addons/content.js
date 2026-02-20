const API_THRESHOLD = 0.6;
const TARGET_LABELS = ["porn", "hentai", "sexy"]; // bisa include sexy kalau mau

function preBlur(img) {
    img.classList.add("pre-blur");
}

function blurImage(img) {
    img.classList.remove("pre-blur");
    img.classList.add("nsfw-blur");
    img.setAttribute("data-nsfw", "true");
}

function unblurImage(img) {
    img.classList.remove("pre-blur");
    img.classList.remove("nsfw-blur");
    img.setAttribute("data-nsfw", "false");
}

function scanImage(img) {
    if (!img.src || img.getAttribute("data-scanned")) return;

    img.setAttribute("data-scanned", "true");

    // 🔥 PREVENTIVE BLUR (langsung)
    preBlur(img);

    chrome.runtime.sendMessage({
        type: "CHECK_IMAGE",
        imageUrl: img.src
    }, (response) => {
        if (!response || !response.success) {
            // kalau API error → tetap blur (fail-safe)
            return;
        }

        const res = response.data;
        const label = res.prediksi;
        const conf = res.skor_confidence;

        if (
            TARGET_LABELS.includes(label) &&
            conf >= API_THRESHOLD
        ) {
            // NSFW → tetap blur
            blurImage(img);
        } else {
            // SAFE → unblur
            unblurImage(img);
        }
    });
}

function scanAllImages() {
    document.querySelectorAll("img").forEach(scanImage);
}

const observer = new MutationObserver(scanAllImages);

observer.observe(document.body, {
    childList: true,
    subtree: true
});

window.addEventListener("load", scanAllImages);