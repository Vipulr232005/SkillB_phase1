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
    document.querySelectorAll("[data-skill-type]").forEach((btn) => {
        btn.addEventListener("click", () => {
            const type = btn.getAttribute("data-skill-type");
            const input = document.getElementById("skillTypeInput");
            const title = document.getElementById("addSkillTitle");
            if (input) input.value = type;
            if (title) title.textContent = type === "LEARN" ? "Add a skill to learn" : "Add a skill to teach";
            if (addSkillModal) addSkillModal.classList.add("active");
        });
    });

    const requestModal = document.getElementById("requestSessionModal");
    const requestSkillId = document.getElementById("requestSkillId");
    const requestHint = document.getElementById("requestSessionHint");
    document.querySelectorAll(".js-request").forEach((btn) => {
        btn.addEventListener("click", () => {
            if (requestSkillId) requestSkillId.value = btn.getAttribute("data-skill-id");
            if (requestHint) requestHint.textContent = "Request: " + (btn.getAttribute("data-label") || "");
            if (requestModal) requestModal.classList.add("active");
        });
    });

    if (document.body.dataset.openEdit === "true") {
        openModal("editProfileModal");
    }
});
