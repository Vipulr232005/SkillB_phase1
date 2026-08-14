/* ==========================================================================
   Skill Bridge - Interactive Peer-to-Peer Student Platform Logic
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    // Master Peer Mentors Data Set
    const peersData = [
        {
            id: 1,
            name: "Alex Rivera",
            role: "Python & Data Structures",
            skillTag: "Python & DSA",
            langKey: "python",
            rating: "4.9 (42 reviews)",
            rate: "$15 / hr",
            priceCategory: "under15",
            status: "online",
            avatar: "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?auto=format&fit=crop&q=80&w=250",
            about: "CS Senior at MIT. 3+ years experience with Python algorithms, Leetcode prep, and clean code principles.",
            sessions: 42
        },
        {
            id: 2,
            name: "Sophia Chen",
            role: "React & Modern UI/UX",
            skillTag: "React & UI/UX",
            langKey: "react",
            rating: "5.0 (68 reviews)",
            rate: "Free Swap",
            priceCategory: "free",
            status: "online",
            avatar: "https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&q=80&w=250",
            about: "UI/UX Designer and Frontend Specialist. Love helping students craft beautiful responsive web apps.",
            sessions: 68
        },
        {
            id: 3,
            name: "Marcus Vance",
            role: "C++ & Low-Level Systems",
            skillTag: "C++ & Algorithms",
            langKey: "cpp",
            rating: "4.8 (31 reviews)",
            rate: "$12 / hr",
            priceCategory: "under15",
            status: "busy",
            avatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&q=80&w=250",
            about: "Passionate about memory management, pointers, and Competitive Programming in C++20.",
            sessions: 31
        },
        {
            id: 4,
            name: "Priya Sharma",
            role: "AI & Machine Learning",
            skillTag: "AI & ML",
            langKey: "ai",
            rating: "4.9 (55 reviews)",
            rate: "$18 / hr",
            priceCategory: "15plus",
            status: "online",
            avatar: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&q=80&w=250",
            about: "Machine Learning Researcher. Expert in PyTorch, TensorFlow, and Data Science pipelines.",
            sessions: 55
        },
        {
            id: 5,
            name: "David Kim",
            role: "Full Stack Web & Node.js",
            skillTag: "Node & Express",
            langKey: "react",
            rating: "4.7 (24 reviews)",
            rate: "Free Swap",
            priceCategory: "free",
            status: "online",
            avatar: "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&q=80&w=250",
            about: "Backend developer specializing in REST APIs, PostgreSQL databases, and async JavaScript.",
            sessions: 24
        },
        {
            id: 6,
            name: "Elena Rostova",
            role: "Figma UI/UX & Design Systems",
            skillTag: "UI/UX & Figma",
            langKey: "uiux",
            rating: "5.0 (89 reviews)",
            rate: "$20 / hr",
            priceCategory: "15plus",
            status: "online",
            avatar: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&q=80&w=250",
            about: "Lead designer for student tech projects. Specializing in micro-animations and accessibility.",
            sessions: 89
        }
    ];

    // DOM Elements
    const sidebar = document.getElementById('sidebar');
    const menuToggleBtn = document.getElementById('menuToggleBtn');
    const closeSidebarBtn = document.getElementById('closeSidebarBtn');
    const sidebarOverlay = document.getElementById('sidebarOverlay');

    const navItems = document.querySelectorAll('.nav-item');
    const viewSections = document.querySelectorAll('.view-section');
    const pageTitle = document.getElementById('pageTitle');

    const notifBtn = document.getElementById('notifBtn');
    const notifDropdown = document.getElementById('notifDropdown');

    const profileModal = document.getElementById('profileModal');
    const modalCloseBtn = document.getElementById('modalCloseBtn');
    const toastContainer = document.getElementById('toastContainer');

    // 1. Sidebar Navigation Toggle
    function toggleSidebar() {
        sidebar.classList.toggle('active');
        sidebarOverlay.classList.toggle('active');
    }

    if (menuToggleBtn) menuToggleBtn.addEventListener('click', toggleSidebar);
    if (closeSidebarBtn) closeSidebarBtn.addEventListener('click', toggleSidebar);
    if (sidebarOverlay) sidebarOverlay.addEventListener('click', toggleSidebar);

    // 2. View Switching Logic
    function switchView(viewId) {
        // Update nav item active states
        navItems.forEach(item => {
            if (item.getAttribute('data-view') === viewId) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });

        // Hide all views, show requested view
        viewSections.forEach(section => {
            if (section.id === viewId + 'View') {
                section.classList.add('active');
            } else {
                section.classList.remove('active');
            }
        });

        // Update Page Titles
        const titles = {
            dashboard: { title: "Dashboard", sub: "Welcome back, Raveena! Connect and learn with peers today." },
            peers: { title: "Peer Mentors & Learning Partners", sub: "Discover verified student coders for pair sessions and doubt solving." },
            studio: { title: "Live Code Studio", sub: "Real-time collaborative code editor with video, compiler, and live chat." },
            earnings: { title: "Earnings & Bounty Analytics", sub: "Track your income earned by mentoring and solving student doubts." },
            forum: { title: "Student Doubt Forum", sub: "Browse bounties posted by peers or post your own coding doubt." }
        };

        if (titles[viewId]) {
            pageTitle.textContent = titles[viewId].title;
            const subElem = document.querySelector('.page-subtitle');
            if (subElem) subElem.textContent = titles[viewId].sub;
        }

        // Close mobile sidebar if open
        if (sidebar.classList.contains('active')) {
            toggleSidebar();
        }
    }

    // Attach click handlers for sidebar nav
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const viewId = item.getAttribute('data-view');
            switchView(viewId);
        });
    });

    // Attach generic view switch buttons
    document.addEventListener('click', (e) => {
        const switchBtn = e.target.closest('.switch-view-btn');
        if (switchBtn) {
            const targetView = switchBtn.getAttribute('data-target');
            if (targetView) switchView(targetView);
        }
    });

    // 3. Notifications Dropdown Toggle
    if (notifBtn && notifDropdown) {
        notifBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            notifDropdown.classList.toggle('show');
        });

        document.addEventListener('click', (e) => {
            if (!notifDropdown.contains(e.target) && !notifBtn.contains(e.target)) {
                notifDropdown.classList.remove('show');
            }
        });
    }

    // 4. Figma Carousel Scroll
    const prevCardBtn = document.getElementById('prevCardBtn');
    const nextCardBtn = document.getElementById('nextCardBtn');
    const peerCardsGrid = document.getElementById('peerCardsGrid');

    if (prevCardBtn && nextCardBtn && peerCardsGrid) {
        prevCardBtn.addEventListener('click', () => {
            peerCardsGrid.scrollBy({ left: -220, behavior: 'smooth' });
        });
        nextCardBtn.addEventListener('click', () => {
            peerCardsGrid.scrollBy({ left: 220, behavior: 'smooth' });
        });
    }

    // 5. Dynamic Peer Mentors Grid Rendering & Filtering (Peers View)
    const fullPeersGrid = document.getElementById('fullPeersGrid');
    const languageFilter = document.getElementById('languageFilter');
    const priceFilter = document.getElementById('priceFilter');
    const peerSearchInput = document.getElementById('peerSearchInput');

    function renderPeersGrid() {
        if (!fullPeersGrid) return;

        const langVal = languageFilter ? languageFilter.value : 'all';
        const priceVal = priceFilter ? priceFilter.value : 'all';
        const searchVal = peerSearchInput ? peerSearchInput.value.toLowerCase().trim() : '';

        const filtered = peersData.filter(peer => {
            const matchLang = (langVal === 'all') || (peer.langKey === langVal);
            const matchPrice = (priceVal === 'all') || (peer.priceCategory === priceVal);
            const matchSearch = (peer.name.toLowerCase().includes(searchVal)) ||
                (peer.role.toLowerCase().includes(searchVal)) ||
                (peer.about.toLowerCase().includes(searchVal));
            return matchLang && matchPrice && matchSearch;
        });

        if (filtered.length === 0) {
            fullPeersGrid.innerHTML = `
                <div style="grid-column: 1/-1; text-align: center; padding: 3rem; color: var(--text-secondary);">
                    <i class="fa-solid fa-user-slash" style="font-size: 2.5rem; margin-bottom: 1rem; color: var(--text-muted);"></i>
                    <h3>No peer mentors found</h3>
                    <p>Try adjusting your search query or filter settings.</p>
                </div>
            `;
            return;
        }

        fullPeersGrid.innerHTML = filtered.map(peer => `
            <div class="peer-card">
                <div class="card-avatar-wrapper">
                    <img src="${peer.avatar}" alt="${peer.name}" class="card-avatar">
                    <span class="status-indicator ${peer.status}" title="${peer.status}"></span>
                </div>
                <h4 class="peer-name">${peer.name}</h4>
                <span class="peer-skill-tag">${peer.skillTag}</span>
                <div class="peer-rating">
                    <i class="fa-solid fa-star"></i>
                    <span>${peer.rating}</span>
                </div>
                <div class="peer-rate-badge">${peer.rate}</div>
                <div class="card-actions">
                    <button class="card-btn primary connect-btn" data-peer="${peer.name}" data-role="${peer.role}">Connect</button>
                    <button class="card-btn secondary profile-modal-trigger" data-peer-id="${peer.id}">Profile</button>
                </div>
            </div>
        `).join('');
    }

    renderPeersGrid();

    if (languageFilter) languageFilter.addEventListener('change', renderPeersGrid);
    if (priceFilter) priceFilter.addEventListener('change', renderPeersGrid);
    if (peerSearchInput) peerSearchInput.addEventListener('input', renderPeersGrid);

    // 6. Modal Profile View & Booking
    document.addEventListener('click', (e) => {
        const trigger = e.target.closest('.profile-modal-trigger');
        if (trigger) {
            const peerId = parseInt(trigger.getAttribute('data-peer-id'));
            const peer = peersData.find(p => p.id === peerId) || peersData[0];

            document.getElementById('modalAvatar').src = peer.avatar;
            document.getElementById('modalPeerName').textContent = peer.name;
            document.getElementById('modalPeerTagline').textContent = peer.role;
            document.getElementById('modalAboutText').textContent = peer.about;
            document.getElementById('modalSessions').textContent = peer.sessions;
            document.getElementById('modalRating').textContent = peer.rating.split(' ')[0] + ' ★';
            document.getElementById('modalRate').textContent = peer.rate;

            profileModal.classList.add('active');
        }

        const connectBtn = e.target.closest('.connect-btn');
        if (connectBtn) {
            const name = connectBtn.getAttribute('data-peer');
            showToast(`Connecting with ${name}... Opening Live Studio Session!`, 'success');
            setTimeout(() => switchView('studio'), 800);
        }
    });

    if (modalCloseBtn) {
        modalCloseBtn.addEventListener('click', () => {
            profileModal.classList.remove('active');
        });
    }

    if (profileModal) {
        profileModal.addEventListener('click', (e) => {
            if (e.target === profileModal) profileModal.classList.remove('active');
        });
    }

    const modalBookBtn = document.getElementById('modalBookBtn');
    if (modalBookBtn) {
        modalBookBtn.addEventListener('click', () => {
            profileModal.classList.remove('active');
            showToast(`Session request sent successfully! Redirecting to Studio...`, 'success');
            setTimeout(() => switchView('studio'), 600);
        });
    }

    // 7. Live Studio Code Compiler Simulator
    const runCodeBtn = document.getElementById('runCodeBtn');
    const codeTextarea = document.getElementById('codeTextarea');
    const consoleOutput = document.getElementById('consoleOutput');
    const clearConsoleBtn = document.getElementById('clearConsoleBtn');
    const codeLangSelect = document.getElementById('codeLangSelect');

    const sampleSnippets = {
        python: `# Skill Bridge Python Compiler
def calculate_bounty(hours, rate):
    return hours * rate

print("⚡ Running Python 3.10 Code...")
result = calculate_bounty(4, 25.0)
print(f"Total Student Earnings: \${result}.00")`,
        javascript: `// Skill Bridge JS Runtime
function solveDoubt(topic) {
    console.log("Analyzing doubt: " + topic);
    return "✅ Resolved by Raveena in 12 mins!";
}

const statusMsg = solveDoubt("React Async State Update");
console.log(statusMsg);`,
        cpp: `// Skill Bridge C++ Environment
#include <iostream>
using namespace std;

int main() {
    cout << "🚀 Executing C++ Binary..." << endl;
    cout << "Tree Node Traversal Completed." << endl;
    return 0;
}`,
        html: `<!-- Skill Bridge HTML Preview -->
<div class="card">
    <h2>Skill Bridge Peer Card</h2>
    <p>Peer-to-peer student mentorship!</p>
</div>`
    };

    if (codeLangSelect) {
        codeLangSelect.addEventListener('change', (e) => {
            const lang = e.target.value;
            if (sampleSnippets[lang]) {
                codeTextarea.value = sampleSnippets[lang];
                showToast(`Switched code editor to ${lang.toUpperCase()}`, 'success');
            }
        });
    }

    if (runCodeBtn && codeTextarea && consoleOutput) {
        runCodeBtn.addEventListener('click', () => {
            const code = codeTextarea.value;
            const lang = codeLangSelect ? codeLangSelect.value : 'python';

            const line = document.createElement('div');
            line.className = 'console-line system';
            line.textContent = `> Compiling & Executing ${lang.toUpperCase()} snippet...`;
            consoleOutput.appendChild(line);

            setTimeout(() => {
                const outLine = document.createElement('div');
                outLine.className = 'console-line success';

                if (lang === 'javascript') {
                    try {
                        let capturedLogs = [];
                        const customConsole = { log: (msg) => capturedLogs.push(String(msg)) };
                        const evalFunc = new Function('console', code);
                        evalFunc(customConsole);
                        outLine.textContent = capturedLogs.join('\n') || "✅ Code executed cleanly with 0 errors.";
                    } catch (err) {
                        outLine.className = 'console-line error';
                        outLine.textContent = `❌ ${err.message}`;
                    }
                } else if (lang === 'python') {
                    outLine.textContent = "🎉 Success! Raveena earned $105.00 on Skill Bridge!\n[Process exited with return code 0]";
                } else {
                    outLine.textContent = `⚡ Executed successfully in 42ms. Output verified.`;
                }

                consoleOutput.appendChild(outLine);
                consoleOutput.scrollTop = consoleOutput.scrollHeight;
            }, 600);
        });
    }

    if (clearConsoleBtn && consoleOutput) {
        clearConsoleBtn.addEventListener('click', () => {
            consoleOutput.innerHTML = '<div class="console-line system">> Terminal cleared. Ready for next run.</div>';
        });
    }

    // 8. Call Control Toggles
    const micToggle = document.getElementById('micToggle');
    const camToggle = document.getElementById('camToggle');
    const shareToggle = document.getElementById('shareToggle');
    const endCallBtn = document.getElementById('endCallBtn');

    if (micToggle) {
        micToggle.addEventListener('click', () => {
            micToggle.classList.toggle('active');
            const isMuted = !micToggle.classList.contains('active');
            micToggle.innerHTML = isMuted ? '<i class="fa-solid fa-microphone-slash"></i>' : '<i class="fa-solid fa-microphone"></i>';
            showToast(isMuted ? 'Microphone muted' : 'Microphone unmuted', 'success');
        });
    }

    if (camToggle) {
        camToggle.addEventListener('click', () => {
            camToggle.classList.toggle('active');
            const isOff = !camToggle.classList.contains('active');
            camToggle.innerHTML = isOff ? '<i class="fa-solid fa-video-slash"></i>' : '<i class="fa-solid fa-video"></i>';
            showToast(isOff ? 'Camera turned off' : 'Camera turned on', 'success');
        });
    }

    if (shareToggle) {
        shareToggle.addEventListener('click', () => {
            showToast('Screen sharing toggle requested', 'success');
        });
    }

    if (endCallBtn) {
        endCallBtn.addEventListener('click', () => {
            showToast('Peer call session ended.', 'success');
        });
    }

    // 9. Peer Live Chat Input
    const chatInput = document.getElementById('chatInput');
    const sendChatBtn = document.getElementById('sendChatBtn');
    const chatMessages = document.getElementById('chatMessages');

    function sendChatMessage() {
        if (!chatInput || !chatInput.value.trim() || !chatMessages) return;

        const txt = chatInput.value.trim();
        const userMsg = document.createElement('div');
        userMsg.className = 'chat-msg user';
        userMsg.innerHTML = `
            <span class="msg-author">You</span>
            <p>${escapeHtml(txt)}</p>
            <span class="msg-time">Just now</span>
        `;
        chatMessages.appendChild(userMsg);
        chatInput.value = '';
        chatMessages.scrollTop = chatMessages.scrollHeight;

        // Auto peer response simulation
        setTimeout(() => {
            const peerMsg = document.createElement('div');
            peerMsg.className = 'chat-msg peer';
            peerMsg.innerHTML = `
                <span class="msg-author">Alex Rivera</span>
                <p>Got it! I see your point. Let's run the code and verify the output console.</p>
                <span class="msg-time">Just now</span>
            `;
            chatMessages.appendChild(peerMsg);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }, 1200);
    }

    if (sendChatBtn) sendChatBtn.addEventListener('click', sendChatMessage);
    if (chatInput) {
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendChatMessage();
        });
    }

    // 10. Withdraw / Cashout Funds Button
    const cashoutBtn = document.getElementById('cashoutBtn');
    if (cashoutBtn) {
        cashoutBtn.addEventListener('click', () => {
            showToast('💰 Cashout of $340.00 initiated to linked bank account!', 'success');
        });
    }

    // ==========================================================================
    // 11. User Profile Dropdown & Settings Submenu Interactive Module
    // ==========================================================================
    const userProfileData = {
        name: "Raveena P V",
        role: "Student Mentor • Lv. 4",
        avatar: "avathar/c1.jpg",
        skills: ["React", "JavaScript", "Python", "UI/UX"],
        toKnow: ["Docker", "GraphQL", "System Design", "Rust"],
        pointsGained: 1450,
        earnings: "$240.00",
        availableHours: "15 hrs / week",
        schedule: "Mon - Fri, 4:00 PM - 8:00 PM",
        bio: "Experienced student mentor passionate about peer coding, pair programming, React UI/UX, and DSA problem solving.",
        privacy: {
            isPublic: true,
            showHours: true,
            allowRequests: true
        }
    };

    // DOM Elements for Profile Dropdown & Modals
    const profilePill = document.getElementById('profilePill');
    const userProfileDropdown = document.getElementById('userProfileDropdown');
    const profileArrowIcon = document.getElementById('profileArrowIcon');
    const settingsTriggerBtn = document.getElementById('settingsTriggerBtn');
    const settingsSubMenu = document.getElementById('settingsSubMenu');
    const settingsChevron = document.getElementById('settingsChevron');

    const dropdownSkillsList = document.getElementById('dropdownSkillsList');
    const dropdownToKnowList = document.getElementById('dropdownToKnowList');
    const dropdownPointsValue = document.getElementById('dropdownPointsValue');
    const dropdownHoursValue = document.getElementById('dropdownHoursValue');
    const dropdownViewPublicBtn = document.getElementById('dropdownViewPublicBtn');

    // Modals & Submenu Trigger Buttons
    const btnEditProfile = document.getElementById('btnEditProfile');
    const btnAccountPrivacy = document.getElementById('btnAccountPrivacy');
    const btnLogout = document.getElementById('btnLogout');

    const editProfileModal = document.getElementById('editProfileModal');
    const editProfileCloseBtn = document.getElementById('editProfileCloseBtn');
    const cancelEditProfileBtn = document.getElementById('cancelEditProfileBtn');
    const editProfileForm = document.getElementById('editProfileForm');

    const accountPrivacyModal = document.getElementById('accountPrivacyModal');
    const accountPrivacyCloseBtn = document.getElementById('accountPrivacyCloseBtn');
    const cancelPrivacyBtn = document.getElementById('cancelPrivacyBtn');
    const accountPrivacyForm = document.getElementById('accountPrivacyForm');

    const publicProfileViewModal = document.getElementById('publicProfileViewModal');
    const publicProfileCloseBtn = document.getElementById('publicProfileCloseBtn');
    const pubModalShareBtn = document.getElementById('pubModalShareBtn');

    const logoutConfirmModal = document.getElementById('logoutConfirmModal');
    const logoutCloseBtn = document.getElementById('logoutCloseBtn');
    const cancelLogoutBtn = document.getElementById('cancelLogoutBtn');
    const confirmLogoutBtn = document.getElementById('confirmLogoutBtn');

    // Function to render user profile UI components
    function renderUserProfileUI() {
        // Update header & dropdown user card
        const headerName = document.getElementById('headerProfileName');
        const headerImg = document.getElementById('headerProfileImg');
        const dropName = document.getElementById('dropdownUserName');
        const dropRole = document.getElementById('dropdownUserRole');
        const dropAvatar = document.getElementById('dropdownAvatarImg');
        const publicBadge = document.getElementById('dropdownPublicBadge');

        if (headerName) headerName.textContent = userProfileData.name.split(' ')[0];
        if (headerImg) headerImg.src = userProfileData.avatar;
        if (dropName) dropName.textContent = userProfileData.name;
        if (dropRole) dropRole.textContent = userProfileData.role;
        if (dropAvatar) dropAvatar.src = userProfileData.avatar;

        if (publicBadge) {
            publicBadge.style.display = userProfileData.privacy.isPublic ? 'inline-flex' : 'none';
        }

        // Render Skills
        if (dropdownSkillsList) {
            dropdownSkillsList.innerHTML = userProfileData.skills
                .map(skill => `<span class="p-tag yellow">${escapeHtml(skill)}</span>`)
                .join('');
        }

        // Render To Know (Skills to learn)
        if (dropdownToKnowList) {
            dropdownToKnowList.innerHTML = userProfileData.toKnow
                .map(item => `<span class="p-tag outline-purple">${escapeHtml(item)}</span>`)
                .join('');
        }

        // Render Points Gained
        if (dropdownPointsValue) {
            dropdownPointsValue.innerHTML = `${userProfileData.pointsGained.toLocaleString()} pts <span class="stat-sub">(${userProfileData.earnings} earned)</span>`;
        }

        // Render Available Hours
        if (dropdownHoursValue) {
            if (userProfileData.privacy.showHours) {
                dropdownHoursValue.innerHTML = `${userProfileData.availableHours} <span class="stat-sub">(${userProfileData.schedule})</span>`;
            } else {
                dropdownHoursValue.innerHTML = `<span style="color: var(--text-muted); font-style: italic;">Private Schedule</span>`;
            }
        }
    }

    renderUserProfileUI();

    // Toggle Profile Dropdown
    if (profilePill && userProfileDropdown) {
        profilePill.addEventListener('click', (e) => {
            e.stopPropagation();
            const isOpen = userProfileDropdown.classList.contains('show');

            // Close notification dropdown if open
            if (notifDropdown && notifDropdown.classList.contains('show')) {
                notifDropdown.classList.remove('show');
            }

            if (isOpen) {
                closeProfileDropdown();
            } else {
                userProfileDropdown.classList.add('show');
                profilePill.classList.add('active');
                if (profileArrowIcon) profileArrowIcon.classList.add('rotated');
            }
        });
    }

    function closeProfileDropdown() {
        if (userProfileDropdown) userProfileDropdown.classList.remove('show');
        if (profilePill) profilePill.classList.remove('active');
        if (profileArrowIcon) profileArrowIcon.classList.remove('rotated');
    }

    let selectedAvatarUrl = userProfileData.avatar;

    // Toggle Settings Accordion Sub-Menu inside Dropdown
    if (settingsTriggerBtn && settingsSubMenu) {
        settingsTriggerBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const isOpen = settingsSubMenu.classList.contains('open');

            if (isOpen) {
                settingsSubMenu.classList.remove('open');
                if (settingsChevron) settingsChevron.classList.remove('rotated');
            } else {
                settingsSubMenu.classList.add('open');
                if (settingsChevron) settingsChevron.classList.add('rotated');
                // Smoothly scroll down so expanded settings options are immediately visible
                setTimeout(() => {
                    settingsSubMenu.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }, 120);
            }
        });
    }

    // Close Dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (userProfileDropdown && !userProfileDropdown.contains(e.target) && !profilePill.contains(e.target)) {
            closeProfileDropdown();
        }
    });

    // Close Dropdown on Escape Key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeProfileDropdown();
            closeAllProfileModals();
        }
    });

    // ==========================================================================
    // Avatar Selection Picker Logic inside Edit Profile Modal (C1 - C6 Options)
    // ==========================================================================
    const avatarOptionCards = document.querySelectorAll('.avatar-circle-option, .avatar-option-card');

    avatarOptionCards.forEach(card => {
        card.addEventListener('click', () => {
            avatarOptionCards.forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            selectedAvatarUrl = card.getAttribute('data-avatar');
        });
    });

    // Sub-menu Option Handlers
    // 1. Edit Profile Button Click
    if (btnEditProfile) {
        btnEditProfile.addEventListener('click', (e) => {
            e.preventDefault();
            closeProfileDropdown();

            // Pre-select active avatar in picker
            selectedAvatarUrl = userProfileData.avatar;
            avatarOptionCards.forEach(card => {
                if (card.getAttribute('data-avatar') === userProfileData.avatar) {
                    card.classList.add('selected');
                } else {
                    card.classList.remove('selected');
                }
            });

            // Populate form fields
            document.getElementById('editFullName').value = userProfileData.name;
            document.getElementById('editSkills').value = userProfileData.skills.join(', ');
            document.getElementById('editToKnow').value = userProfileData.toKnow.join(', ');
            document.getElementById('editAvailableHours').value = userProfileData.availableHours;
            document.getElementById('editSchedule').value = userProfileData.schedule;
            document.getElementById('editBio').value = userProfileData.bio;

            editProfileModal.classList.add('active');
        });
    }

    // Save Edit Profile Form
    if (editProfileForm) {
        editProfileForm.addEventListener('submit', (e) => {
            e.preventDefault();
            userProfileData.avatar = selectedAvatarUrl;
            userProfileData.name = document.getElementById('editFullName').value.trim();
            userProfileData.skills = document.getElementById('editSkills').value.split(',').map(s => s.trim()).filter(Boolean);
            userProfileData.toKnow = document.getElementById('editToKnow').value.split(',').map(s => s.trim()).filter(Boolean);
            userProfileData.availableHours = document.getElementById('editAvailableHours').value.trim();
            userProfileData.schedule = document.getElementById('editSchedule').value.trim();
            userProfileData.bio = document.getElementById('editBio').value.trim();

            renderUserProfileUI();
            editProfileModal.classList.remove('active');
            showToast('🎨 Profile & avatar updated successfully!', 'success');
        });
    }

    // 2. Account & Privacy Button Click
    if (btnAccountPrivacy) {
        btnAccountPrivacy.addEventListener('click', (e) => {
            e.preventDefault();
            closeProfileDropdown();

            // Populate privacy toggles
            document.getElementById('togglePublicProfile').checked = userProfileData.privacy.isPublic;
            document.getElementById('toggleShowHours').checked = userProfileData.privacy.showHours;
            document.getElementById('toggleAllowRequests').checked = userProfileData.privacy.allowRequests;

            accountPrivacyModal.classList.add('active');
        });
    }

    // Save Account & Privacy Form
    if (accountPrivacyForm) {
        accountPrivacyForm.addEventListener('submit', (e) => {
            e.preventDefault();
            userProfileData.privacy.isPublic = document.getElementById('togglePublicProfile').checked;
            userProfileData.privacy.showHours = document.getElementById('toggleShowHours').checked;
            userProfileData.privacy.allowRequests = document.getElementById('toggleAllowRequests').checked;

            renderUserProfileUI();
            accountPrivacyModal.classList.remove('active');
            showToast('🔒 Account & privacy settings saved successfully!', 'success');
        });
    }

    // 3. Logout Button Click
    if (btnLogout) {
        btnLogout.addEventListener('click', (e) => {
            e.preventDefault();
            closeProfileDropdown();
            logoutConfirmModal.classList.add('active');
        });
    }

    // Also wire up sidebar logout button if present
    const logoutBtnSidebar = document.getElementById('logoutBtn');
    if (logoutBtnSidebar) {
        logoutBtnSidebar.addEventListener('click', (e) => {
            e.preventDefault();
            logoutConfirmModal.classList.add('active');
        });
    }

    if (confirmLogoutBtn) {
        confirmLogoutBtn.addEventListener('click', () => {
            logoutConfirmModal.classList.remove('active');
            showToast('🚪 Logged out successfully. Redirecting...', 'success');
            setTimeout(() => {
                location.reload();
            }, 1200);
        });
    }

    // 4. Preview Public Profile Modal
    function openPublicProfileModal() {
        closeProfileDropdown();

        document.getElementById('pubModalAvatar').src = userProfileData.avatar;
        document.getElementById('pubModalName').textContent = userProfileData.name;
        document.getElementById('pubModalRole').textContent = userProfileData.role;
        document.getElementById('pubModalBio').textContent = userProfileData.bio;

        document.getElementById('pubModalSkills').innerHTML = userProfileData.skills
            .map(s => `<span class="p-tag yellow">${escapeHtml(s)}</span>`)
            .join(' ');

        document.getElementById('pubModalToKnow').innerHTML = userProfileData.toKnow
            .map(s => `<span class="p-tag outline-purple">${escapeHtml(s)}</span>`)
            .join(' ');

        document.getElementById('pubModalPoints').textContent = `${userProfileData.pointsGained.toLocaleString()} pts`;
        document.getElementById('pubModalEarned').textContent = `${userProfileData.earnings} Total Earned`;

        document.getElementById('pubModalHours').textContent = userProfileData.availableHours;
        document.getElementById('pubModalSchedule').textContent = userProfileData.schedule;

        publicProfileViewModal.classList.add('active');
    }

    if (dropdownViewPublicBtn) {
        dropdownViewPublicBtn.addEventListener('click', (e) => {
            e.preventDefault();
            openPublicProfileModal();
        });
    }

    // Click on detail items in dropdown opens public profile modal
    ['itemSkills', 'itemToKnow', 'itemPoints', 'itemHours'].forEach(itemId => {
        const itemElem = document.getElementById(itemId);
        if (itemElem) {
            itemElem.style.cursor = 'pointer';
            itemElem.addEventListener('click', (e) => {
                e.stopPropagation();
                openPublicProfileModal();
            });
        }
    });

    if (pubModalShareBtn) {
        pubModalShareBtn.addEventListener('click', () => {
            navigator.clipboard.writeText(window.location.href);
            showToast('📋 Public profile link copied to clipboard!', 'success');
        });
    }

    // Modal Close Listeners
    function closeAllProfileModals() {
        if (editProfileModal) editProfileModal.classList.remove('active');
        if (accountPrivacyModal) accountPrivacyModal.classList.remove('active');
        if (publicProfileViewModal) publicProfileViewModal.classList.remove('active');
        if (logoutConfirmModal) logoutConfirmModal.classList.remove('active');
    }

    [editProfileCloseBtn, cancelEditProfileBtn].forEach(btn => {
        if (btn) btn.addEventListener('click', () => editProfileModal.classList.remove('active'));
    });

    [accountPrivacyCloseBtn, cancelPrivacyBtn].forEach(btn => {
        if (btn) btn.addEventListener('click', () => accountPrivacyModal.classList.remove('active'));
    });

    if (publicProfileCloseBtn) {
        publicProfileCloseBtn.addEventListener('click', () => publicProfileViewModal.classList.remove('active'));
    }

    [logoutCloseBtn, cancelLogoutBtn].forEach(btn => {
        if (btn) btn.addEventListener('click', () => logoutConfirmModal.classList.remove('active'));
    });

    // Close modals on overlay backdrop click
    [editProfileModal, accountPrivacyModal, publicProfileViewModal, logoutConfirmModal].forEach(modal => {
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) modal.classList.remove('active');
            });
        }
    });

    // Helper functions
    function showToast(message, type = 'success') {
        if (!toastContainer) return;
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `<i class="fa-solid fa-circle-check"></i> <span>${message}</span>`;
        toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 3200);
    }

    function escapeHtml(str) {
        return str.replace(/[&<>"']/g, function (m) {
            return {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#039;'
            }[m];
        });
    }
});
