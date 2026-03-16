"""
ui/stop_injection.py
注入一个自定义的 Stop 按钮覆盖在 Streamlit 聊天输入框的上方，用于中止生成。
"""
import streamlit as st


def inject_stop_button_js():
    """
    注入 JS 代码，用于找到 stChatInputSubmitButton，隐藏它，并在上方放置一个红色的 Stop Square 按钮。
    当点击时，它会找到原生 Streamlit stop 按钮来中断后端。
    """
    st.components.v1.html("""
    <script>
    const parentDoc = window.parent.document;
    let overlay = null;
    let origSubmit = null;
    let cleanupTimer = null;

    function setChatInputActivity(chatInput, state) {
        if (!chatInput) return;
        chatInput.setAttribute("data-ag-activity", state);
    }

    function hideNativeSubmit(button) {
        if (!button) return;
        if (button.dataset.agHidden === "true") return;
        button.dataset.agOrigDisplay = button.style.display || "";
        button.dataset.agOrigVisibility = button.style.visibility || "";
        button.dataset.agOrigPointerEvents = button.style.pointerEvents || "";
        button.dataset.agOrigOpacity = button.style.opacity || "";
        button.dataset.agOrigBackground = button.style.background || "";
        button.dataset.agOrigBoxShadow = button.style.boxShadow || "";
        button.dataset.agHidden = "true";
        button.style.display = "none";
        button.style.visibility = "hidden";
        button.style.pointerEvents = "none";
        button.style.opacity = "0";
        button.style.background = "transparent";
        button.style.boxShadow = "none";
    }

    function restoreNativeSubmit(button) {
        if (!button) return;
        button.style.display = button.dataset.agOrigDisplay || "";
        button.style.visibility = button.dataset.agOrigVisibility || "";
        button.style.pointerEvents = button.dataset.agOrigPointerEvents || "";
        button.style.opacity = button.dataset.agOrigOpacity || "";
        button.style.background = button.dataset.agOrigBackground || "";
        button.style.boxShadow = button.dataset.agOrigBoxShadow || "";
        delete button.dataset.agOrigDisplay;
        delete button.dataset.agOrigVisibility;
        delete button.dataset.agOrigPointerEvents;
        delete button.dataset.agOrigOpacity;
        delete button.dataset.agOrigBackground;
        delete button.dataset.agOrigBoxShadow;
        delete button.dataset.agHidden;
    }

    function findNativeStopButton() {
        const directStatusButton = parentDoc.querySelector('[data-testid="stStatusWidget"] button');
        if (directStatusButton) return directStatusButton;

        const candidateButtons = parentDoc.querySelectorAll('header button, [data-testid="stToolbar"] button, button');
        for (const button of candidateButtons) {
            const text = (button.innerText || button.textContent || "").trim().toLowerCase();
            const aria = (button.getAttribute("aria-label") || "").trim().toLowerCase();
            const title = (button.getAttribute("title") || "").trim().toLowerCase();
            if (
                text.includes("stop") || text.includes("停止") ||
                aria.includes("stop") || aria.includes("停止") ||
                title.includes("stop") || title.includes("停止")
            ) {
                return button;
            }
        }
        return null;
    }

    function mountOverlay(chatInput) {
        overlay = parentDoc.getElementById("ag-custom-stop-btn");
        if (overlay) {
            setChatInputActivity(chatInput, "active");
            return overlay;
        }

        overlay = parentDoc.createElement("button");
        overlay.id = "ag-custom-stop-btn";
        overlay.type = "button";
        overlay.setAttribute("aria-label", "停止生成");
        overlay.innerHTML = `
            <span class="ag-stop-label">停止</span>
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" aria-hidden="true">
                <rect x="6" y="6" width="12" height="12" rx="3" fill="#ffffff"></rect>
            </svg>
        `;

        Object.assign(overlay.style, {
            position: 'absolute',
            right: '12px',
            top: '50%',
            transform: 'translateY(-50%)',
            minWidth: '78px',
            height: '38px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            padding: '0 14px',
            cursor: 'pointer',
            zIndex: '10000',
            background: 'linear-gradient(135deg, rgba(248, 109, 126, 0.96), rgba(214, 78, 122, 0.96))',
            boxShadow: '0 16px 32px rgba(211, 91, 107, 0.24), inset 0 1px 0 rgba(255, 255, 255, 0.32)',
            color: '#ffffff',
            backdropFilter: 'blur(16px) saturate(180%)',
            borderRadius: '999px',
            border: '1px solid rgba(255, 255, 255, 0.28)',
            fontSize: '13px',
            fontWeight: '600',
            letterSpacing: '0.04em',
            transition: 'transform 0.18s ease, box-shadow 0.18s ease, opacity 0.18s ease',
        });
        overlay.style.setProperty('appearance', 'none', 'important');
        overlay.style.setProperty('-webkit-appearance', 'none', 'important');
        overlay.style.setProperty('background', 'linear-gradient(135deg, rgba(248, 109, 126, 0.96), rgba(214, 78, 122, 0.96))', 'important');
        overlay.style.setProperty('color', '#ffffff', 'important');
        overlay.style.setProperty('border', '1px solid rgba(255, 255, 255, 0.28)', 'important');
        overlay.style.setProperty('box-shadow', '0 16px 32px rgba(211, 91, 107, 0.24), inset 0 1px 0 rgba(255, 255, 255, 0.32)', 'important');
        overlay.style.setProperty('backdrop-filter', 'blur(16px) saturate(180%)', 'important');
        overlay.style.setProperty('-webkit-backdrop-filter', 'blur(16px) saturate(180%)', 'important');

        overlay.onmouseenter = () => {
            overlay.style.transform = 'translateY(calc(-50% - 1px))';
            overlay.style.boxShadow = '0 20px 36px rgba(211, 91, 107, 0.28), inset 0 1px 0 rgba(255, 255, 255, 0.36)';
        };
        overlay.onmouseleave = () => {
            overlay.style.transform = 'translateY(-50%)';
            overlay.style.boxShadow = '0 16px 32px rgba(211, 91, 107, 0.24), inset 0 1px 0 rgba(255, 255, 255, 0.32)';
        };

        overlay.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            overlay.style.opacity = '0.5';
            overlay.style.pointerEvents = 'none';

            const nativeStop = findNativeStopButton();
            if (nativeStop) {
                setChatInputActivity(chatInput, "idle");
                nativeStop.click();
                cleanupTimer = window.setTimeout(() => {
                    const currentOverlay = parentDoc.getElementById("ag-custom-stop-btn");
                    if (currentOverlay && currentOverlay.parentNode) {
                        currentOverlay.parentNode.removeChild(currentOverlay);
                    }
                    restoreNativeSubmit(origSubmit);
                }, 800);
            } else {
                overlay.style.opacity = '1';
                overlay.style.pointerEvents = 'auto';
                console.log("[Mirror Shopping] Could not find native Streamlit stop button.");
            }
        };

        chatInput.style.position = 'relative';
        setChatInputActivity(chatInput, "active");
        chatInput.appendChild(overlay);
        return overlay;
    }

    const interval = setInterval(() => {
        const chatInput = parentDoc.querySelector('[data-testid="stChatInput"]');
        if (!chatInput) return;

        origSubmit = chatInput.querySelector('[data-testid="stChatInputSubmitButton"]');
        if (origSubmit) {
            hideNativeSubmit(origSubmit);
        }
        setChatInputActivity(chatInput, "active");
        mountOverlay(chatInput);
    }, 200);

    // Cleanup when component unmounts (generation finished / stopped)
    window.addEventListener('unload', () => {
        const chatInput = parentDoc.querySelector('[data-testid="stChatInput"]');
        clearInterval(interval);
        if (cleanupTimer) {
            window.clearTimeout(cleanupTimer);
        }
        if (overlay && overlay.parentNode) {
            overlay.parentNode.removeChild(overlay);
        }
        restoreNativeSubmit(origSubmit);
        setChatInputActivity(chatInput, "idle");
    });
    </script>
    """, height=0)

def remove_stop_button_js():
    """
    注入 JS 代码，用于主动移除之前注入的 Stop 按钮，并恢复发送按钮。
    """
    st.components.v1.html("""
    <script>
    const parentDoc = window.parent.document;
    const overlay = parentDoc.getElementById("ag-custom-stop-btn");
    if (overlay && overlay.parentNode) {
        overlay.parentNode.removeChild(overlay);
    }
    const chatInput = parentDoc.querySelector('[data-testid="stChatInput"]');
    if (chatInput) {
        chatInput.setAttribute("data-ag-activity", "idle");
        const origSubmit = chatInput.querySelector('[data-testid="stChatInputSubmitButton"]');
        if (origSubmit) {
            origSubmit.style.display = origSubmit.dataset.agOrigDisplay || '';
            origSubmit.style.visibility = origSubmit.dataset.agOrigVisibility || '';
            origSubmit.style.pointerEvents = origSubmit.dataset.agOrigPointerEvents || '';
            origSubmit.style.opacity = origSubmit.dataset.agOrigOpacity || '';
            origSubmit.style.background = origSubmit.dataset.agOrigBackground || '';
            origSubmit.style.boxShadow = origSubmit.dataset.agOrigBoxShadow || '';
            delete origSubmit.dataset.agOrigDisplay;
            delete origSubmit.dataset.agOrigVisibility;
            delete origSubmit.dataset.agOrigPointerEvents;
            delete origSubmit.dataset.agOrigOpacity;
            delete origSubmit.dataset.agOrigBackground;
            delete origSubmit.dataset.agOrigBoxShadow;
            delete origSubmit.dataset.agHidden;
        }
    }
    </script>
    """, height=0, width=0)
