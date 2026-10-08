(() => {
    const opening = document.querySelector("#opening-scene");
    const openSurprise = document.querySelector("#open-surprise");
    const content = document.querySelector("#surprise-content");
    const forgiveness = document.querySelector("#forgiveness");
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    openSurprise.addEventListener("click", () => {
        document.querySelector(".opening-envelope")?.classList.add("is-open");
        content.setAttribute("aria-hidden", "false");
        const revealDelay = reduceMotion ? 0 : 700;
        window.setTimeout(() => opening.classList.add("is-leaving"), revealDelay);
        window.setTimeout(() => {
            content.classList.add("is-visible");
            startTypewriter();
            content.querySelector(".surprise-hero")?.scrollIntoView({
                behavior: reduceMotion ? "auto" : "smooth",
                block: "start",
            });

            function startTypewriter() {
                const target = document.querySelector("#typewriter-text");
                if (!target || target.dataset.started) return;
                target.dataset.started = "true";
                const recipient = document.body.dataset.recipient || "Someone special";
                const lines = `${recipient}...\n\nI know I messed up.\n\nAnd I'm genuinely sorry. ❤️`;
                if (reduceMotion) {
                    target.textContent = lines;
                    return;
                }
                let position = 0;
                const typeNext = () => {
                    target.textContent = lines.slice(0, position);
                    if (position < lines.length) {
                        position += 1;
                        window.setTimeout(typeNext, lines[position - 1] === "\n" ? 100 : 34);
                    }
                };
                typeNext();
            }
        }, reduceMotion ? 0 : 900);
    });

    const revealObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.classList.add("is-revealed");
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.12 });
    document.querySelectorAll(".reveal").forEach((section) => revealObserver.observe(section));

    document.querySelectorAll("img, video").forEach((media) => {
        const markLoaded = () => media.closest(".public-section")?.classList.add("is-loaded");
        media.addEventListener("load", markLoaded);
        media.addEventListener("loadeddata", markLoaded);
        media.addEventListener("error", () => {
            if (media.classList.contains("gallery-image")) return;
            const peopleSection = media.closest(".people-messages-section");
            const section = media.closest(".people-message-item, .public-section");
            if (section) section.remove();
            if (peopleSection && !peopleSection.querySelector(".people-message-item")) peopleSection.remove();
        });
        if (media.complete || media.readyState >= 3) markLoaded();
    });

    document.querySelectorAll(".video-section").forEach((section) => {
        const video = section.querySelector("video");
        const readyMessage = section.querySelector(".video-ready");
        const completeMessage = section.querySelector(".video-complete");
        video?.addEventListener("play", () => readyMessage?.classList.add("is-dismissed"));
        video?.addEventListener("ended", () => {
            if (completeMessage) {
                completeMessage.hidden = false;
                completeMessage.classList.add("is-visible");
            }
        });
    });

    const gallery = document.querySelector("#memory-gallery");
    const galleryImages = gallery ? Array.from(gallery.querySelectorAll(".gallery-image")) : [];
    const galleryCaption = gallery?.querySelector(".gallery-caption");
    let galleryIndex = 0;
    let galleryStartX = 0;
    let galleryStartY = 0;
    const galleryCaptions = galleryImages.map((image) => image.dataset.caption || "");

    function showGalleryImage(index) {
        if (!galleryImages.length) return;
        galleryIndex = (index + galleryImages.length) % galleryImages.length;
        galleryImages.forEach((image, imageIndex) => image.classList.toggle("is-hidden", imageIndex !== galleryIndex));
        gallery?.querySelectorAll(".gallery-dots button").forEach((dot, dotIndex) => {
            dot.setAttribute("aria-selected", String(dotIndex === galleryIndex));
        });
        if (galleryCaption) {
            galleryCaption.textContent = galleryCaptions[galleryIndex] || "";
            galleryCaption.hidden = !galleryCaption.textContent;
        }
        const lightboxImage = document.querySelector("#lightbox-image");
        if (lightboxImage) {
            lightboxImage.src = galleryImages[galleryIndex].src;
            lightboxImage.alt = galleryImages[galleryIndex].alt;
        }
    }

    if (gallery) {
        galleryImages.forEach((image, imageIndex) => {
            image.addEventListener("click", () => {
                showGalleryImage(imageIndex);
                document.querySelector("#photo-lightbox").classList.add("is-open");
                document.querySelector("#photo-lightbox").setAttribute("aria-hidden", "false");
            });
            image.addEventListener("error", () => {
                image.remove();
                galleryImages.splice(galleryImages.indexOf(image), 1);
                if (!galleryImages.length) gallery.remove();
                else showGalleryImage(Math.min(galleryIndex, galleryImages.length - 1));
            });
        });
        gallery.querySelector(".gallery-prev")?.addEventListener("click", () => showGalleryImage(galleryIndex - 1));
        gallery.querySelector(".gallery-next")?.addEventListener("click", () => showGalleryImage(galleryIndex + 1));
        gallery.querySelectorAll(".gallery-dots button").forEach((dot) => {
            dot.addEventListener("click", () => showGalleryImage(Number(dot.dataset.index)));
        });
        gallery.addEventListener("touchstart", (event) => {
            galleryStartX = event.touches[0].clientX;
            galleryStartY = event.touches[0].clientY;
        }, { passive: true });
        gallery.addEventListener("touchend", (event) => {
            const deltaX = event.changedTouches[0].clientX - galleryStartX;
            const deltaY = event.changedTouches[0].clientY - galleryStartY;
            if (Math.abs(deltaX) > 45 && Math.abs(deltaX) > Math.abs(deltaY) * 1.3) {
                showGalleryImage(galleryIndex + (deltaX < 0 ? 1 : -1));
            }
        }, { passive: true });
        showGalleryImage(0);
        if (galleryImages.length < 2) {
            gallery.querySelectorAll(".gallery-arrow, .gallery-dots").forEach((control) => control.remove());
        }
    }

    const lightbox = document.querySelector("#photo-lightbox");
    const closeLightbox = () => {
        lightbox?.classList.remove("is-open");
        lightbox?.setAttribute("aria-hidden", "true");
    };
    lightbox?.querySelector(".lightbox-close")?.addEventListener("click", closeLightbox);
    lightbox?.addEventListener("click", (event) => {
        if (event.target === lightbox) closeLightbox();
    });
    lightbox?.querySelector(".lightbox-prev")?.addEventListener("click", () => showGalleryImage(galleryIndex - 1));
    lightbox?.querySelector(".lightbox-next")?.addEventListener("click", () => showGalleryImage(galleryIndex + 1));
    document.addEventListener("keydown", (event) => {
        const tagName = document.activeElement?.tagName;
        if (["INPUT", "TEXTAREA", "SELECT"].includes(tagName)) return;
        if (event.key === "Escape") closeLightbox();
        if (galleryImages.length > 1 && event.key === "ArrowLeft") showGalleryImage(galleryIndex - 1);
        if (galleryImages.length > 1 && event.key === "ArrowRight") showGalleryImage(galleryIndex + 1);
    });

    const letterButton = document.querySelector("#open-letter");
    if (letterButton) {
        letterButton.addEventListener("click", () => {
            document.querySelector("#public-letter").classList.add("is-open");
            document.body.classList.add("letter-open");
        });
    }

    document.querySelector("#continue-button")?.addEventListener("click", () => {
        forgiveness.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "center" });
    });

    const actions = document.querySelector(".forgive-actions");
    const result = document.querySelector("#forgive-result");
    const tryAgain = document.querySelector("#try-again");

    document.querySelector("#yes-button").addEventListener("click", () => {
        actions.classList.add("is-hidden");
        result.innerHTML = "<strong>Thank You ❤️</strong><br>You just made my day. 🥹<br><small>I promise I'll try to do better.</small>";
        result.className = "forgive-result celebrate";
        forgiveness.classList.add("celebrating");
        for (let index = 0; index < 18; index += 1) {
            const particle = document.createElement("span");
            particle.textContent = index % 2 ? "♥" : "✨";
            particle.className = "celebration-particle";
            particle.style.left = `${10 + Math.random() * 80}%`;
            particle.style.top = `${45 + Math.random() * 35}%`;
            document.body.appendChild(particle);
            setTimeout(() => particle.remove(), 1800);
        }
    });

    document.querySelector("#angry-button").addEventListener("click", () => {
        actions.classList.add("is-hidden");
        result.textContent = "Okay... I'm sorry again. 🥺❤️\nI'll wait until you're ready.";
        result.className = "forgive-result celebrate";
        tryAgain.classList.add("is-visible");
    });

    tryAgain.addEventListener("click", () => {
        actions.classList.remove("is-hidden");
        result.textContent = "";
        result.className = "forgive-result";
        tryAgain.classList.remove("is-visible");
    });
})();
