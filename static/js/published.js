const copyButton = document.querySelector("#copy-link");
const shareUrl = document.querySelector("#share-url").textContent.trim();
const shareMessage = `I made something for you ❤️ Open this: ${shareUrl}`;

async function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
        return;
    }
    const input = document.createElement("textarea");
    input.value = text;
    input.setAttribute("readonly", "");
    input.style.position = "fixed";
    input.style.opacity = "0";
    document.body.appendChild(input);
    input.select();
    document.execCommand("copy");
    input.remove();
}

if (copyButton) {
    copyButton.addEventListener("click", async () => {
        try {
            await copyText(shareUrl);
            copyButton.textContent = "Copied ✓";
            document.querySelector("#copy-status").textContent = "Link copied to clipboard ❤️";
            window.setTimeout(() => {
                copyButton.textContent = "Copy Link 🔗";
                document.querySelector("#copy-status").textContent = "";
            }, 2200);
        } catch (error) {
            document.querySelector("#copy-status").textContent = "Unable to copy automatically. Please copy the URL above.";
        }
    });
}

document.querySelector("#native-share")?.addEventListener("click", async () => {
    if (navigator.share) {
        try {
            await navigator.share({ title: "A little Sorry surprise ❤️", text: shareMessage, url: shareUrl });
        } catch (error) {
            if (error.name !== "AbortError") {
                document.querySelector("#copy-status").textContent = "Sharing is unavailable right now.";
            }
        }
    } else {
        try {
            await copyText(shareUrl);
            document.querySelector("#copy-status").textContent = "Link copied to clipboard ❤️";
        } catch (error) {
            document.querySelector("#copy-status").textContent = "Unable to copy automatically. Please copy the URL above.";
        }
    }
});
