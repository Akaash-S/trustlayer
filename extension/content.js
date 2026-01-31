// TrustLayer Content Script

console.log("🛡️ TrustLayer Guard Active");

const API_URL = "http://localhost:8000/v1/sanitize";
let DEBOUNCE_TIMER;

// 1. Listen for inputs
document.addEventListener("input", (e) => {
    const target = e.target;

    // Only target text areas or editable divs (common in LLM chats)
    if (target.tagName === "TEXTAREA" || target.getAttribute("contenteditable") === "true") {
        handleInput(target);
    }
}, true);

function handleInput(target) {
    // Basic debounce to avoid spamming API
    clearTimeout(DEBOUNCE_TIMER);
    DEBOUNCE_TIMER = setTimeout(() => {
        scanAndClean(target);
    }, 1000); // Wait 1 second after typing stops
}

async function scanAndClean(target) {
    let text = "";
    if (target.tagName === "TEXTAREA") {
        text = target.value;
    } else {
        text = target.innerText;
    }

    if (!text || text.length < 5) return;

    // Send to API
    try {
        const formData = new FormData();
        formData.append("prompt", text);

        const response = await fetch(API_URL, {
            method: "POST",
            body: formData
        });

        if (response.ok) {
            const data = await response.json();

            // Check if changes needed
            if (data.sanitized_text !== text) {
                console.log("⚠️ PII Detected! Sanitizing...");

                // Visual Indicator
                showNotification("TrustLayer: PII Redacted");

                // Replacement
                if (target.tagName === "TEXTAREA") {
                    target.value = data.sanitized_text;
                } else {
                    target.innerText = data.sanitized_text;
                }
            }
        }
    } catch (e) {
        console.error("TrustLayer Connection Failed:", e);
    }
}

// Simple Notification UI
function showNotification(msg) {
    let box = document.getElementById("trustlayer-notify");
    if (!box) {
        box = document.createElement("div");
        box.id = "trustlayer-notify";
        document.body.appendChild(box);
    }
    box.innerText = msg;
    box.className = "show";
    setTimeout(() => { box.className = ""; }, 3000);
}
