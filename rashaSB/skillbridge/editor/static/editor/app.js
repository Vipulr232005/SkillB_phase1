document.addEventListener("DOMContentLoaded", () => {
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("sidebarOverlay");
    const openBtn = document.getElementById("menuToggleBtn");
    const closeBtn = document.getElementById("closeSidebarBtn");

    function toggleSidebar(force) {
        if (!sidebar) return;
        const open = typeof force === "boolean" ? force : !sidebar.classList.contains("open");
        sidebar.classList.toggle("open", open);
        if (overlay) overlay.classList.toggle("open", open);
    }

    if (openBtn) openBtn.addEventListener("click", () => toggleSidebar(true));
    if (closeBtn) closeBtn.addEventListener("click", () => toggleSidebar(false));
    if (overlay) overlay.addEventListener("click", () => toggleSidebar(false));

    const trigger = document.getElementById("profileTrigger");
    const dropdown = document.getElementById("userProfileDropdown");
    if (trigger && dropdown) {
        trigger.addEventListener("click", (e) => {
            e.stopPropagation();
            dropdown.classList.toggle("show");
        });
        document.addEventListener("click", (e) => {
            if (!dropdown.contains(e.target) && !trigger.contains(e.target)) {
                dropdown.classList.remove("show");
            }
        });
    }

    function openModal(id) {
        const el = document.getElementById(id);
        if (el) el.classList.add("active");
        if (dropdown) dropdown.classList.remove("show");
    }

    function closeModal(id) {
        const el = document.getElementById(id);
        if (el) el.classList.remove("active");
    }

    document.querySelectorAll("[data-open-modal]").forEach((btn) => {
        btn.addEventListener("click", () => openModal(btn.getAttribute("data-open-modal")));
    });
    document.querySelectorAll("[data-close-modal]").forEach((btn) => {
        btn.addEventListener("click", () => closeModal(btn.getAttribute("data-close-modal")));
    });
    document.querySelectorAll(".modal-overlay").forEach((modal) => {
        modal.addEventListener("click", (e) => {
            if (e.target === modal) modal.classList.remove("active");
        });
    });

    const hiddenAvatar = document.getElementById("avatarInput");
    document.querySelectorAll(".avatar-option").forEach((btn) => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".avatar-option").forEach((b) => b.classList.remove("selected"));
            btn.classList.add("selected");
            if (hiddenAvatar) hiddenAvatar.value = btn.getAttribute("data-avatar");
        });
    });

    const addSkillModal = document.getElementById("addSkillModal");
    const skillTypeInput = document.getElementById("skillTypeInput");
    const addSkillTitle = document.getElementById("addSkillTitle");
    const addSkillSubmit = document.getElementById("addSkillSubmit");
    const levelLabel = document.getElementById("levelLabel");
    function setSkillType(type) {
        if (skillTypeInput) skillTypeInput.value = type;
        document.querySelectorAll("[data-type-choice]").forEach((b) => {
            b.classList.toggle("on", b.getAttribute("data-type-choice") === type);
        });
        const learn = type === "LEARN";
        if (addSkillTitle) addSkillTitle.textContent = learn ? "Add a skill to learn" : "Add a skill to teach";
        if (addSkillSubmit) addSkillSubmit.textContent = learn ? "Add to learning" : "Add skill to teach";
        if (levelLabel) levelLabel.firstChild.textContent = learn ? "Current level" : "Your level";
    }
    document.querySelectorAll("[data-type-choice]").forEach((b) => {
        b.addEventListener("click", () => setSkillType(b.getAttribute("data-type-choice")));
    });
    document.querySelectorAll("[data-skill-type]").forEach((btn) => {
        btn.addEventListener("click", () => {
            setSkillType(btn.getAttribute("data-skill-type"));
            if (addSkillModal) {
                addSkillModal.classList.add("active");
                const first = addSkillModal.querySelector("input[name=name]");
                if (first) setTimeout(() => first.focus(), 50);
            }
        });
    });

    const requestModal = document.getElementById("requestSessionModal");
    const requestSkillId = document.getElementById("requestSkillId");
    const requestHint = document.getElementById("requestSessionHint");
    document.querySelectorAll(".js-request").forEach((btn) => {
        btn.addEventListener("click", () => {
            if (requestSkillId) requestSkillId.value = btn.getAttribute("data-skill-id");
            if (requestHint) requestHint.textContent = btn.getAttribute("data-label") || "";
            if (requestModal) requestModal.classList.add("active");
        });
    });

    document.addEventListener("keydown", (e) => {
        if (e.key !== "Escape") return;
        document.querySelectorAll(".modal-overlay.active").forEach((m) => m.classList.remove("active"));
        if (dropdown) dropdown.classList.remove("show");
        toggleSidebar(false);
    });

    if (document.body.dataset.openEdit === "true") {
        openModal("editProfileModal");
    }
});
