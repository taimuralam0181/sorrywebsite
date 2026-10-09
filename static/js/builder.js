(() => {
    const $ = (selector) => document.querySelector(selector);
    const fields = {
        herName: $("#her-name"),
        yourName: $("#your-name"),
        sorryMessage: $("#sorry-message"),
        letterTitle: $("#letter-title"),
        letterMessage: $("#letter-message"),
        signature: $("#signature"),
        photoCaption: $("#photo-caption"),
    };
    const defaults = {
        herName: "",
        yourName: "",
        sorryMessage: "",
        letterTitle: "I'm Sorry 🥺",
        letterMessage: "",
        signature: "",
        photoCaption: "",
    };
    const photoInput = $("#photo-input");
    let photoUrl = "";
    let galleryUrls = [];
    const videoFields = [
        {
            input: $("#sorry-video-input"),
            name: $("#sorry-video-name"),
            error: $("#sorry-video-error"),
            preview: $("#preview-sorry-video"),
            wrap: $("#preview-sorry-video-wrap"),
            url: "",
        },
        {
            input: $("#memory-video-input"),
            name: $("#memory-video-name"),
            error: $("#memory-video-error"),
            preview: $("#preview-memory-video"),
            wrap: $("#preview-memory-video-wrap"),
            url: "",
        },
    ];
    const peopleFields = $("#people-message-fields");
    const selectedPeople = new Map();

    const valueOr = (field, fallback) => field.value.trim() || fallback;

    function updatePreview() {
        $("#preview-name").textContent = valueOr(fields.herName, "Beautiful");
        $("#preview-message").textContent = valueOr(fields.sorryMessage, "I know you're angry with me... and I'm really sorry. 🥺❤️");
        $("#preview-letter-title").textContent = valueOr(fields.letterTitle, defaults.letterTitle);
        $("#preview-letter-message").textContent = valueOr(fields.letterMessage, "Write your heart out...");
        const defaultSignature = fields.yourName.value.trim()
            ? `— ${fields.yourName.value.trim()} ❤️`
            : "— Your Name ❤️";
        $("#preview-signature").textContent = valueOr(fields.signature, defaultSignature);
        $("#preview-photo-caption").textContent = valueOr(fields.photoCaption, "A moment worth remembering 📸");
    }

    function setTheme(theme) {
        $("#phone-screen").dataset.theme = theme;
        $("#theme-input").value = theme;
        document.querySelectorAll(".theme-option").forEach((option) => {
            option.classList.toggle("active", option.dataset.theme === theme);
        });

    }

    function clearPhoto() {
        if (photoUrl) URL.revokeObjectURL(photoUrl);
        galleryUrls.forEach((url) => URL.revokeObjectURL(url));
        photoUrl = "";
        galleryUrls = [];
        photoInput.value = "";
        $("#preview-photo").removeAttribute("src");
        $("#preview-photo").hidden = true;
        $("#preview-photo-wrap").classList.add("photo-placeholder");
        $("#preview-photo-wrap").classList.remove("has-media");
        $("#preview-photo-caption").classList.remove("hidden");
        $("#remove-photo").classList.add("hidden");
        $("#photo-name").textContent = "0 / 5 photos selected";
        $("#photo-thumbnails").replaceChildren();
    }

    function clearVideos() {
        videoFields.forEach(({ input, name, error, preview, wrap }, index) => {
            const field = videoFields[index];
            if (field.url) URL.revokeObjectURL(field.url);
            field.url = "";
            input.value = "";
            name.textContent = "";
            error.textContent = "";
            preview.pause();
            preview.removeAttribute("src");
            preview.load();
            wrap.classList.add("video-placeholder");
            wrap.classList.remove("has-media");
        });
    }

    function renderPeopleFields() {
            peopleFields.replaceChildren();
            document.querySelectorAll("[data-relationship]:checked").forEach((checkbox) => {
                const relationship = checkbox.dataset.relationship;
                const maximum = relationship === "Baby" ? 3 : 10;
                const count = selectedPeople.get(relationship) || 1;
                selectedPeople.set(relationship, count);
                const group = document.createElement("div");
                group.className = "people-message-group";
                const heading = document.createElement("div");
                heading.className = "people-group-heading";
                heading.innerHTML = `<h3>${relationship === "Baby" ? "👶 A Little Message From Baby ❤️" : relationship}</h3><label>Number of people <button type="button" class="count-button" data-direction="-1" aria-label="Decrease number">−</button><output>${count}</output><button type="button" class="count-button" data-direction="1" aria-label="Increase number">+</button><input type="hidden" name="people_count_${relationship}" value="${count}"></label>`;
                group.appendChild(heading);
                for (let index = 0; index < count; index += 1) {
                    const entry = document.createElement("div");
                    entry.className = "person-message-entry";
                    entry.innerHTML = `<strong>${relationship === "Baby" ? "👶 Baby" : relationship} #${index + 1}</strong><label>Name ${relationship === "Baby" ? "(optional)" : ""}<input type="text" name="people_${relationship}_${index}_name" maxlength="100" placeholder="${relationship === "Baby" ? "Baby's name" : "Their name"}"></label><label>Short Video<input type="file" name="people_${relationship}_${index}_video" accept=".mp4,.webm,video/mp4,video/webm"><small class="people-file-status"></small></label>`;
                    const fileInput = entry.querySelector('input[type="file"]');
                    fileInput.addEventListener("change", () => {
                        const status = entry.querySelector(".people-file-status");
                        const file = fileInput.files[0];
                        if (!file) { status.textContent = ""; return; }
                        if (!/\.(mp4|webm)$/i.test(file.name) || !["video/mp4", "video/webm"].includes(file.type) || file.size > 50 * 1024 * 1024) {
                            fileInput.value = "";
                            status.textContent = "Please choose a valid MP4 or WEBM under 50 MB.";
                            status.classList.add("is-error");
                        } else {
                            status.textContent = `✓ ${file.name}`;
                            status.classList.remove("is-error");
                        }
                    });
                    group.appendChild(entry);
                }
                heading.querySelectorAll(".count-button").forEach((button) => {
                    button.addEventListener("click", () => {
                        const next = Math.max(1, Math.min(maximum, count + Number(button.dataset.direction)));
                        selectedPeople.set(relationship, next);
                        renderPeopleFields();
                    });
                });
                peopleFields.appendChild(group);
            });
        }

    document.querySelectorAll("[data-relationship]").forEach((checkbox) => {
        checkbox.addEventListener("change", renderPeopleFields);
    });

    Object.values(fields).forEach((field) => field.addEventListener("input", updatePreview));
    document.querySelectorAll(".theme-option").forEach((option) => {
        option.addEventListener("click", () => setTheme(option.dataset.theme));
    });

    photoInput.addEventListener("change", () => {
        const selectedFiles = Array.from(photoInput.files);
        const files = selectedFiles.slice(0, 5);
        if (selectedFiles.length > 5) {
            const transfer = new DataTransfer();
            files.forEach((file) => transfer.items.add(file));
            photoInput.files = transfer.files;
        }
        if (!files.length) return;
        galleryUrls.forEach((url) => URL.revokeObjectURL(url));
        galleryUrls = files.map((file) => URL.createObjectURL(file));
        photoUrl = galleryUrls[0];
        $("#preview-photo").src = photoUrl;
        $("#preview-photo").hidden = false;
        $("#preview-photo-wrap").classList.remove("hidden");
        $("#preview-photo-caption").classList.remove("hidden");
        $("#remove-photo").classList.remove("hidden");
        $("#photo-name").textContent = `${files.length} / 5 photos selected`;
        const thumbnails = $("#photo-thumbnails");
        thumbnails.replaceChildren();
        files.forEach((file, index) => {
            const item = document.createElement("div");
            item.className = "photo-thumb";
            item.innerHTML = `<img src="${galleryUrls[index]}" alt="Selected photo ${index + 1}"><button type="button" aria-label="Remove selected photo ${index + 1}">×</button>`;
            item.querySelector("button").addEventListener("click", () => {
                const transfer = new DataTransfer();
                Array.from(photoInput.files).forEach((current, currentIndex) => {
                    if (currentIndex !== index) transfer.items.add(current);
                });
                photoInput.files = transfer.files;
                photoInput.dispatchEvent(new Event("change"));
            });
            thumbnails.appendChild(item);
        });
        $("#preview-photo-wrap").classList.remove("photo-placeholder");
        $("#preview-photo-wrap").classList.add("has-media");
    });

    videoFields.forEach((field) => {
        const { input, name, error, preview, wrap } = field;
        input.addEventListener("change", () => {
            const file = input.files[0];
            if (field.url) URL.revokeObjectURL(field.url);
            field.url = "";
            error.textContent = "";
            name.textContent = "";
            preview.pause();
            preview.removeAttribute("src");
            preview.load();
            wrap.classList.add("video-placeholder");
            wrap.classList.remove("has-media");
            if (!file) return;
            const validExtension = /\.(mp4|webm)$/i.test(file.name);
            const validType = ["video/mp4", "video/webm"].includes(file.type);
            if (!validExtension || !validType || file.size > 50 * 1024 * 1024) {
                input.value = "";
                error.textContent = "Please choose a valid MP4 or WEBM video smaller than 50 MB.";
                return;
            }
            field.url = URL.createObjectURL(file);
            preview.src = field.url;
            preview.load();
            wrap.classList.remove("video-placeholder");
            wrap.classList.add("has-media");
            name.textContent = `✓ ${file.name}`;
        });
    });

    $("#remove-photo").addEventListener("click", clearPhoto);

    $("#reset-builder").addEventListener("click", () => {
        Object.entries(defaults).forEach(([key, value]) => {
            fields[key].value = value;
        });
        setTheme("romantic");
        clearPhoto();
        clearVideos();
        selectedPeople.clear();
        document.querySelectorAll("[data-relationship]").forEach((checkbox) => { checkbox.checked = false; });
        renderPeopleFields();
        $("#letter-card").className = "letter-card is-closed";
        $("#forgive-response").textContent = "";
        $("#forgive-response").className = "forgive-response";
        updatePreview();
    });

    $("#preview-builder").addEventListener("click", () => {
        const preview = $("#live-preview");
        preview.classList.remove("preview-pulse");
        void preview.offsetWidth;
        preview.classList.add("preview-pulse");
        preview.scrollIntoView({ behavior: "smooth", block: "center" });
    });

    $("#open-letter").addEventListener("click", () => {
        $("#letter-card").classList.remove("is-closed");
        $("#letter-card").classList.add("is-open");
    });

    $("#forgive-yes").addEventListener("click", () => {
        $("#forgive-response").textContent = "You just made my whole heart smile ❤️";
        $("#forgive-response").className = "forgive-response response-positive";
    });

    $("#forgive-angry").addEventListener("click", () => {
        $("#forgive-response").textContent = "That's okay... I'll keep choosing you, every day 🥺";
        $("#forgive-response").className = "forgive-response response-gentle";
    });

    updatePreview();
})();
