const slider = document.getElementById("threshold");

slider.oninput = () => {
    chrome.storage.sync.set({ threshold: slider.value });
};