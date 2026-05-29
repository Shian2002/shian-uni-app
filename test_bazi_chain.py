from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1280, 'height': 800})
    page.goto('http://119.29.128.18')
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(2000)
    
    page.evaluate('''async () => {
        const form = new FormData();
        form.append('username', 'pwtest');
        form.append('password', 'test1234');
        await fetch('/api/login', { method: 'POST', body: form });
    }''')
    page.reload()
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(2000)
    
    # Check: is bazi page even loaded? 
    check = page.evaluate('''() => {
        var container = document.getElementById('baiChatContainer');
        var aiPanel = document.getElementById('baziTabAiContent');
        var activeTab = null;
        // Check if Vue component has the activeTab ref
        if (window.__vue_app__ || document.querySelector('[data-v-]')) {
            // Try to find the Vue instance
        }
        return {
            hasBaiChatContainer: !!container,
            hasAiPanel: !!aiPanel,
            aiPanelDisplay: aiPanel ? getComputedStyle(aiPanel).display : 'N/A',
            aiPanelVshow: aiPanel ? aiPanel.style.display : 'N/A',
            // Check if we're on the bazi page
            currentPath: window.location.href,
            // Check tabBar
            hasTabBar: !!document.querySelector('.uni-tabbar')
        };
    }''')
    print(f'Before sidebar click:')
    print(f'  hasBaiChatContainer: {check["hasBaiChatContainer"]}')
    print(f'  hasAiPanel: {check["hasAiPanel"]}')
    print(f'  aiPanelDisplay: {check["aiPanelDisplay"]}')
    print(f'  currentPath: {check["currentPath"]}')
    
    # Click sidebar bazi item
    sidebar_btn = page.query_selector('.topnav-sidebar-btn')
    if sidebar_btn:
        sidebar_btn.click()
        page.wait_for_timeout(1000)
    
    page.evaluate('''() => {
        var items = document.querySelectorAll('.sidebar-item-body');
        for (var i = 0; i < items.length; i++) {
            var onclick = items[i].getAttribute('onclick') || '';
            if (onclick.indexOf('_showBaziConvDetail') > -1) {
                items[i].click();
                return;
            }
        }
    }''')
    page.wait_for_timeout(4000)
    
    check2 = page.evaluate('''() => {
        var aiPanel = document.getElementById('baziTabAiContent');
        var container = document.getElementById('baiChatContainer');
        return {
            currentPath: window.location.href,
            hasContainer: !!container,
            aiPanelDisplay: aiPanel ? getComputedStyle(aiPanel).display : 'N/A',
            containerHTML: container ? container.innerHTML.substring(0, 100) : 'N/A',
            // Check if switchBaziTab was called
            activeTabExists: typeof activeTab !== 'undefined'
        };
    }''')
    print(f'\nAfter sidebar click (4s):')
    print(f'  currentPath: {check2["currentPath"]}')
    print(f'  hasContainer: {check2["hasContainer"]}')
    print(f'  aiPanelDisplay: {check2["aiPanelDisplay"]}')
    print(f'  containerHTML: {check2["containerHTML"]}')
    
    browser.close()
